# -*- coding: utf-8 -*-
"""
Point d'entrée de l'app py4web « operations ».

py4web ne CHARGE une app que si ce fichier existe (cf. Reloader.import_app :
``... and os.path.exists(init)``). Sans lui, aucun contrôleur n'est importé donc
AUCUNE route @action n'est enregistrée (404 partout).

Ordre d'import :
  1) common   → fixtures partagées (db, auth, session…), exposées au niveau de
                l'app (utile au /dbadmin et à l'API REST de py4web).
  2) models   → définit toutes les tables sur `db` (le référentiel AVANT le métier).
  3) controllers → importe chaque contrôleur ⇒ exécute les @action ⇒ routes.
"""
from .common import *        # noqa: F401,F403
from . import models         # noqa: F401  (définit les tables)
from . import controllers    # noqa: F401  (enregistre les routes @action)
