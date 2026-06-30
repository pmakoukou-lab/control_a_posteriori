"""
Logique métier de la réinitialisation de mot de passe.

- création d'un jeton sécurisé (haute entropie), stocké haché, à usage unique
  et avec expiration ;
- vérification / consommation du jeton ;
- mise à jour du mot de passe utilisateur (en réutilisant le validateur CRYPT
  du champ, donc le même hachage que l'authentification) ;
- envoi de l'e-mail (HTML + texte) via le Mailer py4web.

Configuration (à placer dans settings.py de l'app — valeurs par défaut sûres
pour le dev) :

    # Dev : n'envoie pas réellement, journalise le lien dans la console
    RESET_DEBUG = True
    RESET_TOKEN_TTL_HOURS = 1
    RESET_USER_TABLE = "auth_user"

    # Prod : SMTP réel + RESET_DEBUG = False
    SMTP_SERVER = "smtp.exemple.ci:587"
    SMTP_SENDER = "DGMP <no-reply@dgmp.ci>"
    SMTP_LOGIN  = "utilisateur:motdepasse"   # ou None
    SMTP_TLS    = True
    SMTP_SSL    = False
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta

from pydal.validators import CRYPT

from ..common import db

try:
    # settings.py de l'APP (un cran au-dessus de controllers/). Y figurent les
    # paramètres SMTP — par défaut ceux de MailHog (localhost:1025, sans auth/TLS).
    from .. import settings as _settings
except Exception:                       # settings.py absent : on retombe sur les défauts
    _settings = None


def _cfg(name, default):
    return getattr(_settings, name, default)


# Par défaut on envoie réellement (via le SMTP configuré, MailHog en dev).
# Mettre RESET_DEBUG = True dans settings.py pour seulement journaliser le lien.
RESET_DEBUG = _cfg("RESET_DEBUG", False)
TOKEN_TTL_HOURS = _cfg("RESET_TOKEN_TTL_HOURS", 1)
USER_TABLE = _cfg("RESET_USER_TABLE", "auth_user")

# Ce module est dans controllers/ ; les gabarits d'e-mail (reset_email.html /
# reset_email.txt) sont dans <app>/templates/audits/. On remonte donc d'un cran
# au-dessus de controllers/ avant de pointer sur templates/audits.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(APP_DIR, "templates", "audits")


# --------------------------------------------------------------------------
#  Jetons
# --------------------------------------------------------------------------
def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(user_id):
    """Crée un jeton, invalide les précédents de l'utilisateur, renvoie le brut."""
    db(
        (db.password_reset_token.user_id == user_id)
        & (db.password_reset_token.used == False)  # noqa: E712
    ).update(used=True)

    raw = secrets.token_urlsafe(32)
    db.password_reset_token.insert(
        user_id=user_id,
        token_hash=_hash(raw),
        created_on=datetime.utcnow(),
        expires_on=datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS),
        used=False,
    )
    db.commit()
    return raw


def get_valid_token(raw):
    """Renvoie la ligne du jeton si valide (existe, non utilisé, non expiré), sinon None."""
    if not raw:
        return None
    return db(
        (db.password_reset_token.token_hash == _hash(raw))
        & (db.password_reset_token.used == False)  # noqa: E712
        & (db.password_reset_token.expires_on > datetime.utcnow())
    ).select().first()


def consume_token(row):
    """Marque le jeton comme utilisé (usage unique)."""
    row.update_record(used=True)
    db.commit()


# --------------------------------------------------------------------------
#  Utilisateur
# --------------------------------------------------------------------------
def find_user_by_email(email):
    table = db[USER_TABLE]
    return db(table.email == email).select().first()


def set_user_password(user, new_password):
    """Met à jour le mot de passe avec le MÊME hachage CRYPT que l'authentification.

    On hache explicitement via CRYPT : le champ `auth_user.password` n'a PAS de
    validateur CRYPT par défaut (ses `requires` = [IS_NOT_EMPTY, IS_LENGTH]), donc
    se fier à `field.requires` stockait le mot de passe EN CLAIR — et le login
    (`CRYPT()(pw)[0] == user.password`) ne le reconnaissait jamais."""
    hashed = str(CRYPT()(new_password)[0])
    user.update_record(password=hashed)
    db.commit()


# --------------------------------------------------------------------------
#  E-mail
# --------------------------------------------------------------------------
def _render(name, ctx):
    with open(os.path.join(TPL_DIR, name), encoding="utf-8") as f:
        raw = f.read()
    try:
        from yatl import render
        return render(raw, context=dict(ctx), delimiters="[[ ]]")
    except Exception:
        out = raw
        for k, v in ctx.items():
            out = out.replace("[[=%s]]" % k, str(v))
        return out


def _mailer():
    from py4web.utils.mailer import Mailer
    # Défauts = MailHog (le SMTP de dev) : localhost:1025, pas d'auth, pas de TLS/SSL.
    return Mailer(
        server=_cfg("SMTP_SERVER", "localhost:1025"),
        sender=_cfg("SMTP_SENDER", "noreply@monapp.ci"),
        login=_cfg("SMTP_LOGIN", None),
        tls=_cfg("SMTP_TLS", False),
        ssl=_cfg("SMTP_SSL", False),
    )


def send_reset_email(to_email, user_name, link):
    if RESET_DEBUG:
        # Dev : on n'envoie pas, on journalise le lien pour pouvoir le tester.
        print("\n" + "=" * 70)
        print("[RESET] (mode DEBUG, aucun e-mail envoyé)")
        print("[RESET] destinataire :", to_email)
        print("[RESET] lien         :", link)
        print("=" * 70 + "\n")
        return True

    ctx = dict(user_name=user_name, link=link, ttl_hours=TOKEN_TTL_HOURS)
    html = _render("reset_email.html", ctx)
    text = _render("reset_email.txt", ctx)
    subject = "Réinitialisation de votre mot de passe — AUDIT a posteriori"
    try:
        return _mailer().send(to=to_email, subject=subject, body=[text, html])
    except Exception as e:
        print("[RESET] échec de l'envoi e-mail :", e)
        return False
