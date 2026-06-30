# Modèles de l'app « AUDIT a posteriori ».
#
# Importer ce package charge et enregistre l'ensemble des tables auprès de `db`.
# L'ORDRE DE CHARGEMENT importe : chaque table « reference » doit être définie
# APRÈS sa cible.
#
#   0) audits/table_parametres_models → référentiel (ministere, autorite_contractante,
#      exercice_budgetaire, session_budgetaire, nature_operation). Défini en PREMIER
#      car référencé par le métier et le modèle AOO.
#   1) models.py            → modèle MÉTIER (+ RBAC applicatif) : groupe.
#   2) audit_auth_models.py → AUTORISATION / AUTHENTIFICATION : password_reset_token.
#   3) audits/model_aoo     → modèle AOO : aoo_operations + aoo_allotissements.
from ..common import db

# 0) Tables de paramètres (référentiel audit).
from .audits import table_parametres_models as _params
_params.define_all(db)

# 1-2) Métier (rôles applicatifs) + auth applicative.
from . import models               # noqa: F401, E402
from . import audit_auth_models    # noqa: F401, E402

# 3) Modèles par MODE de passation : chaque mode a son propre modèle
#    (model_<mode>) définissant ses tables <mode>_operations / <mode>_allotissements.
from .audits import model_aoo as _aoo        # noqa: E402  AOO
_aoo.define_all(db)
from .audits import model_aor_pi as _aor_pi   # noqa: E402  AOR — prestations intellectuelles
_aor_pi.define_all(db)
from .audits import model_aor_ft as _aor_ft   # noqa: E402  AOR — fournitures & travaux
_aor_ft.define_all(db)
from .audits import model_gag as _gag          # noqa: E402  GAG — gré à gré
_gag.define_all(db)
