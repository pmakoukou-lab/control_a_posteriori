import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from yatl import render


class AppMailer:
    """
    Remplace auth.sender.
    Appelé via custom_send() dans common.py.
    body = dict contexte brut complet.
    """

    def __init__(self, settings):
        self.settings      = settings
        self.templates_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'templates',
            'emails'
        )

    def _read_template(self, file_name, **variables):
        file_path = os.path.join(self.templates_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if file_name.endswith('.txt'):
            return content.format(**variables)
        return render(
            content    = content,
            context    = variables,
            delimiters = ('[[', ']]'),
            filename   = file_path,
        )

    def _smtp_send(self, msg):
        host, port = self.settings.SMTP_SERVER.split(':')
        try:
            with smtplib.SMTP(host, int(port)) as srv:
                srv.ehlo()
                if self.settings.SMTP_TLS:
                    srv.starttls()
                if self.settings.SMTP_LOGIN:
                    login, pwd = self.settings.SMTP_LOGIN.split(':', 1)
                    srv.login(login, pwd)
                srv.send_message(msg)
            print(f"[MAIL] ✓ Envoyé à {msg['To']} — {msg['Subject']}")
            return True
        except Exception as e:
            print(f"[MAIL] ✗ Erreur SMTP : {e}")
            return False

    def _build_context(self, name, user, link):
        """
        Construit le contexte de variables disponibles dans les templates.
        Chaque type d'email peut avoir des variables supplémentaires.
        """
        from py4web import URL

        # ── Normaliser user : Row pydal ou dict → toujours dict
        # if hasattr(user, 'as_dict'):
        #     user = user.as_dict()   # ← Row pydal → dict

        # ── Variables communes à tous les emails
        context = dict(
            first_name = user.get('first_name', ''),
            last_name  = user.get('last_name', ''),
            email      = user.get('email', ''),
            link       = link,
        )

        # ── Variables spécifiques par type
        EXTRA = {
            'verify_email': {
                # lien déjà dans context['link']
            },
            'welcome': {
                'login_url': URL('custom_login', scheme=True),
            },
            'reset_password': {
                # lien déjà dans context['link']
            },
            'reset_password_success': {
                'login_url': URL('custom_login', scheme=True),
            },
            'unsubscribe': {},
        }

        context.update(EXTRA.get(name, {}))
        return context

    def send(self, to, subject, body, sender=None, **kwargs):
        if isinstance(to, list):
            to = to[0]
        to = str(to)

        # ── Extraire le contexte brut
        name = body.get('name', '')
        user = body.get('user', {})
        link = body.get('link', '')

        # ── Construire le contexte complet
        context = self._build_context(name, user, link)

        msg            = MIMEMultipart('alternative')
        msg['Subject'] = str(subject)
        msg['From']    = str(self.settings.SMTP_SENDER)
        msg['To']      = to

        # ── Partie texte
        try:
            txt = self._read_template(f'{name}.txt', **context)
        except Exception as e:
            print(f"[MAIL] ✗ Erreur template TXT {name}.txt : {e}")
            txt = f"Cliquez ici : {link}" if link else f"Bonjour {context['first_name']}"
        msg.attach(MIMEText(txt, 'plain', 'utf-8'))

        # ── Partie HTML
        try:
            html = self._read_template(f'{name}.html', **context)
            msg.attach(MIMEText(html, 'html', 'utf-8'))
        except Exception as e:
            print(f"[MAIL] ✗ Erreur template HTML {name}.html : {e}")

        return self._smtp_send(msg)