# -*- coding: utf-8 -*-
"""
Tables de PARAMÈTRES (référentiel) de l'app « AUDIT a posteriori ».

Regroupe, sous une nomenclature unique, tout le référentiel audité. Ces tables
ont été migrées depuis ``models/models.py`` vers le package ``audits/`` ; leurs
définitions (champs, ordre, valeurs par défaut) sont conservées à l'identique afin
de ne déclencher AUCUNE migration sur les tables déjà présentes dans storage.db.

Elles doivent être définies AVANT tout modèle qui les référence (métier,
operations / allotissements) — l'ordre de chargement est piloté par
``models/__init__.py``.

Tables :
  - ministere
  - exercice_budgetaire
  - session_budgetaire
  - autorite_contractante   (nouvelle : analogue « nouvelle nomenclature » du
                              gestionnaire de crédit pour mp_aoo)
  - nature_operation        (référence Travaux / Fournitures / Prestations)
  - mode_passation          (modes de passation : AOO, AOR, GAG, PSO, PSC…)
"""
from pydal import Field
from pydal.validators import IS_NOT_EMPTY
from datetime import datetime, timezone
from ...common import auth


def _meta_fields(modified=False):
    """Champs de traçabilité communs. Recréés à chaque table : un objet Field
    pydal ne peut pas être partagé entre plusieurs tables.

    `modified=True` ajoute `modified_on` (date de dernière modification, mise à
    jour automatiquement à chaque enregistrement)."""
    fields = [
        Field("is_deleted",  "boolean",  default=False, readable=False),
        Field("created_on",  "datetime", default=lambda: datetime.now(timezone.utc),
                                         writable=False),
    ]
    if modified:
        fields.append(
            Field("modified_on", "datetime",
                  default=lambda: datetime.now(timezone.utc),
                  update=lambda: datetime.now(timezone.utc),
                  writable=False),
        )
    fields.append(
        Field("created_by",  "reference auth_user",
                              default=auth.user_id, writable=False),
    )
    return fields


def define_ministere(db):
    """Table de référence `ministere`."""
    db.define_table("ministere",
        Field("name",        "text",     requires=IS_NOT_EMPTY()),
        Field("abbr",        "string",   default=""),
        Field("is_active",   "boolean",  default=True),
        *_meta_fields(modified=True),
    )
    db.commit()
    return db.ministere


def define_exercice_budgetaire(db):
    """Table de référence `exercice_budgetaire` (une année budgétaire)."""
    db.define_table("exercice_budgetaire",
        Field("annee",       "integer",  requires=IS_NOT_EMPTY()),
        *_meta_fields(),
    )
    db.commit()
    return db.exercice_budgetaire


def define_session_budgetaire(db):
    """Table de référence `session_budgetaire` (période datée d'un exercice)."""
    db.define_table("session_budgetaire",
        Field("exercice",    "reference exercice_budgetaire"),
        Field("objet",       "text",     default=""),
        Field("objectif",    "text",     default=""),
        Field("date_debut",  "date"),
        Field("date_fin",    "date"),
        *_meta_fields(),
    )
    db.commit()
    return db.session_budgetaire


def define_autorite_contractante(db):
    """Table de référence `autorite_contractante` (entité contractante rattachée
    à un ministère)."""
    db.define_table("autorite_contractante",
        Field("name",        "text",     requires=IS_NOT_EMPTY()),
        Field("abbr",        "string",   default=""),
        Field("ministere",   "reference ministere"),
        Field("is_active",   "boolean",  default=True),
        *_meta_fields(modified=True),
    )
    db.commit()
    return db.autorite_contractante


def seed_ministere(db):
    """Amorce la table `ministere` depuis la liste PSPM (cf. `_pspm_seed_data`).

    Idempotent par `name` : seuls les ministères absents sont insérés, de sorte
    qu'un ajout dans la liste source soit pris en compte au rechargement. Le code
    PSPM (col. D du document) est conservé dans `abbr` pour servir de référence."""
    from ._pspm_seed_data import MINISTERES
    _changed = False
    for code, name in MINISTERES:
        if db(db.ministere.name == name).isempty():
            db.ministere.insert(name=name, abbr=str(code))
            _changed = True
    if _changed:
        db.commit()


def seed_autorite_contractante(db):
    """Amorce la table `autorite_contractante` depuis la liste PSPM, chaque autorité
    étant rattachée à son ministère via le code PSPM (cf. `_pspm_seed_data`).

    Idempotent par couple (`name`, `ministere`). Suppose `seed_ministere` exécuté
    au préalable afin de résoudre les références."""
    from ._pspm_seed_data import MINISTERES, AUTORITES_CONTRACTANTES
    # code PSPM -> id ministere (résolu par nom, indépendant de `abbr`).
    code_to_id = {}
    for code, name in MINISTERES:
        row = db(db.ministere.name == name).select(db.ministere.id).first()
        if row:
            code_to_id[code] = row.id
    _changed = False
    for code, noms in AUTORITES_CONTRACTANTES.items():
        mid = code_to_id.get(code)
        if not mid:
            continue
        for nom in noms:
            q = ((db.autorite_contractante.name == nom) &
                 (db.autorite_contractante.ministere == mid))
            if db(q).isempty():
                db.autorite_contractante.insert(name=nom, ministere=mid)
                _changed = True
    if _changed:
        db.commit()


def define_nature_operation(db):
    """Table de référence `nature_operation`."""
    db.define_table(
        "nature_operation",
        Field("operation_nom", "string", label="Operation nom"),
        Field("operation_code", "string", label="Operation code"),
        format="%(operation_nom)s",
        migrate=True,
    )
    db.commit()
    return db.nature_operation


def seed_nature_operation(db):
    """Insère les valeurs de référence si la table est vide."""
    if db(db.nature_operation).isempty():
        for _r in [
            dict(operation_nom="Travaux", operation_code="trv"),
            dict(operation_nom="Fournitures", operation_code="frt"),
            dict(operation_nom="Prestations", operation_code="prt"),
        ]:
            db.nature_operation.insert(**_r)
        db.commit()


def define_mode_passation(db):
    """Table de référence `mode_passation` (modes de passation des marchés).

    Alimente le dropdown « Ajouter une opération » de la page collecte ; l'abrégé
    sert de segment d'URL (``operation/<abrege>``)."""
    db.define_table(
        "mode_passation",
        Field("mode_passation_nom", "string", label="Mode passation nom",
              requires=IS_NOT_EMPTY()),
        Field("mode_passation_abrege", "string", label="Mode passation abrégé"),
        format="%(mode_passation_nom)s",
        migrate=True,
    )
    db.commit()
    return db.mode_passation


def seed_mode_passation(db):
    """Insère les modes de passation de référence manquants (idempotent par abrégé,
    afin que l'ajout d'un nouveau mode soit pris en compte au rechargement)."""
    _changed = False
    for _r in [
        dict(mode_passation_nom="Appel d'Offres Ouvert", mode_passation_abrege="AOO"),
        dict(mode_passation_nom="Appel d'Offres Restreint — prestations intellectuelles", mode_passation_abrege="AOR_PI"),
        dict(mode_passation_nom="Appel d'Offres Restreint — fournitures & travaux", mode_passation_abrege="AOR_FT"),
        dict(mode_passation_nom="Gré à Gré", mode_passation_abrege="GAG"),
        dict(mode_passation_nom="Procédure Simplifiée Ouverte", mode_passation_abrege="PSO"),
        dict(mode_passation_nom="Procédure Simplifiée par Consultation", mode_passation_abrege="PSC"),
        dict(mode_passation_nom="Procédure Simplifiée par cotation", mode_passation_abrege="PSL"),
        dict(mode_passation_nom="Procédure Simplifiée à Demande de prix", mode_passation_abrege="PSD"),
        dict(mode_passation_nom="Exécution", mode_passation_abrege="EXECUTION"),
    ]:
        if db(db.mode_passation.mode_passation_abrege == _r["mode_passation_abrege"]).isempty():
            db.mode_passation.insert(**_r)
            _changed = True
    if _changed:
        db.commit()


def seed_exercice_session(db):
    """Amorce les exercices budgétaires (année en cours + deux précédentes) avec
    deux sessions chacun, si AUCUN exercice n'existe encore. Idempotent : ne fait
    rien dès qu'au moins un exercice est présent (la saisie se fait ensuite via la
    page Gestion). Sert de défaut au sélecteur Gestion/Session du formulaire."""
    if not db(db.exercice_budgetaire).isempty():
        return
    cur = datetime.now().year
    for y in (cur - 2, cur - 1, cur):
        eid = db.exercice_budgetaire.insert(annee=y)
        db.session_budgetaire.insert(
            exercice=eid, objet="1re session",
            date_debut=datetime(y, 1, 15).date(), date_fin=datetime(y, 6, 30).date())
        db.session_budgetaire.insert(
            exercice=eid, objet="2e session",
            date_debut=datetime(y, 7, 1).date(), date_fin=datetime(y, 12, 31).date())
    db.commit()


def define_all(db):
    """Définit toutes les tables de paramètres dans l'ordre de dépendance, puis
    amorce les valeurs de référence."""
    define_ministere(db)
    define_exercice_budgetaire(db)
    define_session_budgetaire(db)
    define_autorite_contractante(db)
    define_nature_operation(db)
    seed_nature_operation(db)
    define_mode_passation(db)
    seed_mode_passation(db)
    seed_exercice_session(db)
    # Référentiel PSPM : ministères puis autorités contractantes (qui les référencent).
    seed_ministere(db)
    seed_autorite_contractante(db)
    return db
