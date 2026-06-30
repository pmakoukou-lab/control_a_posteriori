import re

from py4web import action, URL, redirect, request

from pydal.validators import CRYPT

from ..common import db, session, auth, groups

from ..fixtures.rbac_fixture import access

from .password_reset import (
    create_reset_token, get_valid_token, consume_token,
    find_user_by_email, set_user_password, send_reset_email,
)

# ============================================================================
#  Contrôleur d'AUTORISATION / AUTHENTIFICATION de l'app « AUDIT a posteriori ».
#
#  Périmètre : connexion, déconnexion, réinitialisation de mot de passe et
#  gestion des comptes (création d'utilisateurs et de rôles). La logique métier
#  vit dans audit_controler.py ; les modèles d'auth dans models/audit_auth_models.py.
# ============================================================================


def _parse_roles(f):
    """Normalise le champ multi-valeurs `role` (chaîne, liste ou absent) en liste."""
    raw = f.get('role')
    raw = raw if isinstance(raw, list) else ([raw] if raw else [])
    return [r.strip() for r in raw if r and r.strip()]


# ----------------------------------------------------------------------------
#  Connexion
# ----------------------------------------------------------------------------
@action('login', method=['GET', 'POST'])
@action.uses('audits/login.html', session, db, auth)
def login():
    error = ""
    notice = ""
    if request.query.get("msg") == "reset":
        notice = ("Votre mot de passe a été réinitialisé. "
                  "Connectez-vous avec vos nouveaux identifiants.")
    if request.method == "POST":
        identifier = (request.forms.get("username") or "").strip()
        password = request.forms.get("password") or ""
        # Identifiant = nom d'utilisateur OU e-mail. Vérification du mot de passe
        # via le validateur CRYPT du champ (même mécanique que py4web).
        if identifier and password:
            value = identifier.lower()
            field = db.auth_user.email if "@" in value else db.auth_user.username
            user = db(field == value).select().first()
            if user and CRYPT()(password)[0] == user.password and user.is_active != False:  # noqa: E712
                auth.store_user_in_session(user.id)
                redirect(URL("dashboard"))
        error = "Identifiant ou mot de passe incorrect."
    return dict(error=error, notice=notice)


# ----------------------------------------------------------------------------
#  Mot de passe oublié → envoi du lien de réinitialisation
# ----------------------------------------------------------------------------
@action('password_forget', method=['GET', 'POST'])
@action.uses('audits/password_forget.html', session, db)
def password_forget():
    sent = False
    error = ""
    if request.method == "POST":
        email = (request.forms.get("email") or "").strip().lower()
        # Validation simple du format ( a@b.c ).
        domain = email.split("@")[-1] if "@" in email else ""
        if "@" not in email or "." not in domain:
            error = "Veuillez saisir une adresse e-mail valide."
        else:
            user = find_user_by_email(email)
            if user:
                raw = create_reset_token(user.id)
                link = URL("reset", raw, scheme=True)
                name = (getattr(user, "first_name", None)
                        or getattr(user, "username", None) or email)
                send_reset_email(user.email, name, link)
            # Anti-énumération : on confirme toujours l'envoi, que le compte
            # existe ou non.
            sent = True
    return dict(sent=sent, error=error)


# ----------------------------------------------------------------------------
#  Réinitialisation via le jeton reçu par e-mail
# ----------------------------------------------------------------------------
@action("reset/<token>", method=["GET", "POST"])
@action.uses('audits/password_reset.html', session, db)
def password_reset(token):
    row = get_valid_token(token)
    invalid = row is None
    error = ""
    if not invalid and request.method == "POST":
        pw = request.forms.get("password") or ""
        pw2 = request.forms.get("password2") or ""
        if not pw or not pw2:
            error = "Veuillez remplir les deux champs."
        elif len(pw) < 8:
            error = "Le mot de passe doit contenir au moins 8 caractères."
        elif pw != pw2:
            error = "Les deux mots de passe ne correspondent pas."
        else:
            user = db(db.auth_user.id == row.user_id).select().first()
            if not user:
                error = "Compte introuvable."
            else:
                set_user_password(user, pw)
                consume_token(row)
                # Succès → retour au login avec un message de confirmation.
                redirect(URL("login", vars=dict(msg="reset")))
    return dict(token=token, invalid=invalid, done=False, error=error)


# ----------------------------------------------------------------------------
#  Ajout d'un compte utilisateur (onglet « Utilisateurs » de la page comptes)
# ----------------------------------------------------------------------------
@action('comptes/users/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_account():
    f = request.forms
    first_name = (f.get('prenom') or '').strip()
    last_name  = (f.get('nom') or '').strip()
    email      = (f.get('email') or '').strip().lower()
    # Le validateur du modèle attend ^\+?\d{8,15}$ (aucun séparateur) : on retire
    # espaces, points, tirets et parenthèses saisis par l'utilisateur.
    phone      = re.sub(r'[\s.\-()]', '', (f.get('tel') or '').strip())
    password   = f.get('pwd') or ''
    password2  = f.get('pwd2') or ''
    # Multi-sélection : le formulaire envoie un champ `role` par rôle coché.
    roles      = _parse_roles(f)

    # --- Validations minimales côté serveur -------------------------------
    if '@' not in email or '.' not in email.split('@')[-1]:
        redirect(URL('comptes', vars=dict(msg='bad_email')))
    if len(password) < 8:
        redirect(URL('comptes', vars=dict(msg='bad_pwd')))
    if password != password2:
        redirect(URL('comptes', vars=dict(msg='pwd_mismatch')))

    # --- Création du compte (même mécanique que l'inscription publique) ----
    username = email.split('@')[0]
    db.auth_user.password.requires = CRYPT()
    user = auth.register(
        {
            'username':     username,
            'first_name':   first_name,
            'last_name':    last_name,
            'email':        email,
            'password':     password,
            'phone_number': phone,
        },
        send=False,
    )

    if not user.get('id'):
        # On remonte le détail réel des erreurs de validation (champ par champ),
        # consommé une seule fois par la page comptes.
        errors = user.get('errors') or {}
        session['comptes_error'] = "  ".join(
            "%s : %s" % (k, v) for k, v in errors.items()
        ) or "Échec de l'ajout de l'utilisateur."
        redirect(URL('comptes', vars=dict(msg='register_failed')))

    # Rôles (stockés comme tags sur l'utilisateur, cf. common.groups)
    for role in roles:
        groups.add(user['id'], role)

    # Compte créé par un administrateur : actif immédiatement.
    db(db.auth_user.id == user['id']).update(is_active=True)
    db.commit()
    redirect(URL('comptes', vars=dict(msg='user_added')))


# ----------------------------------------------------------------------------
#  Ajout d'un rôle (onglet « Role » de la page comptes)
# ----------------------------------------------------------------------------
@action('comptes/roles/add', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def add_role():
    f = request.forms
    name = (f.get('nom') or '').strip()
    desc = (f.get('desc') or '').strip()

    if not name:
        redirect(URL('comptes', vars=dict(msg='role_name')))
    if db(db.groupe.name == name).count():
        redirect(URL('comptes', vars=dict(msg='role_exists')))

    db.groupe.insert(name=name, description=desc)
    db.commit()
    redirect(URL('comptes', vars=dict(msg='role_added')))


# ----------------------------------------------------------------------------
#  Modification d'un compte utilisateur
# ----------------------------------------------------------------------------
@action('comptes/users/<uid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def update_account(uid):
    user = db((db.auth_user.id == uid) & (db.auth_user.is_deleted == False)).select().first()  # noqa: E712
    if not user:
        redirect(URL('comptes', vars=dict(msg='not_found')))

    f = request.forms
    first_name = (f.get('prenom') or '').strip()
    last_name  = (f.get('nom') or '').strip()
    email      = (f.get('email') or '').strip().lower()
    phone      = re.sub(r'[\s.\-()]', '', (f.get('tel') or '').strip())
    password   = f.get('pwd') or ''
    password2  = f.get('pwd2') or ''
    roles      = _parse_roles(f)

    # --- Validations (unicité hors enregistrement courant) -----------------
    if '@' not in email or '.' not in email.split('@')[-1]:
        redirect(URL('comptes', vars=dict(msg='bad_email')))
    if db((db.auth_user.email == email) & (db.auth_user.id != uid)).count():
        redirect(URL('comptes', vars=dict(msg='email_taken')))
    if phone:
        if not re.match(r'^\+?\d{8,15}$', phone):
            redirect(URL('comptes', vars=dict(msg='bad_phone')))
        if db((db.auth_user.phone_number == phone) & (db.auth_user.id != uid)).count():
            redirect(URL('comptes', vars=dict(msg='phone_taken')))

    # Mot de passe : modifié uniquement s'il est renseigné.
    if password or password2:
        if len(password) < 8:
            redirect(URL('comptes', vars=dict(msg='bad_pwd')))
        if password != password2:
            redirect(URL('comptes', vars=dict(msg='pwd_mismatch')))

    fields = dict(first_name=first_name, last_name=last_name,
                  email=email, phone_number=phone)
    if password:
        fields['password'] = CRYPT()(password)[0]
    user.update_record(**fields)

    # Rôles : on remplace l'ensemble des tags par la nouvelle sélection.
    current = list(groups.get(uid) or [])
    if current:
        groups.remove(uid, current)
    for role in roles:
        groups.add(uid, role)

    db.commit()
    redirect(URL('comptes', vars=dict(msg='user_updated')))


# ----------------------------------------------------------------------------
#  Activation / désactivation d'un compte
# ----------------------------------------------------------------------------
@action('comptes/users/<uid:int>/activate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def activate_account(uid):
    db((db.auth_user.id == uid) & (db.auth_user.is_deleted == False)).update(is_active=True)  # noqa: E712
    db.commit()
    redirect(URL('comptes', vars=dict(msg='user_activated')))


@action('comptes/users/<uid:int>/deactivate', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def deactivate_account(uid):
    db((db.auth_user.id == uid) & (db.auth_user.is_deleted == False)).update(is_active=False)  # noqa: E712
    db.commit()
    redirect(URL('comptes', vars=dict(msg='user_deactivated')))


# ----------------------------------------------------------------------------
#  Suppression d'un compte (soft delete : is_deleted = True)
# ----------------------------------------------------------------------------
@action('comptes/users/<uid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def delete_account(uid):
    db(db.auth_user.id == uid).update(is_deleted=True, is_active=False)
    db.commit()
    redirect(URL('comptes', vars=dict(msg='user_deleted')))


# ----------------------------------------------------------------------------
#  Modification d'un rôle (édition inline dans le tableau)
# ----------------------------------------------------------------------------
@action('comptes/roles/<rid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def update_role(rid):
    f = request.forms
    name = (f.get('nom') or '').strip()
    desc = (f.get('desc') or '').strip()

    role = db((db.groupe.id == rid) & (db.groupe.is_deleted == False)).select().first()  # noqa: E712
    if not role:
        redirect(URL('comptes', vars=dict(msg='not_found')))
    if not name:
        redirect(URL('comptes', vars=dict(msg='role_name')))
    if db((db.groupe.name == name) & (db.groupe.id != rid)).count():
        redirect(URL('comptes', vars=dict(msg='role_exists')))

    # Si le nom change, on répercute le renommage sur les tags des utilisateurs.
    if name != role.name:
        tt = groups.tag_table
        old_path = "/%s/" % role.name.strip("/")
        new_path = "/%s/" % name.strip("/")
        db(tt.tagpath == old_path).update(tagpath=new_path)

    role.update_record(name=name, description=desc)
    db.commit()
    redirect(URL('comptes', vars=dict(msg='role_updated')))


# ----------------------------------------------------------------------------
#  Suppression d'un rôle (soft delete : is_deleted = True)
# ----------------------------------------------------------------------------
@action('comptes/roles/<rid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles='Administrateur'))
def delete_role(rid):
    db(db.groupe.id == rid).update(is_deleted=True)
    db.commit()
    redirect(URL('comptes', vars=dict(msg='role_deleted')))


# ----------------------------------------------------------------------------
#  Déconnexion (lien « Quitter » de l'en-tête)
# ----------------------------------------------------------------------------
@action("logout")
@action.uses(session)
def logout():
    session.clear()
    redirect(URL("login"))
