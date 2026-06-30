"""
This module sets up core fixtures and utilities for a py4web application, including:

- Logging: Configures a custom logger using application settings.
- Database: Connects to the database using settings from the configuration.
- Caching: Instantiates a cache object for use throughout the app.
- Translation: Sets up the translation object for internationalization.
- Session Management: Selects and configures the session backend (cookies, Redis, Memcache, or database) based on settings.
- Authentication: Initializes the Auth object, configures its parameters, and defines authentication tables and actions.
- Email: Configures the email sender for authentication-related emails if SMTP settings are provided.
- User Groups: Sets up tagging for user groups if the authentication database is available.
- Auth Plugins: Optionally registers authentication plugins (PAM, LDAP, OAuth2 for Google, GitHub, Facebook, Okta) based on settings.
- File Download: Defines an action for downloading uploaded files if an upload folder is specified.
- Scheduler: Optionally starts a background scheduler for running tasks if enabled in settings.
- Decorators: Provides convenience action factories for authenticated and unauthenticated routes.

This file is intended to be a foundational part of the application and typically does not require modification.
"""

import os
import sys

from pydal.tools.scheduler import Scheduler
from pydal.tools.tags import Tags

from py4web import URL, DAL, Cache, Field, Flash, Session, Translator, action,redirect
from py4web.server_adapters.logging_utils import make_logger
from py4web.utils.auth import Auth
from py4web.utils.downloader import downloader
from py4web.utils.factories import ActionFactory
from py4web.utils.mailer import Mailer

from pydal.validators import IS_MATCH, IS_NOT_EMPTY, IS_LENGTH, IS_NOT_IN_DB

from . import settings
from .utils.emails import AppMailer  

from datetime import datetime, timezone

# #######################################################
# implement custom loggers form settings.LOGGERS
# #######################################################
logger = make_logger("py4web:" + settings.APP_NAME, settings.LOGGERS)

# #######################################################
# connect to db
# #######################################################
db = DAL(
    settings.DB_URI,
    folder=settings.DB_FOLDER,
    pool_size=settings.DB_POOL_SIZE,
    migrate=settings.DB_MIGRATE,
    fake_migrate=settings.DB_FAKE_MIGRATE,
)

# #######################################################
# define global objects that may or may not be used by the actions
# #######################################################
cache = Cache(size=1000)
T = Translator(settings.T_FOLDER)

# #######################################################
# pick the session type that suits you best
# #######################################################
if settings.SESSION_TYPE == "cookies":
    session = Session(secret=settings.SESSION_SECRET_KEY)

elif settings.SESSION_TYPE == "redis":
    import redis  # type: ignore[reportMissingImports]

    host, port = settings.REDIS_SERVER.split(":")
    # for more options: https://github.com/andymccurdy/redis-py/blob/master/redis/client.py
    conn = redis.Redis(host=host, port=int(port))
    conn.set = lambda k, v, e, cs=conn.set, ct=conn.ttl: (
        cs(k, v, ct(k)) if ct(k) >= 0 else cs(k, v, e)
    )
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)

elif settings.SESSION_TYPE == "memcache":
    import time

    import memcache  # type: ignore[reportMissingImports]

    conn = memcache.Client(settings.MEMCACHE_CLIENTS, debug=0)
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)

elif settings.SESSION_TYPE == "database":
    from py4web.utils.dbstore import DBStore

    session = Session(secret=settings.SESSION_SECRET_KEY, storage=DBStore(db))

# #######################################################
# Instantiate the object and actions that handle auth
# #######################################################

extra_fields = [
    Field(
        'created_at',
        'datetime',
        default  = lambda: datetime.now(timezone.utc),  # ← auto à l'insertion
        update   = None,                        # ← jamais mis à jour
        writable = False,
        readable = True,
    ),
    Field(
        'token_created_on',
        'datetime',
        readable = False,
        writable = False,
        default  = None,
    ),
    Field(
        'is_active',
        'boolean',
        readable = True,
        writable = True,
        default  = False,
    ),
    Field(
        'is_deleted',
        'boolean',
        readable = False,
        writable = True,
        default  = False,
    ),
]


auth = Auth(
    session, 
    db, 
    extra_fields=extra_fields,
    use_phone_number            = True,   # ← active phone_number natif
    block_previous_password_num = 3,      # ← active past_passwords_hash
    allowed_actions = [        # ← ici, pas dans enable()
        'config',
        'two_factor',
        'profile',
        'change_password',
    ]
)
auth.use_username = True
auth.param.registration_requires_confirmation = settings.VERIFY_EMAIL
auth.param.registration_requires_approval = settings.REQUIRES_APPROVAL
auth.param.login_after_registration = settings.LOGIN_AFTER_REGISTRATION
auth.param.allowed_actions = settings.ALLOWED_ACTIONS
auth.param.login_expiration_time = 3600
auth.param.password_complexity = {"entropy": settings.PASSWORD_ENTROPY}
auth.param.block_previous_password_num = 3
auth.param.default_login_enabled = settings.DEFAULT_LOGIN_ENABLED
auth.define_tables()
auth.fix_actions()
auth.logger = logger

flash = auth.flash

# S'applique à toute opération sur la table db.auth_user
db.auth_user.first_name.requires = None
db.auth_user.last_name.requires = None

db.auth_user.phone_number.requires = [
    IS_NOT_EMPTY(error_message="Le numéro de téléphone est requis"),
    # Autorise le '+' optionnel suivi de 8 à 15 chiffres
    IS_MATCH(r'^\+?\d{8,15}$', error_message="Format international invalide (ex: +225...)"),
    IS_NOT_IN_DB(db, 'auth_user.phone_number', error_message="Ce numéro est déjà utilisé")
]

db.auth_user.email.requires = [
    IS_NOT_EMPTY(error_message="Email requis"),
    IS_NOT_IN_DB(db, 'auth_user.email', error_message="Cet email est déjà utilisé")
]

db.auth_user.username.requires = [
    IS_NOT_EMPTY(error_message="Username requis"),
    IS_NOT_IN_DB(db, 'auth_user.username', error_message="Cet email est déjà utilisé")
]

db.auth_user.password.requires = [
    IS_NOT_EMPTY(error_message="Mot de passe requis"),
    IS_LENGTH(minsize=8, error_message="Le mot de passe doit contenir au moins 8 caractères")
]

# S'applique sur le rendu du formulaire db.auth_user
db.auth_user.first_name.label   = T('Prénom')
db.auth_user.last_name.label    = T('Nom')
db.auth_user.email.label        = T('Adresse e-mail')
db.auth_user.username.label     = T('Identifiant')
db.auth_user.password.label     = T('Mot de passe')
db.auth_user.phone_number.label    = T('N° de téléphone')

db.auth_user.email.comment      = T("Utilisé pour la connexion et le cas d'oubli de mot de passe")
db.auth_user.username.comment   = T('4 à 20 caractères, sans espace')
db.auth_user.password.comment   = T('8 caractères au minimun')
db.auth_user.phone_number.comment  = T("Avec indicatif pays ex: +225. Utilisé pour la connexion et le cas d'oubli de mot de passe")


# #######################################################
# Create a table to tag users as group members
# #######################################################
if auth.db:
    groups = Tags(db.auth_user, "groups") # rôles des utilisateurs
    permissions = Tags(db.auth_user, "permissions") # permissions des utilisateurs



# #######################################################
# Configure email sender for auth
# #######################################################
if settings.SMTP_SERVER:
    auth.sender = Mailer(
        server=settings.SMTP_SERVER,
        sender=settings.SMTP_SENDER,
        login=settings.SMTP_LOGIN,
        tls=settings.SMTP_TLS,
        ssl=settings.SMTP_SSL,
    )

# #######################################################
# Enable optional auth plugin
# #######################################################
if settings.USE_PAM:
    from py4web.utils.auth_plugins.pam_plugin import PamPlugin

    auth.register_plugin(PamPlugin())

if settings.USE_LDAP:
    from py4web.utils.auth_plugins.ldap_plugin import LDAPPlugin

    auth.register_plugin(LDAPPlugin(db=db, groups=groups, **settings.LDAP_SETTINGS))

if settings.OAUTH2GOOGLE_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2google import OAuth2Google  # TESTED

    auth.register_plugin(
        OAuth2Google(
            client_id=settings.OAUTH2GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH2GOOGLE_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2google/callback",
        )
    )

if settings.OAUTH2GOOGLE_SCOPED_CREDENTIALS_FILE:
    from py4web.utils.auth_plugins.oauth2google_scoped import (
        OAuth2GoogleScoped,
    )  # TESTED

    auth.register_plugin(
        OAuth2GoogleScoped(
            secrets_file=settings.OAUTH2GOOGLE_SCOPED_CREDENTIALS_FILE,
            scopes=[],  # Put here any scopes you want in addition to login
            db=db,  # Needed to store credentials in auth_credentials
        )
    )

if settings.OAUTH2GITHUB_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2github import OAuth2Github  # TESTED

    auth.register_plugin(
        OAuth2Github(
            client_id=settings.OAUTH2GITHUB_CLIENT_ID,
            client_secret=settings.OAUTH2GITHUB_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2github/callback",
        )
    )

if settings.OAUTH2FACEBOOK_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2facebook import OAuth2Facebook  # UNTESTED

    auth.register_plugin(
        OAuth2Facebook(
            client_id=settings.OAUTH2FACEBOOK_CLIENT_ID,
            client_secret=settings.OAUTH2FACEBOOK_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2facebook/callback",
        )
    )

if settings.OAUTH2OKTA_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2okta import OAuth2Okta  # TESTED

    auth.register_plugin(
        OAuth2Okta(
            client_id=settings.OAUTH2OKTA_CLIENT_ID,
            client_secret=settings.OAUTH2OKTA_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2okta/callback",
        )
    )

# #######################################################
# Enable optional API token plugins
# #######################################################

# curl -H "Authorization: Bearer {token}"
# create tokens in db.auth_simple_token
#
# simple_token_plugin = SimpleTokenPlugin(auth)
# auth.token_plugins.append(simple_token_plugin)

# curl -H "Authorization: Bearer {token}"
# create tokens with JwtTokenPlugin(auth).make(user, expiration)
#
# jwt_token_plugin = JwtTokenPlugin(auth)
# auth.token_plugins.append(jwt_token_plugin)

# #######################################################
# Define a convenience action to allow users to download
# files uploaded and reference by Field(type='upload')
# #######################################################
if settings.UPLOAD_FOLDER:

    @action("download/<filename>")
    @action.uses(db)
    def download(filename):
        return downloader(db, settings.UPLOAD_FOLDER, filename)

    # To take advantage of this in Form(s)
    # for every field of type upload you MUST specify:
    #
    # field.upload_path = settings.UPLOAD_FOLDER
    # field.download_url = lambda filename: URL('download/%s' % filename)

# #######################################################
# Define and optionally start the scheduler
# #######################################################
if settings.USE_SCHEDULER:
    scheduler = Scheduler(
        db, logger=logger, max_concurrent_runs=settings.SCHEDULER_MAX_CONCURRENT_RUNS
    )
    scheduler.start()
else:
    scheduler = None

# #######################################################
# Enable authentication
# #######################################################
auth.enable(uses=(session, T, db), env=dict(T=T))

# #######################################################
# Define convenience decorators
# They can be used instead of @action and @action.uses
# They should NEVER BE MIXED with @action and @action.uses
# If you need to provide extra fixtures for a specific controller
# add them like this: @authenticated(uses=[extra_fixture])
# #######################################################
unauthenticated = ActionFactory(db, session, T, flash, auth)
authenticated = ActionFactory(db, session, T, flash, auth.user)


# #########################################################
# Custom class for sending email by auth
# #########################################################

# ── Mailer
auth.sender = AppMailer(settings)

# ── Surcharge auth.send()
def custom_send(name, user, **attrs):
    """
    Intercepte tous les envois auth et custom.

    Emails gérés :
      verify_email         → confirmation inscription  (auth.register)
      welcome              → bienvenue                 (verify_email action)
      reset_password       → lien reset                (auth.request_reset_password)
      reset_password_success → confirmation modif mdp  (custom_reset_password action)
      unsubscribe          → désinscription RGPD        (auth.gdpr_unsubscribe)
    """
    
    SUBJECTS = {
        'reset_password': "Réinitialisation de votre mot de passe",
        'reset_password_success' : "Votre mot de passe a été modifié",   # ← nouveau
        'verify_email'  : "Confirmez votre adresse email",
        'welcome'       : "Bienvenue sur MonApplication",
        'unsubscribe'   : "Désinscription confirmée",
    }

    # ── Normaliser user → dict (Row pydal ou dict)
    # if hasattr(user, 'as_dict'):
    #     user = user.as_dict()

    auth.sender.send(
        to      = user['email'],
        subject = SUBJECTS.get(name, "Notification"),
        body    = {
            'name' : name,
            'user' : user,
            'link' : attrs.get('link', ''),
        },
    )

auth.send = custom_send