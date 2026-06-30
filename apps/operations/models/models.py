"""
This file defines the database models
"""

from pydal.validators import *
from ..common import Field, db, auth
from datetime import datetime, timezone

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#

db.define_table("groupe",
    Field("name",        "string",   unique=True,  requires=IS_NOT_EMPTY()),
    Field("description", "text",     default=""),
    Field("actif",       "boolean",  default=True),
    Field("created_on",  "datetime", default=lambda: datetime.now(timezone.utc),
                                     writable=False),
    Field("created_by",  "reference auth_user",
                          default=auth.user_id, writable=False),
    Field(
        'is_deleted',
        'boolean',
        readable = False,
        writable = True,
        default  = False,
    ),
)
db.commit()

# NOTE: les tables `permission`, `permission_group` et `historique` ont été
# RETIRÉES (modèles métier non utilisés). Seule `groupe` (rôles applicatifs)
# subsiste — elle alimente la page « comptes ».

# ---------------------------------------------------------------------------
#  Référentiel métier — migré vers models/audits/table_parametres_models.py
#  (nouvelle nomenclature) :
#    - `ministere`, `exercice_budgetaire`, `session_budgetaire`
#    - `gestionnaire_credit` est REMPLACÉ par `autorite_contractante`.
#  Toutes ces tables sont définies AVANT ce module (cf. models/__init__.py).
# ---------------------------------------------------------------------------
