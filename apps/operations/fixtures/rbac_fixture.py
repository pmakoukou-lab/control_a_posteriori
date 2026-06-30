# -*- coding: utf-8 -*-
"""
Contrôle d'accès RBAC — basé EXCLUSIVEMENT sur les Tags py4web.

Les rôles et permissions sont des Tags portés sur ``auth_user`` (cf. common.py :
``groups = Tags(db.auth_user, "groups")`` et ``permissions = Tags(db.auth_user,
"permissions")``). Aucune table de rôles « maison » n'intervient dans la décision
d'accès.

Usage (factory) — à placer EN DERNIER dans ``action.uses`` pour que l'instance
configurée s'injecte dans le contexte du template (``output["access"]``) AVANT le
rendu (les ``on_success`` sont déroulés en ordre inverse) ::

    @action.uses('audits/collecte.html', db, session, auth, access)                       # connecté lit (injecte access)
    @action.uses('audits/administration.html', db, session, auth, access(roles="Administrateur"))  # admin écrit

Logique de garde (« admin écrit / connecté lit ») : toute route portant le fixture
exige d'être authentifié (anonyme → redirection login) ; si des rôles/permissions
sont requis, il faut « au moins un des rôles requis ET au moins une des permissions
requises », sinon HTTP 403.
"""
import threading

from py4web import redirect, URL, HTTP
from py4web.core import Fixture

from ..common import (
    auth,
    groups,
    permissions,
)


class AccessControl(Fixture):
    # État par requête : les Tags de l'utilisateur courant sont chargés dans un
    # thread-local (les Fixtures py4web sont des singletons partagés entre requêtes).
    _tl = threading.local()

    def __init__(self, roles=None, perms=None):
        self.dict_name = "access"
        self.required_roles = [roles] if isinstance(roles, str) else list(roles or [])
        self.required_perms = [perms] if isinstance(perms, str) else list(perms or [])

    # -- rôles / permissions de la requête courante (thread-local) --------------
    @property
    def user_roles(self):
        return getattr(AccessControl._tl, "roles", [])

    @property
    def user_perms(self):
        return getattr(AccessControl._tl, "perms", [])

    # -- cycle de vie Fixture ---------------------------------------------------
    def on_request(self, context):
        """Charge rôles/permissions de l'utilisateur courant puis applique la garde."""
        user_id = auth.user_id
        AccessControl._tl.roles = list(groups.get(user_id) or []) if user_id else []
        AccessControl._tl.perms = list(permissions.get(user_id) or []) if user_id else []

        # « Connecté lit » : toute route portant ce fixture exige au minimum d'être
        # authentifié (l'anonyme est renvoyé vers le login). Les rôles/permissions
        # ajoutent la couche « admin écrit » par-dessus.
        if not user_id:
            redirect(URL("login"))

        if self.required_roles or self.required_perms:
            role_ok = (any(r in self.user_roles for r in self.required_roles)
                       if self.required_roles else True)
            perm_ok = (any(p in self.user_perms for p in self.required_perms)
                       if self.required_perms else True)
            if not (role_ok and perm_ok):
                raise HTTP(403)

    def on_success(self, context):
        """Injecte l'instance (qui a chargé les rôles de CETTE requête) dans le template."""
        output = context.get("output")
        if isinstance(output, dict):
            output[self.dict_name] = self

    # -- API templates / contrôleurs -------------------------------------------
    def has_role(self, *roles):
        return any(r in self.user_roles for r in roles)

    def has_permission(self, *perms):
        return any(p in self.user_perms for p in perms)

    # -- factory : access(roles=..., perms=...) -> instance configurée ----------
    def __call__(self, roles=None, perms=None):
        return AccessControl(roles=roles, perms=perms)


# Instance prête à l'emploi : utilisable telle quelle (lecture, injecte access) ou
# comme factory (access(roles="Administrateur")).
access = AccessControl()
