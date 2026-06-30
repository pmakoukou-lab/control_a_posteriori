# -*- coding: utf-8 -*-
"""
Contrôleur PROPRE au mode AOO — Appel d'Offres Ouvert.

« Un mode = un modèle + un contrôleur + un allotissement » :
  - modèle      : models/audits/model_aoo.py  → aoo_operations / aoo_allotissements
  - gabarits    : templates/audits/aoo/ajout.html, modification.html, details.html
  - contrôleur  : CE fichier — il déclare SES PROPRES actions (ajout, détails,
                  modification, suppression, export Excel) sous le préfixe d'URL
                  ``aoo/…`` et délègue l'orchestration aux helpers de l'engine
                  (``audit_controler``). La page « Collecte » (mutualisée) liste
                  l'union des modes inscrits.
"""
from py4web import action, request, redirect, URL

from .. import models as _models  # noqa: F401  (force le chargement des tables)
from ..common import db, session, auth
from ..fixtures.rbac_fixture import access
from . import audit_controler as E


# Champs alignés sur une même ligne dans le formulaire (propre à la grille AOO).
AOO_FIELD_ROWS = [
    ('examen_validation_dao_dgmp_date_reception', 'examen_validation_dao_dgmp_date_validation'),
    ('garantie_offre_minimale', 'garantie_offre_maximale'),
    ('publication_aao_date', 'publication_aao_num'),
    ('publication_aao_duree', 'publication_aao_nb_report'),
    ('delai_impart_cojo_trvx_date_ouv', 'delai_impart_cojo_trvx_date_jug',
     'delai_impart_cojo_trvx_dern_recours'),
    ('delai_impart_cojo_trvx_nb_jug', 'delai_impart_cojo_trvx_respect_delai'),
    ('pub_resultat_trvx_cojo_date', 'pub_resultat_trvx_cojo_support_pub'),
    ('exam_prealable_approb_date_soumission', 'exam_prealable_approb_date_validation'),
]

MODE = 'AOO'
SLUG = 'aoo'

E.register_mode(MODE, E.build_mode_config(
    db.aoo_operations,
    db.aoo_allotissements,
    label="Appel d'offres ouvert",
    pill='modepill mode-aoo',
    field_rows=AOO_FIELD_ROWS,
    grille_export={'file': '1-Saisie_AOO_nv.xlsx', 'sheet': 'Nouv', 'start_row': 7},
))


# --- Ajout -----------------------------------------------------------------
@action('aoo/operation/add', method=['GET'])
@action.uses('audits/aoo/ajout.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aoo_add_form():
    return E.form_context(MODE)


@action('aoo/operation/add', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aoo_add():
    E.create_operation(MODE, request.forms)
    if request.forms.get('save_again'):
        redirect(URL(SLUG, 'operation', 'add', vars=dict(msg='op_added')))
    redirect(URL('collecte', vars=dict(msg='op_added')))


# --- Modification ----------------------------------------------------------
@action('aoo/operation/<oid:int>/edit', method=['GET'])
@action.uses('audits/aoo/modification.html', db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aoo_edit_form(oid):
    ctx = E.form_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


@action('aoo/operation/<oid:int>/edit', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aoo_edit(oid):
    if not E.update_operation(MODE, oid, request.forms):
        redirect(URL('collecte', vars=dict(msg='not_found')))
    redirect(URL('collecte', vars=dict(msg='op_updated')))


# --- Suppression -----------------------------------------------------------
@action('aoo/operation/<oid:int>/delete', method=['POST'])
@action.uses(db, session, auth, access(roles=['Administrateur', 'contrôleur']))
def aoo_delete(oid):
    E.soft_delete_operation(MODE, oid)
    redirect(URL('collecte', vars=dict(msg='op_deleted')))


# --- Détails ---------------------------------------------------------------
@action('aoo/details/<oid:int>', method=['GET'])
@action.uses('audits/aoo/details.html', db, session, auth, access)
def aoo_details(oid):
    ctx = E.details_context(MODE, oid)
    if ctx is None:
        redirect(URL('collecte', vars=dict(msg='not_found')))
    return ctx


# --- Export Excel ----------------------------------------------------------
@action('aoo/export', method=['GET'])
@action.uses(db, session, auth, access)
def aoo_export():
    data = E.export_xlsx(MODE)
    if data is None:
        redirect(URL('collecte', vars=dict(msg='export_na')))
    return data
