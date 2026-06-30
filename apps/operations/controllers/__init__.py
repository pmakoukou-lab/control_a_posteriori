# On importe chaque fichier de contrôleur pour que py4web voie les @action
# from . import default   # Ton contrôleur de base (index, etc.)
# from . import produits  # TON NOUVEAU CONTRÔLEUR
from . import (
    controllers,  # etc..
    user_api,
    admin_controller,
    audit_controler,        # « engine » mutualisé : routes + registre des modes
    aoo_controller,         # mode AOO : inscrit sa config dans le registre
    aor_pi_controller,      # mode AOR — prestations intellectuelles
    aor_ft_controller,      # mode AOR — fournitures & travaux
    gag_controller,         # mode GAG — gré à gré
    audit_auth_controler
)
