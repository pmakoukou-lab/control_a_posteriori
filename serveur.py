# serveur.py
import os
from py4web.core import wsgi
from waitress import serve

BASE = os.path.abspath(os.path.dirname(__file__))

# L'objet WSGI exposé par py4web.
# wsgi() accepte les mêmes arguments que la commande `py4web run`.
application = wsgi(
    apps_folder=os.path.join(BASE, "apps"),
    password_file=os.path.join(BASE, "password.txt"),
    dashboard_mode="none",   # "none" ou "readonly" en prod, jamais "full"
)

if __name__ == "__main__":
    serve(
        application,
        host="127.0.0.1",
        port=8000,
        threads=8,
        # nginx fait la terminaison TLS : on lui fait confiance pour le scheme
        # url_scheme="https",        # à retirer si tu restes en HTTP
    )