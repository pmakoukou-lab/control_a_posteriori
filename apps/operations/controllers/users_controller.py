from py4web import URL, abort, action, redirect, request, HTTP
from yatl.helpers import A
from py4web.utils.form import Form
from pydal.validators import CRYPT
from py4web import Field

from ..forms.user_forms import validate_register_form, login_form, request_reset_password_form, reset_password_form
from ..utils.token import is_token_expired, mark_token_created, clear_token
from .. import settings
from ..common import (
    T,
    auth,
    authenticated,
    cache,
    db,
    flash,
    logger,
    session,
    unauthenticated,
    groups
)

# ═══════════════════════════════════════════════════════════════
# REGISTER FLOW
# ═══════════════════════════════════════════════════════════════

@action('user/custom_register', method=['GET', 'POST'], name='operations_custom_register')
@action.uses('auth/inscription.html', db, session, auth, flash)
def custom_register():
    db.auth_user.password.writable = True
    db.auth_user.password.readable = True

    fields = ['first_name', 'last_name', 'email', 'password', 'phone_number']

    form = Form(
        db.auth_user,
        fields=fields,
        validation=validate_register_form,
        csrf_session=session,
        dbio=False
    )

    if form.accepted:
        db.auth_user.password.requires = CRYPT()
        user = auth.register(
            {
                'username'   : form.vars.get('username', '').strip(),
                'first_name' : form.vars.get('first_name', '').strip(),
                'last_name'  : form.vars.get('last_name', '').strip(),
                'email'      : form.vars.get('email', '').strip().lower(),
                'password'   : form.vars.get('password', ''),
                'phone_number'  : form.vars.get('phone_number', '').strip(),
            },
            send=True,
            route='user'
        )

        if user.get('id'):
            groups.add(user['id'], 'client')   # Assigner le rôle client ← ici, res['id'] est l'id du nouvel user

            mark_token_created(db, user['id'])
            flash.set('Inscription réussie ! Vérifiez votre boîte mail.')
            auth.session['_success_action'] = 'register'
            redirect(URL('success'))
        else:
            flash.set("Erreur lors de l'inscription.")
            logger.error(f"auth.register errors : {user.get('errors')}")

    return dict(form=form)


@action('user/verify_email', method=['GET'])
@action.uses(db, session, flash, auth)
def verify_email():
    token = request.query.get('token')

    if not token:
        raise HTTP(404)

    query = auth._query_from_token(token)
    user  = db(query).select().first()
    if not user:
        flash.set('Lien invalide ou expiré.')
        redirect(URL('custom_register'))

    if is_token_expired(user.token_created_on, settings.TOKEN_EXPIRY_VERIFY_EMAIL):
        user.delete_record()
        db.commit()
        flash.set('Ce lien a expiré. Veuillez vous inscrire à nouveau.')
        redirect(URL('custom_register'))

    # ── Token valide : activer le compte
    auth.verify_email(token)
    clear_token(db, user.id)

    # ── Activer le compte
    db(db.auth_user.id == user.id).update(is_actif=True)
    db.commit()

    # ── Email de bienvenue
    auth.send('welcome', user.as_dict())

    flash.set('Email confirmé ! Bienvenue sur MonApplication.')
    redirect(URL('custom_login'))


# ═══════════════════════════════════════════════════════════════
# SUCCES PAGE
# ═══════════════════════════════════════════════════════════════
@action('user/success', method=['GET'])
@action.uses('auth/success.html', session, flash)
def success_page():
    success_action = session.get('_success_action')
    session['_success_action'] = None

    # Accès direct sans action → rediriger
    if not success_action:
        redirect(URL('index'))

    CONTENT = {
        'request_reset_password': {
            'title'     : 'Vérifiez votre boîte mail',
            'message'   : 'Un lien de réinitialisation a été envoyé. '
                          'Il expirera dans 1 heure.',
            'icon'      : '📧',
            'back_url'  : URL('auth/login'),
            'back_label': 'Retour à la connexion',
        },
        'register': {
            'title'     : 'Presque fini !',
            'message'   : "Un email de confirmation vient d'être envoyé. "
                          "Veuillez cliquer sur le lien pour activer votre compte.",
            'icon'      : '✅',
            'back_url'  : URL('index'),
            'back_label': "Retour à l'accueil",
        },
    }

    context = CONTENT.get(success_action, {
        'title'     : 'Opération réussie',
        'message'   : 'Votre demande a bien été prise en compte.',
        'icon'      : '✔️',
        'back_url'  : URL('index'),
        'back_label': "Retour à l'accueil",
    })

    return dict(**context)

 
# ═══════════════════════════════════════════════════════════════
# LOGIN FLOW
# ═══════════════════════════════════════════════════════════════
@action('user/custom_login', method=['GET', 'POST'], name='operations_custom_login')
@action.uses('auth/login.html', db, session, auth)
def custom_login():
    if auth.is_logged_in:
        redirect(URL('index'))
    
    form = login_form(db, session)

    if form.accepted:
        login_input = form.vars.get('email_or_username', '').strip().lower()

        # ── Recherche par email OU par username ──────────────────────
        user = (
            db(db.auth_user.email == login_input).select().first()
            or
            db(db.auth_user.username == login_input).select().first()
        )

        # ── Vérifier que le compte est actif ────────────────────────
        if user and not user.is_actif:
            flash.set("Votre compte n'est pas encore activé. "
                      "Vérifiez votre boîte mail.")
            redirect(URL('custom_login'))

        identifier = form.vars.get('login_identifier', '').strip()
        password   = request.forms.get('password', '')

        user, error = auth.login(identifier, password)

        if user:
            auth.store_user_in_session(user['id'])
            redirect(URL('index'))
        else:
            form.errors['_error'] = error

    return dict(form=form)


# ═══════════════════════════════════════════════════════════════
# RESET PASSWORD FLOW
# ═══════════════════════════════════════════════════════════════

@action('user/custom_request_reset_password', method=['GET', 'POST'])
@action.uses('auth/request_reset_password.html', db, session, flash, auth)
def custom_request_reset_password():
    if auth.is_logged_in:
        redirect(URL('index'))

    form = request_reset_password_form(db, session)

    if form.accepted:
        email = form.vars['email'].strip().lower()
        token = auth.request_reset_password(
                                            email,
                                            send=True,
                                            route='user',
                                        )

        if not token:
            form.errors['email'] = "Aucun compte associé à cette adresse."
            form.accepted = False
        else:
            user = db(db.auth_user.email == email).select(
                db.auth_user.id
            ).first()
            mark_token_created(db, user.id)
            flash.set('Un lien de réinitialisation a été envoyé à votre adresse email.')
            auth.session['_success_action'] = 'request_reset_password'
            redirect(URL('success'))

    return dict(form=form)


@action('user/reset_password', method=['GET'])
@action.uses(db, session, flash, auth)
def verify_reset_password_token():
    token = request.query.get('token')

    # ── Token absent
    if not token:
        raise HTTP(404)

    # ── Token inexistant en base
    query = auth._query_from_token(token)
    user  = db(query).select().first()
    if not user:
        flash.set('Lien invalide ou expiré.')
        redirect(URL('custom_request_reset_password'))

    # ── Token expiré
    if is_token_expired(user.token_created_on, settings.TOKEN_EXPIRY_RESET_PASSWORD):
        clear_token(db, user.id)
        flash.set('Ce lien a expiré. Veuillez faire une nouvelle demande.')
        redirect(URL('custom_request_reset_password'))

    # ── Token valide : rediriger vers le formulaire
    redirect(URL('custom_reset_password', vars=dict(token=token)))


@action('user/custom_reset_password', method=['GET', 'POST'])
@action.uses('auth/reset_password.html', db, session, flash, auth)
def custom_reset_password():
    token = request.query.get('token')

    if not token:
        raise HTTP(404)

    # ── Vérifier que le token existe encore (POST peut arriver sans redirect)
    query = auth._query_from_token(token)
    user  = db(query).select().first()
    if not user:
        flash.set('Lien invalide ou expiré.')
        redirect(URL('custom_request_reset_password'))

    form = reset_password_form(session)

    if form.accepted:
        db.auth_user.password.requires = CRYPT()
        new_password  = form.vars.get('new_password', '')
        new_password2 = form.vars.get('new_password2', '')

        res = auth.reset_password(token, new_password, new_password2)

        if res.get('errors'):
            # ← erreurs de validation remontées par auth.reset_password()
            form.errors.update(res['errors'])
            form.accepted = False
        else:
            clear_token(db, user.id)
            auth.send('reset_password_success', user.as_dict())
            flash.set('Mot de passe modifié avec succès.')
            redirect(URL('custom_login'))

    return dict(form=form, token=token)