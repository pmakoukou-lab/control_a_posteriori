# from datetime import timedelta
# from py4web.core import utcnow


# # ── Délais configurables ──────────────────────────────────────
# TOKEN_EXPIRY = {
#     'reset_password' : 3600,   # 1 heure
#     'verify_email'   : 86400,  # 24 heures
# }


# def is_token_expired(token_created_on, token_type):
#     """
#     Vérifie si un token a expiré.

#     token_created_on : datetime stocké dans auth_user.token_created_on
#     token_type       : 'reset_password' | 'verify_email'

#     Retourne True si expiré, False si valide.
#     """
#     if not token_created_on:
#         return True

#     expiry_seconds = TOKEN_EXPIRY.get(token_type, 3600)
#     elapsed = utcnow() - token_created_on

#     return elapsed > timedelta(seconds=expiry_seconds)


# def mark_token_created(db, user_id):
#     """Stocke le timestamp de création du token."""
#     db(db.auth_user.id == user_id).update(
#         token_created_on=utcnow()
#     )
#     db.commit()


# def clear_token(db, user_id):
#     """Nettoie le token et le timestamp après utilisation."""
#     db(db.auth_user.id == user_id).update(
#         action_token     = None,
#         token_created_on = None,
#     )
#     db.commit()



from datetime import timedelta, datetime, timezone
from py4web.core import utcnow

def now_utc():
    """Aware UTC."""
    return datetime.now(timezone.utc)

def _make_aware(dt):
    """
    Convertit un datetime naive en aware UTC.
    SQLite + pydal retourne toujours du naive →
    on suppose que c'est UTC et on ajoute tzinfo.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)  # ← naive → aware UTC
    return dt


def is_token_expired(token_created_on, expiry_seconds):
    """
    Vérifie si un token a expiré.
    token_created_on : datetime stocké dans auth_user.token_created_on
    expiry_seconds   : délai en secondes depuis settings
    """
    if not token_created_on:
        return True
    # ── Normaliser token_created_on → aware UTC
    created = _make_aware(token_created_on)
    now     = now_utc()

    return (now - created) > timedelta(seconds=expiry_seconds)


def mark_token_created(db, user_id):
    """Stocke le timestamp de création du token."""
    db(db.auth_user.id == user_id).update(token_created_on=utcnow())
    db.commit()


def clear_token(db, user_id):
    """Nettoie le token et le timestamp après utilisation."""
    db(db.auth_user.id == user_id).update(
        action_token     = None,
        token_created_on = None,
    )
    db.commit()