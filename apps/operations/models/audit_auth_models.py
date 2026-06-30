"""
Modèle : jetons de réinitialisation de mot de passe.

La table stocke uniquement le HACHÉ du jeton (jamais le jeton brut), avec une
date d'expiration et un drapeau d'usage unique. Le jeton brut n'existe que le
temps d'être envoyé par e-mail.

Import : assurez-vous que ce module est chargé au démarrage de l'app, après
`common` (qui définit `db`) et après la table utilisateur. Dans la plupart des
scaffolds py4web, ajoutez/maintenez dans __init__.py :

    from . import common
    from . import models          # <-- cette ligne
    from . import controllers

La table référence `auth_user`. Si votre table utilisateur porte un autre nom,
adaptez la référence ci-dessous (et RESET_USER_TABLE dans settings).
"""
from datetime import datetime
from ..common import db, Field


db.define_table(
    "password_reset_token",
    Field("user_id", "reference auth_user"),
    Field("token_hash", "string", length=64, writable=False, readable=False),
    Field("created_on", "datetime", default=lambda: datetime.utcnow(), writable=False),
    Field("expires_on", "datetime", writable=False),
    Field("used", "boolean", default=False, writable=False),
    migrate=True,
)

db.commit()
