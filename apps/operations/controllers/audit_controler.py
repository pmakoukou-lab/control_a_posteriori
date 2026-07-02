
import io
import json
import unicodedata
from datetime import datetime

import xlrd
from xlutils.copy import copy as _xlutils_copy

from py4web import action, URL, redirect, request, response

from ..common import (
    auth,
    db,
    flash,
    session,
    groups,
)

import os

from ..fixtures.rbac_fixture import access
from ..fixtures.period_fixture import period, active_period
# Force le chargement du package `models` (définition des tables operations /
# allotissements / référentiel) AVANT de dériver les specs ci-dessous : les
# contrôleurs sont importés avant les modèles par l'__init__ de l'app.
from .. import models as _models  # noqa: F401


# Messages affichés sur la page « comptes » après une action (POST → redirect).
# Clé = code passé dans ?msg= ; valeur = (niveau, texte).
COMPTES_MESSAGES = {
    'user_added':       ('ok',  "Utilisateur ajouté avec succès."),
    'user_updated':     ('edit', "Utilisateur modifié avec succès."),
    'user_activated':   ('ok',  "Compte activé."),
    'user_deactivated': ('ok',  "Compte désactivé."),
    'user_deleted':     ('del', "Utilisateur supprimé."),
    'role_added':       ('ok',  "Rôle ajouté avec succès."),
    'role_updated':     ('edit', "Rôle modifié avec succès."),
    'role_deleted':     ('del', "Rôle supprimé."),
    'bad_email':        ('err', "Adresse e-mail invalide."),
    'email_taken':      ('err', "Cet e-mail est déjà utilisé par un autre compte."),
    'bad_phone':        ('err', "Numéro de téléphone invalide (format international, ex. +225...)."),
    'phone_taken':      ('err', "Ce numéro est déjà utilisé par un autre compte."),
    'bad_pwd':          ('err', "Le mot de passe doit contenir au moins 8 caractères."),
    'pwd_mismatch':     ('err', "Les deux mots de passe ne correspondent pas."),
    'register_failed':  ('err', "Échec de l'ajout : e-mail, identifiant ou téléphone déjà utilisé."),
    'role_exists':      ('err', "Ce rôle existe déjà."),
    'role_name':        ('err', "Le nom du rôle est requis."),
    'not_found':        ('err', "Élément introuvable."),
}

# Messages de la page « gestion » (ministères & autorités contractantes).
GESTION_MESSAGES = {
    'min_added':       ('ok',  "Ministère ajouté avec succès."),
    'min_updated':     ('edit', "Ministère modifié avec succès."),
    'min_activated':   ('ok',  "Ministère activé."),
    'min_deactivated': ('ok',  "Ministère désactivé."),
    'min_deleted':     ('del', "Ministère supprimé."),
    'gc_added':        ('ok',  "Autorité contractante ajoutée avec succès."),
    'gc_updated':      ('edit', "Autorité contractante modifiée avec succès."),
    'gc_activated':    ('ok',  "Autorité contractante activée."),
    'gc_deactivated':  ('ok',  "Autorité contractante désactivée."),
    'gc_deleted':      ('del', "Autorité contractante supprimée."),
    'exo_added':       ('ok',  "Exercice budgétaire enregistré avec succès."),
    'sess_added':      ('ok',  "Mission(s) ajoutée(s) avec succès."),
    'sess_updated':    ('edit', "Mission modifiée avec succès."),
    'sess_deleted':    ('del', "Mission supprimée."),
    'min_name':        ('err', "Le nom du ministère est requis."),
    'gc_name':         ('err', "Le nom de l'autorité contractante est requis."),
    'gc_min':          ('err', "Veuillez choisir un ministère valide."),
    'exo_year':        ('err', "Veuillez choisir une année valide pour l'exercice."),
    'not_found':       ('err', "Élément introuvable."),
}

# Noms de mois en français pour l'affichage des plages de dates des sessions.
_MONTHS_FR = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
              'août', 'septembre', 'octobre', 'novembre', 'décembre']


def _fr_date(d):
    """Date → « 13 avril 2026 » (ou « … » si absente)."""
    if not d:
        return '…'
    return '%d %s %d' % (d.day, _MONTHS_FR[d.month], d.year)


def _range_label(s):
    """Libellé « du <début> au <fin> » d'une session."""
    return 'du ' + _fr_date(s.date_debut) + ' au ' + _fr_date(s.date_fin)


def _parse_date(value):
    """Convertit une saisie (jj/mm/aaaa, aaaa-mm-jj…) en date, ou None."""
    value = (value or '').strip()
    if not value:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _to_int(value):
    """Entier depuis une saisie (numéro de mission…), ou None si vide/invalide."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None

# Rôles par défaut créés au premier affichage si la table est vide.
# NB : les noms ci-dessous DOIVENT correspondre aux tags réellement assignés aux
# utilisateurs (cf. gardes access(roles=...)). Seed appliqué uniquement si la table
# `groupe` est vide ; la base existante porte déjà « contrôleur / staticien /
# Administrateur ».
DEFAULT_ROLES = [
    ("contrôleur",    "Réalise la saisie et la consultation des opérations auditées."),
    ("staticien",     "Consulte, exporte et imprime les opérations (lecture seule)."),
    ("Administrateur", "Gère les objets manipulés par l'application."),
]


# ---------------------------------------------------------------------------
# Pages de l'application « AUDIT a posteriori ».
#
# Chaque action renvoie `active=<clé>` : cette clé pilote l'élément surligné
# dans la barre latérale (voir templates/audits/_sidebar.html, qui lit
# `globals().get('active')`). Les noms de routes correspondent exactement aux
# URL utilisées par le sidebar : URL('dashboard'), URL('collecte'),
# URL('rapport'), URL('comptes'), URL('gestion').
# ---------------------------------------------------------------------------


def _search_norm(s):
    """Normalise pour la recherche : minuscules + suppression des accents."""
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return s.lower().strip()


def _rget(row, name):
    """Lecture DÉFENSIVE d'un champ : renvoie None si la colonne n'existe pas dans
    la table du mode. Les modes n'ont pas tous les mêmes colonnes « transverses »
    (ministere, nature_operation, n_bomp…) — l'engine ne doit pas planter pour autant."""
    try:
        return row[name]
    except (KeyError, AttributeError):
        return None


def _current_user_display():
    """Identité de l'acteur connecté, pour la section utilisateur de l'en-tête :
    nom (en capitales) + prénom et rôle(s). None si personne n'est connecté.

    On relit la fiche complète en base via `auth.user_id` : `auth.get_user()` ne
    renvoie pas toujours les champs first_name/last_name selon la session."""
    uid = auth.user_id
    if not uid:
        return None
    u = db.auth_user(uid)
    if not u:
        return None
    first = (u.first_name or '').strip()
    last = (u.last_name or '').strip()
    name = (last.upper() + ' ' + first).strip() or u.username or u.email or ''
    tags = list(groups.get(uid) or [])
    return dict(first=first, last=last, name=name,
                role=', '.join(tags) if tags else 'Utilisateur')


# ---------------------------------------------------------------------------
# Tableau de bord — JOURNAL DE COLLECTE (cadré sur la mission active).
# Phase « journal » : on mesure l'ACTIVITÉ de saisie, PAS la conformité ; le
# statut reste neutre « en attente » partout. Tout est agrégé EN BASE
# (count/sum/group by) sur les 4 tables d'opérations, puis combiné — aucune
# boucle N+1, aucun comptage Python sur des listes chargées.
# ---------------------------------------------------------------------------


def _fmt_fcfa(v):
    """Montant FCFA lisible : abréviation Md / M, sinon séparateur de milliers."""
    try:
        v = float(v or 0)
    except (TypeError, ValueError):
        v = 0.0
    if v >= 1e9:
        return ('%.2f' % (v / 1e9)).rstrip('0').rstrip('.').replace('.', ',') + ' Md FCFA'
    if v >= 1e6:
        return ('%.1f' % (v / 1e6)).rstrip('0').rstrip('.').replace('.', ',') + ' M FCFA'
    return format(int(round(v)), ',').replace(',', ' ') + ' FCFA'


def _ago(value):
    """Ancienneté lisible (« aujourd'hui », « il y a 3 j »…) d'une date/datetime."""
    from datetime import datetime as _dt, timezone as _tz, date as _date
    if not value:
        return '—'
    now = _dt.now(_tz.utc)
    if isinstance(value, _dt):
        if value.tzinfo is None:
            value = value.replace(tzinfo=_tz.utc)
        days = (now - value).days
    elif isinstance(value, _date):
        days = (now.date() - value).days
    else:
        return '—'
    if days <= 0:
        return "aujourd'hui"
    if days == 1:
        return "hier"
    if days < 7:
        return "il y a %d j" % days
    if days < 31:
        return "il y a %d sem" % (days // 7)
    if days < 365:
        return "il y a %d mois" % (days // 30)
    y = days // 365
    return "il y a %d an%s" % (y, 's' if y > 1 else '')


# Dégradés des pastilles d'initiales — palette « maison » (ambre, vert, violet,
# bleu, sarcelle) ; teintes foncées pour garder un texte blanc lisible. La couleur
# est dérivée du nom (stable par personne, aspect « aléatoire » varié).
_AVATAR_GRADIENTS = [
    'linear-gradient(135deg,var(--color-amber-700),var(--color-amber-800))',
    'linear-gradient(135deg,var(--color-green-600),var(--color-green-800))',
    'linear-gradient(135deg,#7C5C9E,#5B3F78)',
    'linear-gradient(135deg,var(--color-info-600),#16476F)',
    'linear-gradient(135deg,#0E8A8A,#0A6B6B)',
]


def _avatar_gradient(name):
    """Dégradé de fond d'une pastille d'initiales, choisi dans la palette d'après
    le nom (déterministe : même acteur → même couleur)."""
    name = (name or '').strip()
    if not name or name == '—':
        return 'linear-gradient(135deg,var(--color-neutral-500),var(--color-neutral-600))'
    return _AVATAR_GRADIENTS[sum(ord(c) for c in name) % len(_AVATAR_GRADIENTS)]


# Palette catégorielle des répartitions : le vert ouvre (marque / positif),
# l'orange suit en accent vivant, puis violet / bleu / sarcelle ; gris = neutre
# (« non renseigné » / modes sans données).
_CAT_DEFAULT = 'var(--color-neutral-500)'
_NATURE_COLORS = {
    'Travaux': 'var(--color-green-600)',
    'Fournitures': 'var(--color-amber-600)',
    'Prestations': '#6B4E86',
    'Non renseigné': 'var(--color-neutral-500)',
}
_MODE_COLORS = {
    'AOO': 'var(--color-green-600)',
    'AOR_FT': 'var(--color-amber-600)',
    'AOR_PI': '#6B4E86',
    'GAG': 'var(--color-info-500)',
    'PSO': '#0E8A8A', 'PSC': '#0E8A8A', 'PSL': '#0E8A8A', 'PSD': '#0E8A8A',
    'EXECUTION': 'var(--color-neutral-500)',
}


def _dashboard_context():
    """Agrège le journal de collecte cadré sur la mission active (session py4web)."""
    per = active_period()
    sid, gid = per['session_id'], per['gestion_id']

    total_ops, total_montant, last_saisie, hors_mission = 0, 0.0, None, 0
    structures, ministeres = set(), set()
    by_nature, by_mode, recent_struct = {}, {}, {}
    derniers = []

    for code, cfg in PASSATION_MODES.items():
        tbl = _op_table(cfg)
        q = (tbl.is_deleted == False)  # noqa: E712
        if sid:
            q &= (tbl.session == sid)
        elif gid:
            q &= (tbl.gestion == gid)

        # -- volumétrie / montant / fraîcheur (une seule agrégation) --
        c_cnt, c_sum, c_max = tbl.id.count(), tbl.montant_dotation_credit.sum(), tbl.created_on.max()
        agg = db(q).select(c_cnt, c_sum, c_max).first()
        n = (agg[c_cnt] or 0) if agg else 0
        m = (agg[c_sum] or 0) if agg else 0
        last = agg[c_max] if agg else None
        total_ops += n
        total_montant += m
        by_mode[code] = n
        if last and (last_saisie is None or last > last_saisie):
            last_saisie = last

        # -- opérations « hors mission » (session non renseignée) : visibilité --
        if sid:
            hq = (tbl.is_deleted == False) & (tbl.session == None)  # noqa: E711,E712
            if gid:
                hq &= (tbl.gestion == gid)
            hors_mission += db(hq).count()

        # -- structures / ministères distincts (group by) --
        for r in db(q).select(tbl.autorite_contractante, groupby=tbl.autorite_contractante):
            if r[tbl.autorite_contractante]:
                structures.add(r[tbl.autorite_contractante])
        for r in db(q).select(tbl.ministere, groupby=tbl.ministere):
            if r[tbl.ministere]:
                ministeres.add(r[tbl.ministere])

        # -- répartition par nature (nombre d'opérations) ; aor_pi : colonne absente --
        if 'nature_operation' in tbl.fields:
            n_cnt = tbl.id.count()
            for r in db(q).select(tbl.nature_operation, n_cnt, groupby=tbl.nature_operation):
                key = r[tbl.nature_operation] or 0
                by_nature[key] = by_nature.get(key, 0) + (r[n_cnt] or 0)
        elif n:
            by_nature[0] = by_nature.get(0, 0) + n   # bucket « non renseigné »

        # -- structures récemment contrôlées (max date_controle par AC) --
        d_max = tbl.date_controle.max()
        for r in db(q).select(tbl.autorite_contractante, d_max, groupby=tbl.autorite_contractante):
            ac, d = r[tbl.autorite_contractante], r[d_max]
            if ac and d and (ac not in recent_struct or d > recent_struct[ac]):
                recent_struct[ac] = d

        # -- 10 dernières saisies de CETTE table (fusion globale ensuite) --
        has_nat = 'nature_operation' in tbl.fields
        fields = [tbl.id, tbl.objet_operation, tbl.created_on, tbl.created_by, tbl.autorite_contractante]
        if has_nat:
            fields.append(tbl.nature_operation)
        for r in db(q).select(*fields, orderby=~tbl.created_on, limitby=(0, 10)):
            derniers.append(dict(
                objet=r.objet_operation or '—', ac_id=r.autorite_contractante,
                nature_id=(r.nature_operation if has_nat else None),
                user_id=r.created_by, created_on=r.created_on, mode=code,
            ))

    # ----- résolution des libellés (lots groupés : pas de N+1) -----
    recent = sorted(recent_struct.items(), key=lambda kv: kv[1], reverse=True)[:10]
    ac_ids = {a for a, _ in recent} | {d['ac_id'] for d in derniers if d['ac_id']}
    ac_lbl = {}
    if ac_ids:
        for r in db(db.autorite_contractante.id.belongs(list(ac_ids))).select(
                db.autorite_contractante.id, db.autorite_contractante.name, db.autorite_contractante.abbr):
            ac_lbl[r.id] = r.name + ((' (' + r.abbr + ')') if r.abbr else '')

    nat_ids = {k for k in by_nature if k} | {d['nature_id'] for d in derniers if d['nature_id']}
    nat_lbl = {}
    if nat_ids:
        for r in db(db.nature_operation.id.belongs(list(nat_ids))).select(
                db.nature_operation.id, db.nature_operation.operation_nom):
            nat_lbl[r.id] = r.operation_nom

    uids = {d['user_id'] for d in derniers if d['user_id']}
    usr = {}
    if uids:
        for u in db(db.auth_user.id.belongs(list(uids))).select(
                db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name, db.auth_user.username):
            full = ((u.last_name or '').strip() + ' ' + (u.first_name or '').strip()).strip() or u.username or '—'
            ini = ((u.first_name or ' ')[:1] + (u.last_name or ' ')[:1]).strip().upper() or '—'
            usr[u.id] = dict(name=full, initials=ini)

    # ----- répartition par nature : TOUTES les natures du référentiel (la nature est
    # un champ obligatoire) ; on n'affiche jamais de bucket « Non renseigné ». -----
    nature_rows = []
    for nrec in db(db.nature_operation).select(db.nature_operation.id, db.nature_operation.operation_nom,
                                               orderby=db.nature_operation.id):
        c = by_nature.get(nrec.id, 0)
        nature_rows.append(dict(label=nrec.operation_nom, count=c,
                                color=_NATURE_COLORS.get(nrec.operation_nom, _CAT_DEFAULT),
                                pct=int(round(100 * c / total_ops)) if total_ops else 0))
    nature_rows.sort(key=lambda r: r['count'], reverse=True)

    # ----- répartition par mode (une couleur par mode ; part du TOTAL d'opérations) -----
    mode_rows = [dict(label=PASSATION_MODES.get(code, {}).get('label', code),
                      count=c, color=_MODE_COLORS.get(code, _CAT_DEFAULT),
                      pct=int(round(100 * c / total_ops)) if total_ops else 0)
                 for code, c in sorted(by_mode.items(), key=lambda kv: kv[1], reverse=True)]

    # ----- structures récemment contrôlées -----
    recent_structures = [dict(name=ac_lbl.get(ac, '—'), ago=_ago(d), date=_fr_date(d))
                         for ac, d in recent]

    # ----- 10 dernières saisies (fusion + tri global décroissant) -----
    derniers.sort(key=lambda d: d['created_on'] or datetime.min, reverse=True)
    rows = []
    for d in derniers[:10]:
        # « Saisi par » = utilisateur connecté ayant créé l'enregistrement (created_by).
        u = usr.get(d['user_id'], dict(name='—', initials='—'))
        rows.append(dict(
            objet=d['objet'], structure=ac_lbl.get(d['ac_id'], '—'),
            nature=(nat_lbl.get(d['nature_id']) if d['nature_id'] else None) or 'Non renseigné',
            agent_name=u['name'], agent_initials=u['initials'],
            avatar=_avatar_gradient(u['name']),
            created_ago=_ago(d['created_on']),
            mode=PASSATION_MODES.get(d['mode'], {}).get('label', d['mode']),
        ))

    kpi = dict(operations=total_ops, structures=len(structures), ministeres=len(ministeres),
               montant_fmt=_fmt_fcfa(total_montant), last_ago=_ago(last_saisie),
               last_date=(_fr_date(last_saisie) if last_saisie else '—'), hors=hors_mission)

    return dict(active='dashboard', period=per, kpi=kpi,
                nature_rows=nature_rows, mode_rows=mode_rows,
                recent_structures=recent_structures, derniers=rows,
                current_user=_current_user_display())


@action('set_period', method=['GET'])
@action.uses(db, session, auth, access)
def set_period():
    """Mémorise le cadre Gestion/Mission choisi (en-tête) puis revient à la page."""
    g = (request.query.get('gestion') or '').strip()
    s = (request.query.get('session') or '').strip()
    if g:
        session['period_gestion'] = int(g) if g.isdigit() else None
        session['period_session'] = None     # gestion changée → mission par défaut
    if s:
        session['period_session'] = int(s) if s.isdigit() else None
    nxt = (request.query.get('next') or 'dashboard').strip()
    if not nxt.replace('_', '').isalnum():
        nxt = 'dashboard'
    redirect(URL(nxt))


@action('index', method=['GET', 'POST'])
@action.uses('audits/dashboard.html', db, session, auth, access, period)
def index():
    return _dashboard_context()


@action('dashboard', method=['GET', 'POST'])
@action.uses('audits/dashboard.html', db, session, auth, access, period)
def dashboard():
    return _dashboard_context()


@action('collecte', method=['GET', 'POST'])
@action.uses('audits/collecte.html', db, session, auth, access, period)
def collecte():
    return _collecte_context()


def _collecte_context():
    # Liste l'union des opérations de tous les modes de passation.
    #  - `q` : recherche plein-texte (ministère, gestionnaire, objet, n° BOMP).
    #  - Filtres structurés (panneau « Filtre »), combinés en ET : `ministere`
    #    (id), `gestionnaire` (id), `imputation` (valeur exacte), `mode` (code).
    q = (request.query.get('q') or '').strip()
    ql = _search_norm(q)
    f_min = (request.query.get('ministere') or '').strip()
    f_gc = (request.query.get('gestionnaire') or '').strip()
    f_type = (request.query.get('type') or '').strip()
    f_mode = (request.query.get('mode') or '').strip().upper()

    operations = []
    for mode, cfg in PASSATION_MODES.items():
        tbl = _op_table(cfg)
        for r in db(tbl.is_deleted == False).select(orderby=~tbl.id):  # noqa: E712
            # Champs « transverses » lus de façon DÉFENSIVE : tous les modes ne
            # possèdent pas chaque colonne (ex. AOR_PI n'a pas `nature_operation`).
            # Filtres structurés (ET logique).
            if f_mode and mode != f_mode:
                continue
            if f_min and str(_rget(r, 'ministere') or '') != f_min:
                continue
            if f_gc and str(_rget(r, 'autorite_contractante') or '') != f_gc:
                continue
            if f_type and str(_rget(r, 'nature_operation') or '') != f_type:
                continue
            ministere = _ref_label('ref_min', _rget(r, 'ministere'))
            gestionnaire = _ref_label('ref_gc', _rget(r, 'autorite_contractante'))
            objet = _rget(r, 'objet_operation') or ''
            bomp = _rget(r, 'n_bomp') or ''
            imputation = str(_rget(r, 'imputation_budgetaire') or '')
            # Recherche plein-texte (inclut l'imputation budgétaire — cf. placeholder).
            if ql and ql not in _search_norm(
                    ' '.join((ministere, gestionnaire, objet, bomp, imputation))):
                continue
            d = r.created_on
            operations.append(dict(
                mode=mode,
                id=r.id,
                number=_op_number(r),
                sort_key=(d or datetime.min, r.id),
                date=_fr_date(d.date()) if d else '',
                gestionnaire=gestionnaire,
                ministere=ministere,
                objet=objet,
                nature_operation=_ref_label('ref_nature', _rget(r, 'nature_operation')),
                bomp=bomp,
                mode_label=mode,
                pill=cfg['pill'],
                edit_url=URL(cfg['slug'], 'operation', r.id, 'edit'),
                details_url=URL(cfg['slug'], 'details', r.id),
                delete_url=URL(cfg['slug'], 'operation', r.id, 'delete'),
            ))
    operations.sort(key=lambda o: o['sort_key'], reverse=True)

    # Modes de passation proposés par le CTA « Ajouter une opération » : pilotés
    # par la table de référence `mode_passation`, RESTREINTS aux modes réellement
    # inscrits (qui ont un contrôleur + ses routes). L'abrégé = segment d'URL.
    add_modes = [dict(mode=m.mode_passation_abrege,
                      label=m.mode_passation_nom,
                      abrege=m.mode_passation_abrege,
                      url=URL(m.mode_passation_abrege.lower(), 'operation', 'add'))
                 for m in db(db.mode_passation).select(orderby=db.mode_passation.id)
                 if m.mode_passation_abrege.upper() in PASSATION_MODES]

    # Options des combos du panneau « Filtre » (données réelles).
    def _min_label(m):
        return m.name + ((' (' + m.abbr + ')') if m.abbr else '')
    filt_min_options = [dict(id=m.id, label=_min_label(m))
                        for m in db(db.ministere.is_deleted == False).select(orderby=db.ministere.name)]  # noqa: E712
    filt_gc_options = [dict(id=g.id, label=g.name + ((' (' + g.abbr + ')') if g.abbr else ''))
                       for g in db(db.autorite_contractante.is_deleted == False).select(orderby=db.autorite_contractante.name)]  # noqa: E712
    filt_mode_options = [dict(id=m, label=cfg['label']) for m, cfg in PASSATION_MODES.items()]
    filt_type_options = [dict(id=n.id, label=n.operation_nom)
                         for n in db(db.nature_operation).select(orderby=db.nature_operation.id)]

    # Sélections courantes (pour pré-remplir les combos).
    filters = dict(
        ministere=f_min, ministere_label=(_ref_label('ref_min', f_min) if f_min else ''),
        gestionnaire=f_gc, gestionnaire_label=(_ref_label('ref_gc', f_gc) if f_gc else ''),
        type=f_type, type_label=(_ref_label('ref_nature', f_type) if f_type else ''),
        mode=f_mode, mode_label=(PASSATION_MODES[f_mode]['label'] if f_mode in PASSATION_MODES else ''),
    )

    # Pagination : gérée à 100 % CÔTÉ CLIENT (static/js/app.js, composant unifié,
    # plafond 15 lignes/page). Le serveur renvoie donc la liste COMPLÈTE (déjà
    # filtrée/recherchée) ; le découpage en pages se fait dans le navigateur.
    total = len(operations)
    level, message = OPERATION_MESSAGES.get(request.query.get('msg'), ('', ''))
    return dict(active='collecte', operations=operations, count=total,
                add_modes=add_modes, msg_level=level, msg_text=message,
                q=q, filters=filters,
                filt_min_options=filt_min_options, filt_gc_options=filt_gc_options,
                filt_mode_options=filt_mode_options, filt_type_options=filt_type_options,
                current_user=_current_user_display())


@action('test', method=['GET', 'POST'])
@action.uses('audits/test.html', db, session, auth, access, period)
def test():
    """Page de TEST de design (copie de `collecte`) — thème secondaire « noir »
    appliqué via le gabarit audits/test.html. Données identiques à collecte."""
    return _collecte_context()


@action('rapport', method=['GET', 'POST'])
@action.uses('audits/rapport.html', db, session, auth, access, period)
def rapport():
    return dict(active='rapport', current_user=_current_user_display())


def _admin_context():
    """Contexte UNIFIÉ de la page Administration (comptes + gestion réunis).

    Regroupe les données des deux anciennes pages : utilisateurs, rôles,
    ministères, autorités contractantes (gestionnaires), exercices/sessions."""
    # Amorçage : crée les rôles par défaut au premier passage.
    if db(db.groupe).isempty():
        for name, desc in DEFAULT_ROLES:
            db.groupe.insert(name=name, description=desc)
        db.commit()

    roles = db(db.groupe.is_deleted == False).select(orderby=db.groupe.name)  # noqa: E712
    users = []
    for u in db(db.auth_user.is_deleted == False).select(orderby=db.auth_user.first_name):  # noqa: E712
        tags = list(groups.get(u.id) or [])
        full_name = ((u.first_name or '') + ' ' + (u.last_name or '')).strip() or u.username
        users.append(dict(
            id=u.id, name=full_name, first=u.first_name or '', last=u.last_name or '',
            phone=u.phone_number or '', email=u.email,
            role=', '.join(tags) if tags else '—', active=bool(u.is_active)))

    def _min_label(m):
        return m.name + ((' (' + m.abbr + ')') if m.abbr else '')

    ministeres = db(db.ministere.is_deleted == False).select(orderby=db.ministere.name)  # noqa: E712
    gestionnaires = []
    ac_counts = {}  # nb d'autorités contractantes par ministère (affiché onglet Ministère)
    for g in db(db.autorite_contractante.is_deleted == False).select(orderby=db.autorite_contractante.name):  # noqa: E712
        m = db.ministere(g.ministere) if g.ministere else None
        if g.ministere:
            ac_counts[g.ministere] = ac_counts.get(g.ministere, 0) + 1
        gestionnaires.append(dict(
            id=g.id, name=g.name, abbr=g.abbr or '',
            ministere_id=g.ministere or '',
            ministere_label=_min_label(m) if m else '',
            ministere_name=(m.name if m else ''), active=bool(g.is_active)))
    min_options = [dict(id=m.id, label=_min_label(m)) for m in ministeres]

    exercices = []
    for e in db(db.exercice_budgetaire.is_deleted == False).select(  # noqa: E712
            orderby=~db.exercice_budgetaire.annee):
        rows = db((db.session_budgetaire.exercice == e.id) &
                  (db.session_budgetaire.is_deleted == False)).select(  # noqa: E712
            orderby=db.session_budgetaire.id)
        sessions = [dict(
            id=s.id, numero=(s.numero_mission if s.numero_mission is not None else ''),
            objet=s.objet or '', objectif=s.objectif or '',
            debut=s.date_debut.strftime('%Y-%m-%d') if s.date_debut else '',
            fin=s.date_fin.strftime('%Y-%m-%d') if s.date_fin else '',
            range=_range_label(s)) for s in rows]
        exercices.append(dict(id=e.id, annee=e.annee, sessions=sessions))

    current_year = datetime.now().year
    year_options = list(range(current_year + 1, current_year - 6, -1))

    return dict(users=users, roles=roles, ministeres=ministeres, gestionnaires=gestionnaires,
                ac_counts=ac_counts,
                min_options=min_options, exercices=exercices, year_options=year_options,
                current_user=_current_user_display())


def _admin_msg(code):
    """Message flash de la page Administration (dictionnaires comptes + gestion fusionnés)."""
    level, message = dict(GESTION_MESSAGES, **COMPTES_MESSAGES).get(code, ('', ''))
    if code == 'register_failed':
        detail = session.get('comptes_error')
        session['comptes_error'] = None
        if detail:
            message = detail
    return level, message


def _admin_render(active_tab):
    ctx = _admin_context()
    level, message = _admin_msg(request.query.get('msg'))
    ctx.update(active='administration', active_tab=active_tab,
               msg_level=level, msg_text=message)
    return ctx


@action('administration', method=['GET', 'POST'])
@action.uses('audits/administration.html', db, session, auth, access(roles='Administrateur'), period)
def administration():
    """Page unique d'administration : tous les onglets (exercices, ministères,
    gestionnaires, utilisateurs, rôles) réunis dans une seule fenêtre."""
    return _admin_render(request.query.get('tab') or 'exo')


# Routes héritées : conservées (les formulaires CRUD y redirigent encore) ; elles
# rendent désormais la fenêtre Administration unifiée, sur l'onglet correspondant.
@action('comptes', method=['GET', 'POST'])
@action.uses('audits/administration.html', db, session, auth, access(roles='Administrateur'), period)
def comptes():
    return _admin_render('users')


@action('gestion', method=['GET', 'POST'])
@action.uses('audits/administration.html', db, session, auth, access(roles='Administrateur'), period)
def gestion():
    return _admin_render('min')


# ===========================================================================
#  Ministères : CRUD + activation / désactivation
# ===========================================================================
@action('gestion/ministeres/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_ministere():
    f = request.forms
    name = (f.get('nom') or '').strip()
    abbr = (f.get('abbr') or '').strip()
    active = f.get('actif') is not None
    if not name:
        redirect(URL('gestion', vars=dict(msg='min_name')))
    db.ministere.insert(name=name, abbr=abbr, is_active=active)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='min_added')))


@action('gestion/ministeres/<mid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def update_ministere(mid):
    row = db((db.ministere.id == mid) & (db.ministere.is_deleted == False)).select().first()  # noqa: E712
    if not row:
        redirect(URL('gestion', vars=dict(msg='not_found')))
    f = request.forms
    name = (f.get('nom') or '').strip()
    abbr = (f.get('abbr') or '').strip()
    if not name:
        redirect(URL('gestion', vars=dict(msg='min_name')))
    row.update_record(name=name, abbr=abbr)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='min_updated')))


@action('gestion/ministeres/<mid:int>/activate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def activate_ministere(mid):
    db((db.ministere.id == mid) & (db.ministere.is_deleted == False)).update(is_active=True)  # noqa: E712
    db.commit()
    redirect(URL('gestion', vars=dict(msg='min_activated')))


@action('gestion/ministeres/<mid:int>/deactivate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def deactivate_ministere(mid):
    db((db.ministere.id == mid) & (db.ministere.is_deleted == False)).update(is_active=False)  # noqa: E712
    db.commit()
    redirect(URL('gestion', vars=dict(msg='min_deactivated')))


@action('gestion/ministeres/<mid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def delete_ministere(mid):
    db(db.ministere.id == mid).update(is_deleted=True, is_active=False)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='min_deleted')))


# ===========================================================================
#  Gestionnaires de crédit : CRUD + activation / désactivation
# ===========================================================================
def _valid_ministere(min_id):
    if not min_id:
        return None
    try:
        min_id = int(min_id)
    except (TypeError, ValueError):
        return None
    if db((db.ministere.id == min_id) & (db.ministere.is_deleted == False)).count():  # noqa: E712
        return min_id
    return None


@action('gestion/gestionnaires/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_gestionnaire():
    f = request.forms
    name = (f.get('nom') or '').strip()
    abbr = (f.get('abbr') or '').strip()
    active = f.get('actif') is not None
    min_id = _valid_ministere(f.get('ministere_id'))
    if not name:
        redirect(URL('gestion', vars=dict(msg='gc_name')))
    if not min_id:
        redirect(URL('gestion', vars=dict(msg='gc_min')))
    db.autorite_contractante.insert(name=name, abbr=abbr, ministere=min_id, is_active=active)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='gc_added')))


@action('gestion/gestionnaires/<gid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def update_gestionnaire(gid):
    row = db((db.autorite_contractante.id == gid) & (db.autorite_contractante.is_deleted == False)).select().first()  # noqa: E712
    if not row:
        redirect(URL('gestion', vars=dict(msg='not_found')))
    f = request.forms
    name = (f.get('nom') or '').strip()
    abbr = (f.get('abbr') or '').strip()
    min_id = _valid_ministere(f.get('ministere_id'))
    if not name:
        redirect(URL('gestion', vars=dict(msg='gc_name')))
    if not min_id:
        redirect(URL('gestion', vars=dict(msg='gc_min')))
    row.update_record(name=name, abbr=abbr, ministere=min_id)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='gc_updated')))


@action('gestion/gestionnaires/<gid:int>/activate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def activate_gestionnaire(gid):
    db((db.autorite_contractante.id == gid) & (db.autorite_contractante.is_deleted == False)).update(is_active=True)  # noqa: E712
    db.commit()
    redirect(URL('gestion', vars=dict(msg='gc_activated')))


@action('gestion/gestionnaires/<gid:int>/deactivate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def deactivate_gestionnaire(gid):
    db((db.autorite_contractante.id == gid) & (db.autorite_contractante.is_deleted == False)).update(is_active=False)  # noqa: E712
    db.commit()
    redirect(URL('gestion', vars=dict(msg='gc_deactivated')))


@action('gestion/gestionnaires/<gid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def delete_gestionnaire(gid):
    db(db.autorite_contractante.id == gid).update(is_deleted=True, is_active=False)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='gc_deleted')))


# ===========================================================================
#  Exercices budgétaires & sessions
# ===========================================================================
def _as_list(value):
    """Normalise une valeur de `request.forms` en liste.

    ombott stocke les champs répétés sous forme de liste et les champs uniques
    sous forme de chaîne ; on uniformise pour itérer dessus.
    """
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _insert_sessions(exo_id, forms):
    """Insère les sessions du formulaire (champs répétés debut/fin/objet/objectif).

    Renvoie le nombre de sessions créées. Les blocs entièrement vides sont
    ignorés.
    """
    debuts = _as_list(forms.get('debut'))
    fins = _as_list(forms.get('fin'))
    objets = _as_list(forms.get('objet'))
    objectifs = _as_list(forms.get('objectif'))
    numeros = _as_list(forms.get('numero_mission'))
    n = max(len(debuts), len(fins), len(objets), len(objectifs), len(numeros))
    created = 0
    for i in range(n):
        debut = _parse_date(debuts[i] if i < len(debuts) else '')
        fin = _parse_date(fins[i] if i < len(fins) else '')
        objet = (objets[i] if i < len(objets) else '').strip()
        objectif = (objectifs[i] if i < len(objectifs) else '').strip()
        numero = _to_int(numeros[i] if i < len(numeros) else '')
        if not (debut or fin or objet or objectif or numero):
            continue  # bloc vide → on ignore
        db.session_budgetaire.insert(exercice=exo_id, numero_mission=numero,
                                     date_debut=debut, date_fin=fin,
                                     objet=objet, objectif=objectif)
        created += 1
    return created


@action('gestion/exercices/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_exercice():
    try:
        annee = int((request.forms.get('year') or '').strip())
    except (TypeError, ValueError):
        redirect(URL('gestion', vars=dict(msg='exo_year')))
    # Réutilise l'exercice de l'année si elle existe déjà, sinon le crée.
    exo = db((db.exercice_budgetaire.annee == annee) &
             (db.exercice_budgetaire.is_deleted == False)).select().first()  # noqa: E712
    exo_id = exo.id if exo else db.exercice_budgetaire.insert(annee=annee)
    _insert_sessions(exo_id, request.forms)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='exo_added')))


@action('gestion/exercices/<eid:int>/sessions/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_session(eid):
    exo = db((db.exercice_budgetaire.id == eid) &
             (db.exercice_budgetaire.is_deleted == False)).select().first()  # noqa: E712
    if not exo:
        redirect(URL('gestion', vars=dict(msg='not_found')))
    _insert_sessions(eid, request.forms)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='sess_added')))


@action('gestion/sessions/<sid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def update_session(sid):
    row = db((db.session_budgetaire.id == sid) &
             (db.session_budgetaire.is_deleted == False)).select().first()  # noqa: E712
    if not row:
        redirect(URL('gestion', vars=dict(msg='not_found')))
    f = request.forms
    row.update_record(
        numero_mission=_to_int(f.get('numero_mission')),
        date_debut=_parse_date(f.get('debut')),
        date_fin=_parse_date(f.get('fin')),
        objet=(f.get('objet') or '').strip(),
        objectif=(f.get('objectif') or '').strip(),
    )
    db.commit()
    redirect(URL('gestion', vars=dict(msg='sess_updated')))


@action('gestion/sessions/<sid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def delete_session(sid):
    db(db.session_budgetaire.id == sid).update(is_deleted=True)
    db.commit()
    redirect(URL('gestion', vars=dict(msg='sess_deleted')))


# ===========================================================================
#  Opérations auditées (par mode de passation)
#
#  Chaque mode de passation est une table distincte qui porte la section
#  commune « Opérations » + ses sections propres. La page « Collecte » liste
#  l'union de tous les modes ; les actions ciblent (mode, id).
#  On démarre par AOO ; ajouter un mode = ajouter une entrée ici + sa table.
# ===========================================================================
# ---------------------------------------------------------------------------
#  Specs dérivées des tables pydal `operations` / `allotissements`
#  (source de vérité UNIQUE). Chaque champ est classé par sa section, lue dans
#  le `comment` du Field : « Section: <titre> | col. <XX> ».
# ---------------------------------------------------------------------------
_META_FIELDS = {'is_deleted', 'created_on', 'created_by', 'gestion', 'session'}

# Sections CALCULÉES par le gabarit Excel : jamais saisies ni affichées dans
# l'application (le fichier Excel les calcule). Les champs restent en base mais
# sont retirés du rendu (formulaire + détails) et de l'export.
HIDDEN_SECTION_PREFIXES = ('Temps total pour la conduite',)


def _kind_for(field):
    """Type pydal → genre de widget utilisé par les templates et le parsing."""
    t = field.type
    if t == 'boolean':
        return 'bool'
    if t == 'date':
        return 'date'
    if t == 'integer':
        return 'int'
    if t == 'text':
        return 'txt'
    if t.startswith('double') or t.startswith('decimal'):
        return 'num'
    if t == 'reference ministere':
        return 'ref_min'
    if t == 'reference autorite_contractante':
        return 'ref_gc'
    if t == 'reference nature_operation':
        return 'ref_nature'
    return 'str'


def _field_section(field):
    """Titre de section porté par le commentaire « Section: X | col. Y »."""
    c = field.comment or ''
    if c.startswith('Section:'):
        return c.split('|', 1)[0].replace('Section:', '', 1).strip()
    return 'Autres'


def _field_col(field):
    """Colonne Excel portée par le commentaire (« … | col. XX ») ou None."""
    c = field.comment or ''
    if '| col.' in c:
        return c.split('| col.', 1)[1].strip()
    return None


def _sections_from_table(table, skip=()):
    """[(key, titre, [(name, label, kind), …]), …] dérivé d'une table pydal,
    les champs regroupés par section (l'ordre des colonnes est préservé)."""
    skip = set(skip) | _META_FIELDS | {'id'}
    sections, index = [], {}
    for name in table.fields:
        if name in skip:
            continue
        f = table[name]
        title = _field_section(f)
        if any(title.startswith(p) for p in HIDDEN_SECTION_PREFIXES):
            continue  # section calculée par Excel → non rendue
        if title not in index:
            index[title] = []
            sections.append((title, title, index[title]))
        index[title].append((f.name, f.label, _kind_for(f)))
    return sections


def _flat_fields(sections):
    """Aplatit une spec de sections en [(name, label, kind), …]."""
    return [item for _k, _t, items in sections for item in items]


def _table_fields(table, skip=()):
    """[(name, label, kind), …] de tous les champs métier d'une table (à plat)."""
    skip = set(skip) | _META_FIELDS | {'id'}
    return [(table[n].name, table[n].label, _kind_for(table[n]))
            for n in table.fields if n not in skip]


def _col_key(letters):
    """Clé de tri d'une colonne Excel (« A »→1, « Q »→17, « AA »→27…)."""
    n = 0
    for ch in (letters or ''):
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n


def _ordered_sections(op_table, op_sections, allot_table, allot_sections):
    """Sections (opération + lot) d'UN mode dans l'ORDRE DES COLONNES de sa grille
    (sections op et lot entrelacées). Chaque entrée : (type, key, titre, items).

    Appelé par le contrôleur PROPRE à chaque mode lors de la construction de sa
    config (cf. controllers/<mode>_controller.py)."""
    tagged = []
    for table, typ, secs in ((op_table, 'op', op_sections),
                             (allot_table, 'lot', allot_sections)):
        for skey, title, items in secs:
            col = next((_field_col(table[n]) for n, _l, _k in items if _field_col(table[n])), '')
            tagged.append((_col_key(col), typ, skey, title, items))
    tagged.sort(key=lambda s: s[0])
    return [(typ, skey, title, items) for _c, typ, skey, title, items in tagged]


# ---------------------------------------------------------------------------
#  Registre des modes de passation.
#
#  VIDE au chargement de l'engine. Chaque mode de passation s'inscrit lui-même via
#  SON PROPRE contrôleur (controllers/<mode>_controller.py) en appelant
#  register_mode() — un fichier modèle + un fichier contrôleur par mode. La page
#  « Collecte » liste l'union des opérations de tous les modes inscrits.
# ---------------------------------------------------------------------------
PASSATION_MODES = {}


def register_mode(code, cfg):
    """Inscrit un mode de passation dans le registre partagé et renvoie sa config.

    `cfg` (dict) doit fournir :
      - table, attr_table : noms des tables `<mode>_operations` / `<mode>_allotissements`
      - label, pill, template
      - sections, allot_sections, allot_fields, all_sections (dérivés des tables)
      - field_rows    : groupes de champs à aligner sur une même ligne (par mode)
      - grille_export : {file, sheet, start_row} du gabarit Excel, ou None
    Appelé à l'import du contrôleur propre au mode."""
    code = (code or '').upper()
    cfg['code'] = code
    cfg['slug'] = code.lower()          # segment d'URL des routes du mode (ex. 'aor_pi')
    PASSATION_MODES[code] = cfg
    return cfg


def build_mode_config(op_table, allot_table, **cfg):
    """Construit la config d'un mode à partir de ses deux tables pydal.

    Dérive sections / allot_sections / allot_fields / all_sections à partir des
    tables (`<mode>_operations`, `<mode>_allotissements`) et fusionne les clés
    propres au mode (label, pill, template, field_rows, grille_export). Le
    contrôleur du mode n'a plus qu'à appeler register_mode(code, build_mode_config(...))."""
    op_sections = _sections_from_table(op_table)
    # `objet_lot` (saisi en section « Opérations ») et `numero_lot` (auto) ne sont
    # pas rendus dans les sections d'allotissement.
    allot_sections = _sections_from_table(allot_table, skip={'operation', 'objet_lot', 'numero_lot'})
    allot_fields = _table_fields(allot_table, skip={'operation', 'numero_lot'})
    cfg.update(
        table=op_table._tablename,
        attr_table=allot_table._tablename,
        sections=op_sections,
        allot_sections=allot_sections,
        allot_fields=allot_fields,
        all_sections=_ordered_sections(op_table, op_sections, allot_table, allot_sections),
        field_rows=cfg.get('field_rows', []),
        grille_export=cfg.get('grille_export'),
    )
    return cfg


OPERATION_MESSAGES = {
    'op_added':   ('ok',  "Opération enregistrée avec succès."),
    'op_updated': ('edit', "Opération modifiée avec succès."),
    'op_deleted': ('del', "Opération supprimée."),
    'bad_mode':   ('err', "Mode de passation inconnu."),
    'not_found':  ('err', "Opération introuvable."),
    'export_na':  ('err', "Export Excel non disponible pour ce mode de passation."),
}


def _mode_cfg(mode):
    """Renvoie la config d'un mode de passation, ou None si inconnu."""
    return PASSATION_MODES.get((mode or '').upper())


def _op_table(cfg):
    return db[cfg['table']]


def _op_number(row):
    """Numéro d'opération lisible : AAAAMMJJ + id sur 5 chiffres."""
    d = row.created_on
    return d.strftime('%Y%m%d') + str(row.id).zfill(5)


def _ref_label(kind, value):
    """Libellé d'une référence ministère / autorité contractante / nature."""
    if not value:
        return ''
    if kind == 'ref_min':
        r = db.ministere(value)
        return r.name if r else ''
    if kind == 'ref_nature':
        r = db.nature_operation(value)
        return r.operation_nom if r else ''
    r = db.autorite_contractante(value)
    return r.name if r else ''


def _valid_ref(kind, value):
    """Valide un id de référence (ministère/autorité contractante/nature)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    if kind == 'ref_nature':
        # `nature_operation` est un simple référentiel (sans soft delete).
        return value if db(db.nature_operation.id == value).count() else None
    tbl = db.ministere if kind == 'ref_min' else db.autorite_contractante
    if db((tbl.id == value) & (tbl.is_deleted == False)).count():  # noqa: E712
        return value
    return None


def _clean_number(raw):
    """Nettoie une saisie numérique : retire tous les séparateurs de milliers
    (espace, espace insécable, espace fine…) et normalise la virgule décimale.
    ``str.split()`` découpe sur tout caractère d'espace Unicode (NBSP inclus)."""
    s = str(raw if raw is not None else '').strip()
    return ''.join(s.split()).replace(',', '.')


def _coerce(raw, kind):
    """Convertit une valeur brute de formulaire selon le genre de champ."""
    if kind == 'bool':
        return raw is not None
    if kind == 'date':
        return _parse_date(raw)
    if kind == 'int':
        try:
            return int(float(_clean_number(raw)))
        except (TypeError, ValueError):
            return 0
    if kind == 'num':
        try:
            return float(_clean_number(raw))
        except (TypeError, ValueError):
            return None
    if kind in ('ref_min', 'ref_gc', 'ref_nature'):
        return _valid_ref(kind, raw)
    return (raw or '').strip()


def _parse_operation(forms, sections):
    """Construit le dict {champ: valeur} d'une opération depuis le formulaire.

    NB : « nombre_lots » est un contrôle d'interface (génération des lignes de
    lots), PAS un champ du modèle → il n'est pas dans `sections` et n'est donc
    jamais persisté ici."""
    data = {}
    for _key, _title, items in sections:
        for name, _label, kind in items:
            data[name] = _coerce(forms.get(name), kind)
    return data


def _save_allotissements(cfg, op_id, forms):
    """Remplace les allotissements (lots) de l'opération par ceux du formulaire.

    Chaque lot est posté sous des champs indexés ``lot_<i>_<champ>`` ; la liste
    des index actifs vient du champ répété ``lot_index`` (robuste aux cases à
    cocher non transmises). Les lots entièrement vides sont ignorés."""
    if not cfg.get('attr_table'):
        return
    attr_tbl = db[cfg['attr_table']]
    db(attr_tbl.operation == op_id).update(is_deleted=True)
    fields = cfg['allot_fields']
    # Un enregistrement par lot généré (l'ordre des marqueurs lot_index = Lot 1..N),
    # afin de conserver l'alignement « Lot k » même si certains lots sont vides.
    for pos, i in enumerate(_as_list(forms.get('lot_index')), start=1):
        row = {name: _coerce(forms.get('lot_%s_%s' % (i, name)), kind)
               for name, _label, kind in fields}
        # Numéro du lot (entier) renseigné automatiquement (1..N).
        try:
            row['numero_lot'] = int(i)
        except (TypeError, ValueError):
            row['numero_lot'] = pos
        # « attributaire_objet » recopie l'objet du lot (section « Opérations ») ;
        # « attributaire_lot » = n° du lot (implicite, garanti même sans JS).
        if 'attributaire_objet' in row:
            row['attributaire_objet'] = row.get('objet_lot') or ''
        if 'attributaire_lot' in row:
            row['attributaire_lot'] = str(row['numero_lot'])
        # Écart = montant de l'estimation − montant du marché (calculé).
        if 'ecart_entre_montant_estimatif' in row:
            row['ecart_entre_montant_estimatif'] = (
                float(row.get('montant_estimation') or 0) - float(row.get('montant_marche') or 0))
        attr_tbl.insert(operation=op_id, **row)


# ---------------------------------------------------------------------------
#  Rendu HTML des champs de formulaire (déporté ici : yatl ne sait pas exécuter
#  des `def` avec boucles dans un bloc de gabarit). Le template appelle
#  simple_field()/lot_tpl() reçus dans le contexte.
# ---------------------------------------------------------------------------
_CAL_SVG = ('<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-muted-2 '
            'pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5.5" width="16" height="14" rx="2"/>'
            '<path d="M4 9.5h16M8.5 3.5v3M15.5 3.5v3"/></svg>')
_DEC_SVG = ('<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="m15 6-6 6 6 6"/></svg>')
_INC_SVG = ('<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>')
_TRASH_SVG = ('<svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a1 1 0 0 1 '
              '1-1h6a1 1 0 0 1 1 1v2M6 6l1 14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-14"/></svg>')


def _html_escape(s):
    s = str(s) if s not in (None, '') else ''
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def _simple_field_html(fname, label, kind, val, checked):
    """HTML d'un champ « simple » (sans combo de référence) — utilisé aussi par
    les cartes de lot."""
    # « Nom de l'Agent DGMP » = acteur de saisie connecté (auth) : champ en
    # LECTURE SEULE, pré-rempli côté serveur ; non modifiable à la saisie.
    if fname == 'agent_dgmp':
        return ('<div><label class="lbl">' + label + '</label><input type="text" name="' + fname +
                '" class="field bg-black/[.03]" readonly tabindex="-1" value="' + _html_escape(val) +
                '" placeholder="—"></div>')
    if kind == 'bool':
        return ('<div class="toggle-row"><span>' + label + '</span><label class="switch">'
                '<input type="checkbox" name="' + fname + '" ' + ('checked' if checked else '') + '>'
                '<span class="track"></span><span class="thumb"></span></label></div>')
    if kind == 'txt':
        return ('<div><label class="lbl">' + label + '</label><textarea name="' + fname +
                '" class="field" rows="2" placeholder="Valeur">' + _html_escape(val) + '</textarea></div>')
    if kind == 'date':
        # Champ date avec date picker maison (branding) : input en lecture seule,
        # ouvert au clic ; le calendrier est rendu par JS dans `.dp-pop`.
        return ('<div><label class="lbl">' + label + '</label>'
                '<div class="relative" data-dp>' + _CAL_SVG +
                '<input type="text" name="' + fname + '" class="field pl-10" value="' + _html_escape(val) +
                '" placeholder="jj/mm/aaaa" readonly autocomplete="off" data-dp-input>'
                '<div class="dp-pop" data-dp-pop hidden></div></div></div>')
    if kind == 'int':
        # Entier SAISISSABLE (input number : frappe + flèches natives).
        return ('<div><label class="lbl">' + label + '</label><input type="number" name="' + fname +
                '" class="field" value="' + _html_escape(val) + '" min="0" step="1" inputmode="numeric" '
                'placeholder="0"></div>')
    if kind == 'num':
        # « Montant disponible » : calculé (dotation − total des montants de marché
        # des lots) → lecture seule, rempli par JS.
        if fname == 'situation_execution_ligne_budgetaire_montant_disponible':
            return ('<div><label class="lbl">' + label + '</label><input type="text" name="' + fname +
                    '" class="field bg-black/[.03]" readonly tabindex="-1" data-montant-dispo '
                    'value="' + _html_escape(val) + '" placeholder="—"></div>')
        # Champ numérique (montant) : séparateur de milliers appliqué par JS.
        return ('<div><label class="lbl">' + label + '</label><input type="text" name="' + fname +
                '" class="field" value="' + _html_escape(val) + '" inputmode="numeric" data-thousands '
                'placeholder="Valeur"></div>')
    # str / autres → champ texte
    return ('<div><label class="lbl">' + label + '</label><input type="text" name="' + fname +
            '" class="field" value="' + _html_escape(val) + '" placeholder="Valeur"></div>')


def _group_into_rows(items, field_rows):
    """Regroupe les champs consécutifs déclarés dans `field_rows` en « lignes »
    (chaque ligne = liste de (name, label, kind)). Les autres champs → ligne seule.

    `field_rows` (groupes de noms de champs à aligner sur une même ligne) est
    PROPRE au mode : il est fourni par la config du mode (cf. register_mode)."""
    row_of = {nm: gi for gi, grp in enumerate(field_rows or ()) for nm in grp}
    rows, i = [], 0
    while i < len(items):
        g = row_of.get(items[i][0])
        if g is None:
            rows.append([items[i]])
            i += 1
        else:
            grp = []
            while i < len(items) and row_of.get(items[i][0]) == g:
                grp.append(items[i])
                i += 1
            rows.append(grp)
    return rows


def _grid_row_html(html_cells, cols):
    """Enveloppe des cellules dans une grille de `cols` colonnes (style inline,
    fiable y compris pour le HTML généré dynamiquement par JS)."""
    return ('<div style="display:grid;grid-template-columns:repeat(%d,minmax(0,1fr));'
            'gap:1rem">%s</div>' % (cols, html_cells))


# Garantie de l'offre : minimale = 1 % et maximale = 1,5 % du montant de
# l'estimation du lot → champs CALCULÉS (lecture seule), remplis par JS. Les noms
# diffèrent selon le mode (AOO vs AOR_FT).
GARANTIE_MIN_FIELDS = {'garantie_offre_minimale',
                       'garantie_offre_comprise_entre_1_garantie_minimale_1'}
GARANTIE_MAX_FIELDS = {'garantie_offre_maximale',
                       'garantie_offre_comprise_entre_1_garantie_maximale_1_5'}


def _lot_section_template_html(items, field_rows):
    """Gabarit HTML d'UN bloc « Lot » pour UNE section d'allotissement.

    Les marqueurs ``__IDX__`` (index du lot, dans les ``name``) et ``__LOTNO__``
    (numéro affiché) sont remplacés côté JS lors de la génération dynamique
    pilotée par « Nombre de lots ».

    Quelques sections ont une disposition sur-mesure :
      - « Montant de l'estimation » : objet du lot (lecture seule) EN FACE du montant.
      - « Garantie de l'offre… »   : garantie minimale (1 %) et maximale (1,5 %)
        CALCULÉES depuis le montant de l'estimation (lecture seule).
    """
    names = [n for n, _l, _k in items]

    def fld(t):
        n, l, k = t
        # Garantie min/max : calculées (1 % / 1,5 % du montant de l'estimation).
        if n in GARANTIE_MIN_FIELDS or n in GARANTIE_MAX_FIELDS:
            attr = 'data-garantie-min' if n in GARANTIE_MIN_FIELDS else 'data-garantie-max'
            return ('<div><label class="lbl">' + l + '</label>'
                    '<input type="text" name="lot___IDX___' + n + '" '
                    'class="field bg-black/[.03]" readonly tabindex="-1" '
                    + attr + '="__IDX__" placeholder="—"></div>')
        return _simple_field_html('lot___IDX___' + n, l, k, '', False)

    # Corps du lot (uniquement des champs d'allotissement), avec quelques
    # dispositions sur-mesure par section.
    body = []
    if 'montant_estimation' in names:
        # Un seul champ : le montant (entier formaté, séparateurs de milliers).
        for t in items:
            if t[0] == 'montant_estimation':
                body.append('<div><label class="lbl">Montant</label>'
                            '<input type="text" name="lot___IDX___montant_estimation" class="field" '
                            'inputmode="numeric" data-thousands placeholder="Montant"></div>')
            else:
                body.append(fld(t))
    elif 'attributaire_nom' in names:
        # Raison sociale (2/3) + NCC (1/3) sur la même ligne ; « Lot » implicite (caché).
        nom = next((t for t in items if t[0] == 'attributaire_nom'), None)
        ncc = next((t for t in items if t[0] == 'attributaire_ncc'), None)
        if nom and ncc:
            body.append('<div style="display:grid;grid-template-columns:2fr 1fr;gap:1rem">'
                        + fld(nom) + fld(ncc) + '</div>')
        for n, l, k in items:
            if n in ('attributaire_nom', 'attributaire_ncc'):
                continue
            if n == 'attributaire_lot':
                body.append('<input type="hidden" name="lot___IDX___attributaire_lot" value="__LOTNO__">')
            elif n == 'attributaire_objet':
                # Objet du lot recopié de la section « Opérations » (lecture seule, rempli par JS).
                body.append('<div><label class="lbl">' + l + '</label>'
                            '<input type="text" name="lot___IDX___attributaire_objet" '
                            'class="field bg-black/[.03]" readonly tabindex="-1" '
                            'data-objet-display="__IDX__" placeholder="—"></div>')
            else:
                body.append(fld((n, l, k)))
    elif 'ecart_entre_montant_estimatif' in names:
        # Écart = montant de l'estimation − montant du marché (calculé, lecture seule).
        for n, l, k in items:
            if n == 'ecart_entre_montant_estimatif':
                body.append('<div><label class="lbl">' + l + '</label>'
                            '<input type="text" name="lot___IDX___ecart_entre_montant_estimatif" '
                            'class="field bg-black/[.03]" readonly tabindex="-1" '
                            'data-ecart="__IDX__" placeholder="—"></div>')
            else:
                body.append(fld((n, l, k)))
    else:
        # Rendu générique avec alignements multi-colonnes (cf. cfg['field_rows']).
        for _row in _group_into_rows(items, field_rows):
            if len(_row) > 1:
                body.append(_grid_row_html(''.join(fld(t) for t in _row), len(_row)))
            else:
                body.append(fld(_row[0]))

    # Chaque bloc de lot est un ACCORDÉON ; l'en-tête « Lot X » (clic) replie/déplie.
    # Le ``<span data-objet-label>`` reçoit « : <objet> » via JS (débounce 5s,
    # uniquement si le nombre de lots > 1).
    return ('<div class="lot-acc open" data-lot-block>'
            '<button type="button" class="lot-acc-head" data-acc-toggle>'
            '<svg class="lot-acc-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>'
            'Lot __LOTNO__<span data-objet-label="__IDX__" class="font-normal text-muted-2"></span></button>'
            '<div class="lot-acc-body">' + ''.join(body) + '</div></div>')


def _objet_lot_tpl_html():
    """Gabarit d'UN champ « Objet du Lot » (un par lot quand N>1)."""
    return ('<div data-lot-objet><label class="lbl">Objet du Lot __LOTNO__</label>'
            '<input type="text" name="lot___IDX___objet_lot" class="field" '
            'placeholder="Objet du lot __LOTNO__"></div>')


def _prefill_value(v, kind):
    """Valeur d'un champ formatée pour pré-remplir un widget de formulaire."""
    if kind == 'date':
        return v.strftime('%d/%m/%Y') if v else ''
    if kind == 'bool':
        return bool(v)
    if kind == 'ref_min':
        return dict(id=v or '', label=_ref_label('ref_min', v))
    if kind == 'ref_gc':
        return dict(id=v or '', label=_ref_label('ref_gc', v))
    if kind == 'ref_nature':
        return dict(id=v or '', label=_ref_label('ref_nature', v))
    if kind == 'int':
        return '' if v is None else v
    if kind == 'num':
        # Convertit en float (les colonnes decimal renvoient un Decimal non
        # sérialisable en JSON pour l'état des lots).
        if v is None:
            return ''
        try:
            return float(v)
        except (TypeError, ValueError):
            return str(v)
    return v or ''


def _operation_form_context(active='collecte', mode='AOO', row=None):
    """Contexte commun au formulaire d'ajout / modification d'opération."""
    cfg = _mode_cfg(mode)
    sections = cfg['sections']

    ministeres = db(db.ministere.is_deleted == False).select(orderby=db.ministere.name)  # noqa: E712
    min_options = [dict(id=m.id, label=m.name + ((' (' + m.abbr + ')') if m.abbr else ''))
                   for m in ministeres]
    gc_options = []
    for g in db(db.autorite_contractante.is_deleted == False).select(orderby=db.autorite_contractante.name):  # noqa: E712
        gc_options.append(dict(id=g.id, min_id=g.ministere or '',
                               label=g.name + ((' (' + g.abbr + ')') if g.abbr else '')))
    nature_options = [dict(id=n.id, label=n.operation_nom)
                      for n in db(db.nature_operation).select(orderby=db.nature_operation.id)]

    # Valeurs de préremplissage (édition) → dict prêt pour le template.
    data, allotissements = {}, []
    if row is not None:
        for name, _l, kind in _flat_fields(sections):
            data[name] = _prefill_value(row[name], kind)
        attr_tbl = db[cfg['attr_table']]
        for a in db((attr_tbl.operation == row.id) & (attr_tbl.is_deleted == False)).select():  # noqa: E712
            allotissements.append({name: _prefill_value(a[name], kind)
                                   for name, _l, kind in cfg['allot_fields']})

    # « Agent DGMP » = utilisateur connecté (champ en lecture seule). À l'ajout, on
    # pré-remplit avec son nom ; en édition, on conserve la valeur enregistrée.
    if row is None:
        data['agent_dgmp'] = (_current_user_display() or {}).get('name', '')

    # État initial des lots, indexé 1..N, injecté en JSON pour la génération JS
    # (le lot k correspond au k-ième allotissement enregistré).
    allot_state = {str(i + 1): lot for i, lot in enumerate(allotissements)}
    allot_state_json = json.dumps(allot_state, default=str).replace('<', '\\u003c')
    # Nombre de lots initial du contrôle d'interface : le nombre d'allotissements
    # déjà enregistrés (édition), au minimum 1 (création).
    lot_count = max(1, len(allotissements))

    # Disposition des lignes PROPRE au mode (cf. cfg['field_rows']) : on lie le
    # paramètre via des closures pour que le gabarit appelle group_rows()/lot_tpl()
    # sans connaître le mode.
    field_rows = cfg.get('field_rows', [])

    # Gestion (exercice) / Session pour la barre collante du formulaire.
    #  - défaut gestion : l'exercice de l'année en cours (sinon le plus récent) ;
    #  - défaut session : la DERNIÈRE session (chronologique) de cette gestion ;
    #  - en édition : valeurs déjà enregistrées sur la ligne si présentes.
    exercices = db(db.exercice_budgetaire.is_deleted == False).select(  # noqa: E712
        orderby=~db.exercice_budgetaire.annee)
    exercice_options = [dict(id=e.id, annee=e.annee) for e in exercices]
    session_options, _last_sess = [], {}
    for e in exercices:
        sess = db((db.session_budgetaire.exercice == e.id) &
                  (db.session_budgetaire.is_deleted == False)).select(  # noqa: E712
            orderby=db.session_budgetaire.date_debut | db.session_budgetaire.id)
        for i, s in enumerate(sess, start=1):
            _num = s.numero_mission if s.numero_mission is not None else i
            session_options.append(dict(id=s.id, gestion=e.id, label='Mission %d' % _num))
            _last_sess[e.id] = s.id
    gestion_default = next((e.id for e in exercices if e.annee == datetime.now().year),
                           (exercices[0].id if exercices else ''))
    session_default = _last_sess.get(gestion_default, '')
    if row is not None:
        if row.gestion:
            gestion_default = row.gestion
        if row.session:
            session_default = row.session

    return dict(
        active=active, all_sections=cfg['all_sections'], mode=mode,
        hide_header=True,
        exercice_options=exercice_options, session_options=session_options,
        gestion_default=gestion_default, session_default=session_default,
        min_options=min_options, gc_options=gc_options, nature_options=nature_options,
        data=data, allotissements=allotissements, allot_state_json=allot_state_json,
        lot_count=lot_count,
        simple_field=_simple_field_html,
        lot_tpl=(lambda items: _lot_section_template_html(items, field_rows)),
        objet_lot_tpl=_objet_lot_tpl_html(),
        group_rows=(lambda items: _group_into_rows(items, field_rows)),
        is_edit=(row is not None),
        op_id=(row.id if row is not None else 0),
        # Routes PROPRES au mode (cf. controllers/<mode>_controller.py).
        add_url=URL(cfg['slug'], 'operation', 'add'),
        edit_url=(URL(cfg['slug'], 'operation', row.id, 'edit') if row is not None else ''),
        current_user=_current_user_display(),
    )


# ---------------------------------------------------------------------------
#  Helpers d'ACTIONS (réutilisés par les routes PROPRES à chaque mode).
#  Chaque contrôleur de mode déclare ses @action (ajout/détails/modification/
#  suppression/export) et délègue l'orchestration à ces fonctions.
# ---------------------------------------------------------------------------
def op_row(mode, oid):
    """Ligne d'opération non supprimée du mode, ou None."""
    cfg = _mode_cfg(mode)
    tbl = _op_table(cfg)
    return db((tbl.id == oid) & (tbl.is_deleted == False)).select().first()  # noqa: E712


def form_context(mode, oid=None):
    """Contexte du formulaire d'ajout (oid=None) ou de modification (oid).
    Renvoie None si l'opération à modifier est introuvable."""
    row = None
    if oid is not None:
        row = op_row(mode, oid)
        if not row:
            return None
    return _operation_form_context(mode=mode, row=row)


def _gs_from_forms(forms):
    """Rattachement Gestion / Session posté par la barre du formulaire (ids ou None).
    Ces champs sont `writable=False` (hors saisie auto) : on les écrit explicitement."""
    def _to_id(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None
    return dict(gestion=_to_id(forms.get('gestion')), session=_to_id(forms.get('session')))


def create_operation(mode, forms):
    """Crée une opération + ses allotissements depuis le formulaire. Renvoie l'id."""
    cfg = _mode_cfg(mode)
    data = _parse_operation(forms, cfg['sections'])
    data.update(_gs_from_forms(forms))
    # Acteur de saisie = utilisateur connecté (le `default` du modèle est figé à
    # l'import, donc on renseigne explicitement created_by à chaque création). Le
    # « Nom de l'Agent DGMP » (lecture seule au formulaire) est figé sur ce même
    # acteur, côté serveur, pour éviter toute divergence.
    data['created_by'] = auth.user_id
    if 'agent_dgmp' in _op_table(cfg).fields:
        data['agent_dgmp'] = (_current_user_display() or {}).get('name', '')
    op_id = _op_table(cfg).insert(**data)
    _save_allotissements(cfg, op_id, forms)
    db.commit()
    return op_id


def update_operation(mode, oid, forms):
    """Met à jour l'opération + remplace ses allotissements. False si introuvable."""
    cfg = _mode_cfg(mode)
    row = op_row(mode, oid)
    if not row:
        return False
    vals = _parse_operation(forms, cfg['sections'])
    vals.update(_gs_from_forms(forms))
    row.update_record(**vals)
    _save_allotissements(cfg, oid, forms)
    db.commit()
    return True


def soft_delete_operation(mode, oid):
    """Marque l'opération comme supprimée (soft delete)."""
    cfg = _mode_cfg(mode)
    tbl = _op_table(cfg)
    db(tbl.id == oid).update(is_deleted=True)
    db.commit()


# NB : les routes d'ajout / modification / suppression / détails / export sont
# désormais déclarées par CHAQUE contrôleur de mode (controllers/<mode>_controller.py)
# sous le préfixe d'URL du mode (ex. ``aor_pi/operation/add``). Elles délèguent à
# create_operation / update_operation / soft_delete_operation / details_context /
# export_xlsx ci-dessus et dessous. Seule la suppression GROUPÉE (multi-modes,
# depuis la page collecte) reste mutualisée ici.


@action('operations/delete', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def delete_operations():
    """Suppression groupée : reçoit des jetons « MODE:id » (un par opération
    cochée) et marque chacune comme supprimée (soft delete)."""
    n = 0
    for token in _as_list(request.forms.get('op')):
        try:
            mode, oid = str(token).split(':', 1)
            oid = int(oid)
        except (ValueError, TypeError):
            continue
        cfg = _mode_cfg(mode)
        if not cfg:
            continue
        tbl = _op_table(cfg)
        if db((tbl.id == oid) & (tbl.is_deleted == False)).count():  # noqa: E712
            db(tbl.id == oid).update(is_deleted=True)
            n += 1
    db.commit()
    redirect(URL('collecte', vars=dict(msg='op_deleted')))


_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _col_idx(letters):
    """« A » → 0, « B » → 1, … « AA » → 26, « DP » → 119 (index 0-based)."""
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n - 1


# Export « gabarit » : remplit le fichier Excel source (openpyxl) aux colonnes
# d'origine (dérivées du `comment` des Field, « … | col. XX »).
# UNE LIGNE PAR LOT : les champs de l'opération sont répétés sur chaque ligne,
# les champs du lot varient. Le gabarit ({file, sheet, start_row}) est PROPRE au
# mode : il est porté par cfg['grille_export'] (cf. register_mode).


def _export_value(value, kind):
    """Valeur formatée pour une cellule d'export."""
    if kind == 'bool':
        return 'oui' if value else 'non'
    if kind == 'date':
        return value.strftime('%d/%m/%Y') if value else ''
    if kind in ('ref_min', 'ref_gc', 'ref_nature'):
        return _ref_label(kind, value)
    if value is None:
        return ''
    if kind == 'num':
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def _xlsx_set(ws, ref, value):
    """Écrit une cellule en ignorant les cellules fusionnées (lecture seule)."""
    try:
        ws[ref] = value
    except (AttributeError, TypeError):
        pass


def export_xlsx(mode):
    """Export Excel du mode : remplit le gabarit (openpyxl). UNE LIGNE PAR LOT —
    les champs de l'opération sont répétés, les champs du lot varient ; une
    opération sans lot produit tout de même une ligne.

    Renvoie les octets du classeur (et positionne les en-têtes de réponse), ou
    None si le gabarit du mode est absent/illisible (le contrôleur redirige alors)."""
    cfg = _mode_cfg(mode)
    if not cfg:
        return None
    grille = cfg.get('grille_export')
    path = os.path.join(_APP_DIR, 'grilles', grille['file']) if grille else None
    if not grille or not path or not os.path.exists(path):
        return None

    import openpyxl

    op_tbl = _op_table(cfg)
    allot_tbl = db[cfg['attr_table']]
    # Champ → (lettre de colonne, kind), dérivé du commentaire des Field.
    op_map = {n: (_field_col(op_tbl[n]), k)
              for n, _l, k in _flat_fields(cfg['sections']) if _field_col(op_tbl[n])}
    allot_map = {n: (_field_col(allot_tbl[n]), k)
                 for n, _l, k in cfg['allot_fields'] if _field_col(allot_tbl[n])}

    ops = db(op_tbl.is_deleted == False).select(orderby=op_tbl.id)  # noqa: E712
    allot_by_op = {}
    for a in db(allot_tbl.is_deleted == False).select(orderby=allot_tbl.id):  # noqa: E712
        allot_by_op.setdefault(a.operation, []).append(a)

    try:
        wb = openpyxl.load_workbook(path)
        ws = wb[grille['sheet']]
    except Exception:
        return None

    start = grille['start_row']
    # Vide la zone de données du gabarit (lignes-modèles + exemples) pour ne
    # conserver que les données réelles écrites ensuite (styles préservés).
    for _row in ws.iter_rows(min_row=start, max_row=ws.max_row,
                             min_col=1, max_col=ws.max_column):
        for _cell in _row:
            if _cell.value is not None:
                try:
                    _cell.value = None
                except (AttributeError, TypeError):
                    pass

    r = start
    for n_op, op in enumerate(ops, start=1):
        lots = allot_by_op.get(op.id) or [None]  # au moins une ligne par opération
        for a in lots:
            _xlsx_set(ws, 'A%d' % r, n_op)  # N° d'opération, répété sur ses lignes
            for name, (col, kind) in op_map.items():
                val = _export_value(op[name], kind)
                if val != '':
                    _xlsx_set(ws, '%s%d' % (col, r), val)
            if a is not None:
                for name, (col, kind) in allot_map.items():
                    val = _export_value(a[name], kind)
                    if val != '':
                        _xlsx_set(ws, '%s%d' % (col, r), val)
            r += 1

    bio = io.BytesIO()
    wb.save(bio)
    response.headers['Content-Type'] = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename="export_%s.xlsx"' % mode
    return bio.getvalue()


def _detail_text(v, kind, name=None):
    """Valeur d'un champ formatée pour l'affichage en lecture seule."""
    if kind == 'bool':
        return 'Oui' if v else 'Non'
    if kind == 'date':
        return v.strftime('%d/%m/%Y') if v else '—'
    if kind in ('ref_min', 'ref_gc', 'ref_nature'):
        return _ref_label(kind, v) or '—'
    if v in (None, ''):
        return '—'
    # Montants → séparateur de milliers (num + montant_estimation entier).
    if kind == 'num' or name == 'montant_estimation':
        try:
            return format(int(round(float(v))), ',d').replace(',', ' ')
        except (TypeError, ValueError):
            pass
    return str(v).strip()


def details_context(mode, oid):
    """Contexte de la page « détails » d'une opération (blocs op + lots dans
    l'ordre de la grille). Renvoie None si l'opération est introuvable."""
    cfg = _mode_cfg(mode)
    if not cfg:
        return None
    tbl = _op_table(cfg)
    row = db((tbl.id == oid) & (tbl.is_deleted == False)).select().first()  # noqa: E712
    if not row:
        return None

    # Allotissements (enregistrements) dans l'ordre.
    allot_tbl = db[cfg['attr_table']]
    allot_records = db((allot_tbl.operation == row.id) &
                       (allot_tbl.is_deleted == False)).select(orderby=allot_tbl.id)

    def _allot_block(title, items):
        """Bloc d'allotissement = section affichée PAR LOT (« Lot k : objet » + champs)."""
        lots = []
        for i, a in enumerate(allot_records, start=1):
            lots.append(dict(
                numero=(a.numero_lot or i), objet=a.objet_lot or '',
                rows=[dict(label=label, value=_detail_text(a[name], kind, name), kind=kind)
                      for name, label, kind in items if name != 'attributaire_lot'],
            ))
        return dict(type='allot', title=title, lots=lots)

    # Blocs dans le MÊME ORDRE que le formulaire (cf. base de données -aoo_vf.xlsx).
    blocks = []
    for typ, _skey, title, items in cfg['all_sections']:
        if typ == 'op':
            blocks.append(dict(type='op', title=title, rows=[
                dict(label=label, value=_detail_text(row[name], kind, name), kind=kind)
                for name, label, kind in items
            ]))
            if any(n == 'nature_operation' for n, _l, _k in items):
                blocks.append(dict(type='op', title='Opérations',
                                   rows=[dict(label='Nombre de lots',
                                              value=str(len(allot_records)), kind='int')]))
        else:
            blocks.append(_allot_block(title, items))

    # Gestion / Session de l'opération (chips lecture seule de l'en-tête détails).
    op_gestion = ''
    if row.gestion:
        _e = db.exercice_budgetaire(row.gestion)
        op_gestion = _e.annee if _e else ''
    op_session = ''
    if row.session:
        _s = db.session_budgetaire(row.session)
        if _s:
            _sess = db((db.session_budgetaire.exercice == _s.exercice) &
                       (db.session_budgetaire.is_deleted == False)).select(  # noqa: E712
                orderby=db.session_budgetaire.date_debut | db.session_budgetaire.id)
            _idx = next((i for i, x in enumerate(_sess, start=1) if x.id == _s.id), '')
            op_session = 'Session %s' % _idx if _idx else ''

    return dict(active='collecte', mode=mode, op_id=row.id, op_number=_op_number(row),
                op_mode=mode, op_bomp=_rget(row, 'n_bomp') or '', op_objet=_rget(row, 'objet_operation') or '',
                op_gestion=op_gestion, op_session=op_session,
                blocks=blocks, current_user=_current_user_display())


