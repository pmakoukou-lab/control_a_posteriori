# -*- coding: utf-8 -*-
"""
Contrôleur PROPRE au mode AOR_PI — Appel d'Offres Restreint, prestations
intellectuelles.

Déclare ses propres actions (ajout, détails, modification, suppression, export
Excel) sous le préfixe d'URL ``aor_pi/…`` et ses propres gabarits
(templates/audits/aor_pi/…). Orchestration déléguée aux helpers de l'engine
``audit_controler``. Modèle : models/audits/model_aor_pi.py.
"""
from py4web import action, request, redirect, URL

from .. import models as _models  # noqa: F401  (force le chargement des tables)
from ..common import db, session, auth
from ..fixtures.rbac_fixture import access
from . import audit_controler as E


MODE = 'AOR_PI'
SLUG = 'aor_pi'

E.register_mode(MODE, E.build_mode_config(
    db.aor_pi_operations,
    db.aor_pi_allotissements,
    label="Appel d'offres restreint — prestations intellectuelles",
    pill='modepill mode-aor',
    field_rows=[],
    grille_export={'file': '2- Saisie_AOR nv prestations intellectuelles.xlsx',
                   'sheet': 'Nouvelle grille', 'start_row': 7},
))


# --- Ajout -----------------------------------------------------------------
@action('aor_pi/operation/add', method=['GET'])
@action.uses('audits/aor_pi/ajout.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aor_pi_add_form():
    return E.form_context(MODE)


@action('aor_pi/operation/add', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aor_pi_add():
    E.create_operation(MODE, request.forms)
    if request.forms.get('save_again'):
        redirect(URL(SLUG, 'operation', 'add', vars=dict(msg='op_added')))
    redirect(URL('collecte', vars=dict(msg='op_added')))


# --- Modification ----------------------------------------------------------
@action('aor_pi/operation/<oid:int>/edit', method=['GET'])
@action.uses('audits/aor_pi/modification.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aor_pi_edit_form(oid):
    ctx = E.form_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


@action('aor_pi/operation/<oid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aor_pi_edit(oid):
    if not E.update_operation(MODE, oid, request.forms):
        redirect(URL('collecte', vars=dict(msg='not_found')))
    redirect(URL('collecte', vars=dict(msg='op_updated')))


# --- Suppression -----------------------------------------------------------
@action('aor_pi/operation/<oid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aor_pi_delete(oid):
    E.soft_delete_operation(MODE, oid)
    redirect(URL('collecte', vars=dict(msg='op_deleted')))


# --- Détails ---------------------------------------------------------------
@action('aor_pi/details/<oid:int>', method=['GET'])
@action.uses('audits/aor_pi/details.html', db, session, auth, access)
def aor_pi_details(oid):
    ctx = E.details_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


# --- Export Excel ----------------------------------------------------------
@action('aor_pi/export', method=['GET'])
@action.uses(db, session, auth, access)
def aor_pi_export():
    data = E.export_xlsx(MODE)
    if data is None:
        redirect(URL('collecte', vars=dict(msg='export_na')))
    return data
