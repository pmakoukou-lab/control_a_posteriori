import logging
import sys
from .. import settings
from ..common import db
from py4web import request

from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_EMAIL, IS_LENGTH, IS_IN_DB, IS_EQUAL_TO, IS_STRONG
from pydal import Field

# Récupérer le logger de l'app
logger = logging.getLogger('apps.' + settings.APP_NAME)
logger.setLevel(logging.DEBUG)

# Vérifier qu'un handler console est bien attaché
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)  # ← stdout, pas stderr
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Empêcher la propagation qui peut bloquer l'affichage
logger.propagate = True  # True pour remonter au logger racine

def validate_register_form(form):
    """
    Appelé par Form() AVANT d'écrire en base.
    form.vars  → données soumises (dict)
    form.errors → dict d'erreurs à remplir pour bloquer
    """

    # Validation username
    username = (form.vars.get('username') or '').strip()
    if not username:
        form.errors['username'] = 'Le nom utilisateur est obligatoire'

    # Validation mot de passe et confirm mot de passe
    password  = form.vars.get('password', '')
    if not password:
        form.errors['password'] = 'Le mot de passe est obligatoire'

    password_confirm = request.forms.get('password_confirm', '')
    if password != password_confirm:
        form.errors['_error'] = 'Les mots de passe ne correspondent pas'
        logger.debug(f"Mot de passe - {password}")
        logger.debug(f"Confirm mot de passe - {password_confirm}")
        
    # Validation email
    email = (form.vars.get('email') or '').strip()
    if not email:
        form.errors['email'] = "L'email est obligatoire"
    elif db(db.auth_user.email == email).count():
        form.errors['email'] = 'Cet email est déjà enregistré'

    # Validation téléphone
    tel = (form.vars.get('phone_number') or '').replace(' ', '')
    if tel and not tel.startswith('+225'):
        form.errors['phone_number'] = 'Utilisez le format international +225...'

def validate_login_form(form):
    if not (form.vars.get('email') or '').strip():
        form.errors['email'] = 'Email obligatoire'
    if not form.vars.get('password'):
        form.errors['password'] = 'Mot de passe obligatoire'

def login_form(db, session):
    """
    Champ login_identifier : accepte email OU username.
    auth.login() fait la détection en interne via '@' + use_username.
    """
    fields = [
        Field(
            'login_identifier',
            'string',
            label='Identifiant',
            comment='nom d\'utilisateur ou adresse email',
            requires=[
                IS_NOT_EMPTY(error_message="L'identifiant est obligatoire."),
            ],
        ),
        Field(
            'password',
            'password',
            label='Mot de passe',
            requires=[
                IS_NOT_EMPTY(error_message="Le mot de passe est obligatoire."),
                IS_LENGTH(minsize=8, error_message="8 caractères minimum."),
            ],
            readable=False,
        ),
    ]

    return Form(
        fields,
        dbio=False,
        csrf_session=session,
    )

def request_reset_password_form(db, session):
    """
    Formulaire de demande de réinitialisation de mot de passe.
    Vérifie que l'email existe dans auth_user.
    """
    fields = [
        Field(
            'email',
            'email',
            label='Adresse email',
            comment='Entrez l\'email associé à votre compte',
            requires=[
                IS_NOT_EMPTY(error_message="L'adresse email est obligatoire."),
                IS_EMAIL(error_message="Adresse email invalide."),
            ],
        ),
    ]

    return Form(
        fields,
        dbio=False,
        csrf_session=session,
    )

def reset_password_form(session):
    """
    Formulaire de réinitialisation de mot de passe.
    """
    fields = [
        Field(
            'new_password',
            'password',
            label='Nouveau mot de passe',
            requires=[
                IS_NOT_EMPTY(
                    error_message='Le mot de passe est obligatoire.'
                ),
                IS_LENGTH(
                    minsize=8,
                    error_message='8 caractères minimun.'
                ),
            ],
            readable=False,
        ),
        Field(
            'new_password2',
            'password',
            label='Confirmer le mot de passe',
            requires=[
                IS_NOT_EMPTY(
                    error_message='La confirmation est obligatoire.'
                ),
            ],
            readable=False,
        ),
    ]

    def validate(form):
        """Vérifie la correspondance des mots de passe → erreur globale."""
        pwd  = request.forms.get('new_password', '')
        pwd2 = request.forms.get('new_password2', '')
        if pwd and pwd2 and pwd != pwd2:
            form.errors['_error'] = 'Les mots de passe ne correspondent pas.'
    
    return Form(
        fields,
        dbio=False,
        csrf_session=session,
        validation=validate,
        submit_value='Réinitialiser le mot de passe',
    )
