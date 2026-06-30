# -*- coding: utf-8 -*-
"""
Contrôleur PROPRE au mode GAG — Gré à Gré.

Déclare ses propres actions (ajout, détails, modification, suppression, export
Excel) sous le préfixe d'URL ``gag/…`` et ses propres gabarits
(templates/audits/gag/…). Orchestration déléguée à l'engine ``audit_controler``.
Modèle : models/audits/model_gag.py.

NB : la grille GAG n'a pas de section « Numéro de l'opération » → pas de champ
``n_bomp`` (lu de façon défensive par l'engine ; numéro dérivé de la date + id).
"""
from py4web import action, request, redirect, URL

from .. import models as _models  # noqa: F401  (force le chargement des tables)
from ..common import db, session, auth
from ..fixtures.rbac_fixture import access
from . import audit_controler as E


MODE = 'GAG'
SLUG = 'gag'

E.register_mode(MODE, E.build_mode_config(
    db.gag_operations,
    db.gag_allotissements,
    label="Gré à gré",
    pill='modepill mode-gag',
    field_rows=[],
    grille_export={'file': '3-saisie_GAG_nv.xlsx', 'sheet': 'Nouvelle grille', 'start_row': 7},
))


# --- Ajout -----------------------------------------------------------------
@action('gag/operation/add', method=['GET'])
@action.uses('audits/gag/ajout.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def gag_add_form():
    return E.form_context(MODE)


@action('gag/operation/add', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def gag_add():
    E.create_operation(MODE, request.forms)
    if request.forms.get('save_again'):
        redirect(URL(SLUG, 'operation', 'add', vars=dict(msg='op_added')))
    redirect(URL('collecte', vars=dict(msg='op_added')))


# --- Modification ----------------------------------------------------------
@action('gag/operation/<oid:int>/edit', method=['GET'])
@action.uses('audits/gag/modification.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def gag_edit_form(oid):
    ctx = E.form_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


@action('gag/operation/<oid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def gag_edit(oid):
    if not E.update_operation(MODE, oid, request.forms):
        redirect(URL('collecte', vars=dict(msg='not_found')))
    redirect(URL('collecte', vars=dict(msg='op_updated')))


# --- Suppression -----------------------------------------------------------
@action('gag/operation/<oid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def gag_delete(oid):
    E.soft_delete_operation(MODE, oid)
    redirect(URL('collecte', vars=dict(msg='op_deleted')))


# --- Détails ---------------------------------------------------------------
@action('gag/details/<oid:int>', method=['GET'])
@action.uses('audits/gag/details.html', db, session, auth, access)
def gag_details(oid):
    ctx = E.details_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


# --- Export Excel ----------------------------------------------------------
@action('gag/export', method=['GET'])
@action.uses(db, session, auth, access)
def gag_export():
    data = E.export_xlsx(MODE)
    if data is None:
        redirect(URL('collecte', vars=dict(msg='export_na')))
    return data
