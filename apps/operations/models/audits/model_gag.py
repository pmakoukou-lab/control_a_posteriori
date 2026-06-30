# -*- coding: utf-8 -*-
"""
Modèle pyDAL — Mode de passation : GAG.

Fichier généré depuis la grille de saisie + le fichier « base de données »
(workdir_files) qui indique, par section, si elle relève de l'opération ou de
l'allotissement (lot). Tables PROPRES au mode (préfixe ``gag_``) :

  - ``gag_operations``     : sections au niveau de l'opération.
  - ``gag_allotissements`` : sections renseignées PAR LOT (relation 1-N).

Les tables de référence (ministere, autorite_contractante, nature_operation…)
sont définies en amont par ``table_parametres_models.define_all``.
"""
from datetime import datetime, timezone

from pydal import Field

from ...common import auth


def _meta_fields():
    """Champs de traçabilité communs (soft delete + audit)."""
    return [
        Field("is_deleted", "boolean", default=False, readable=False),
        Field("created_on", "datetime", default=lambda: datetime.now(timezone.utc),
              writable=False),
        Field("created_by", "reference auth_user", default=auth.user_id, writable=False),
        # Rattachement à la période de contrôle (renseignés par le contrôleur à la
        # création, depuis le contexte Gestion / Session de l'en-tête).
        Field("gestion", "reference exercice_budgetaire", label="Gestion", writable=False, ondelete="SET NULL"),
        Field("session", "reference session_budgetaire", label="Session", writable=False, ondelete="SET NULL"),
    ]


def define_operations(db):
    """Définit la table `gag_operations` (22 champs métier) et la retourne."""
    db.define_table(
        "gag_operations",
        Field("agent_dgmp", "string", label="Nom de l'Agent DGMP", comment="Section: Contrôleur | col. B"),
        Field("date_controle", "date", label="Date de contrôle", comment="Section: Date de contrôle | col. C"),
        Field("ministere", "reference ministere", label="Ministère", comment="Section: Ministère | col. D"),
        Field("autorite_contractante", "reference autorite_contractante", label="Autorité Contractante", comment="Section: Autorité Contractante | col. E"),
        Field("interlocuteur_ac", "string", label="Interlocuteur chez l'AC", comment="Section: Personne Ressource | col. F"),
        Field("imputation_budgetaire", "integer", label="Imputation Budgétaire", comment="Section: Imputation Budgétaire | col. G"),
        Field("montant_dotation_credit", "double", label="Montant", comment="Section: Montant de la dotation / du Crédit | col. H"),
        Field("objet_operation", "string", label="Objet de l'Opération", comment="Section: Objet de l'Opération | col. I"),
        Field("nature_operation", "reference nature_operation", label="Nature de l'opération", comment="Section: Nature de l'opération | col. J"),
        Field("nature_operation_observation", "text", label="Observations", comment="Section: Nature de l'opération | col. K"),
        Field("nature_operation_nombre", "integer", label="Nombre", comment="Section: Nature de l'opération | col. L"),
        Field("preparation_ppm_existence_ppm", "boolean", label="Existence du PPM", comment="Section: Préparation du PPM | col. M"),
        Field("preparation_ppm_observations", "text", label="Observations", comment="Section: Préparation du PPM | col. N"),
        Field("preparation_ppm_respect_ppm", "boolean", label="Respect du PPM", comment="Section: Préparation du PPM | col. O"),
        Field("preparation_ppm_observations_2", "text", label="Observations", comment="Section: Préparation du PPM | col. P"),
        Field("operation_reservee_pme_constat", "boolean", label="Constat", comment="Section: Opération réservée aux PME | col. R"),
        Field("operation_reservee_pme_observations", "text", label="Observations", comment="Section: Opération réservée aux PME | col. S"),
        Field("autorisation_recourir_gre_gre_constat", "boolean", label="Constat", comment="Section: Autorisation de recourir au Gré à Gré | col. T"),
        Field("autorisation_recourir_gre_gre_reference_autorisation", "string", label="Référence de l'autorisation", comment="Section: Autorisation de recourir au Gré à Gré | col. U"),
        Field("situation_execution_ligne_budgetaire_apres_montant_dis", "double", label="Montant disponible", comment="Section: Situation d'exécution de la ligne budgetaire après passation | col. AV"),
        Field("temps_total_conduite_loperation_nombre_jours", "integer", label="Nombre de jours", comment="Section: Temps total pour la conduite de l’opération | col. BR"),
        Field("temps_total_conduite_loperation_observations", "text", label="Observations", comment="Section: Temps total pour la conduite de l’opération | col. BS"),
        *_meta_fields(),
        migrate=True,
    )
    return db.gag_operations


def define_allotissements(db):
    """Définit la table `gag_allotissements` (48 champs métier, 1-N) et la retourne."""
    db.define_table(
        "gag_allotissements",
        Field("operation", "reference gag_operations", label="Dossier opération", comment="Référence vers la table parente"),
        Field("objet_lot", "string", label="Objet du lot", comment="Objet du lot"),
        Field("numero_lot", "integer", label="N° du lot", comment="Numéro du lot"),
        Field("montant_estimation", "double", label="Montant", comment="Section: Montant de l'Estimation | col. Q"),
        Field("attributaire_nom", "string", label="Raison sociale", comment="Section: Attributaire(s) | col. V"),
        Field("attributaire_ncc", "string", label="NCC attributaire", comment="Section: Attributaire(s) | col. W"),
        Field("attributaire_lot", "string", label="LOT", comment="Section: Attributaire(s) | col. X"),
        Field("attributaire_objet", "string", label="Objet", comment="Section: Attributaire(s) | col. Y"),
        Field("attributaire_montant", "double", label="Montant", comment="Section: Attributaire(s) | col. Z"),
        Field("attributaire_observation", "text", label="Observations", comment="Section: Attributaire(s) | col. AA"),
        Field("existence_dun_marche_constat", "boolean", label="Constat", comment="Section: Existence d’un marché | col. AB"),
        Field("existence_dun_marche_observations", "text", label="Observations", comment="Section: Existence d’un marché | col. AC"),
        Field("production_pieces_fiscales_sociales_lattributaire_cons", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. AD"),
        Field("production_pieces_fiscales_sociales_lattributaire_obse", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. AE"),
        Field("exigence_quitus_non_redevance_arcop_constat", "boolean", label="Constat", comment="Section: Exigence du quitus de non redevance de l'ARCOP | col. AF"),
        Field("exigence_quitus_non_redevance_arcop_observations", "text", label="Observations", comment="Section: Exigence du quitus de non redevance de l'ARCOP | col. AG"),
        Field("conformite_contenu_marche_constat", "boolean", label="Constat", comment="Section: Conformité du contenu du marché | col. AH"),
        Field("conformite_contenu_marche_observations", "text", label="Observations", comment="Section: Conformité du contenu du marché | col. AI"),
        Field("signature_marche_lattributaire_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’attributaire | col. AJ"),
        Field("signature_marche_lattributaire_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’attributaire | col. AK"),
        Field("signature_marche_lattributaire_observations", "text", label="Observations", comment="Section: Signature du marché par l’attributaire | col. AL"),
        Field("signature_marche_lautorite_contractante_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’Autorité Contractante | col. AM"),
        Field("signature_marche_lautorite_contractante_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’Autorité Contractante | col. AN"),
        Field("signature_marche_lautorite_contractante_observations", "text", label="Observations", comment="Section: Signature du marché par l’Autorité Contractante | col. AO"),
        Field("signature_lautorite_competente_constat", "boolean", label="Constat", comment="Section: Signature de l’autorité compétente | col. AP"),
        Field("signature_lautorite_competente_observations", "text", label="Observations", comment="Section: Signature de l’autorité compétente | col. AQ"),
        Field("numerotation_marche_constat", "boolean", label="Constat", comment="Section: Numérotation du marché | col. AR"),
        Field("numerotation_marche_numero", "string", label="Numéro", comment="Section: Numérotation du marché | col. AS"),
        Field("numerotation_marche_observations", "text", label="Observations", comment="Section: Numérotation du marché | col. AT"),
        Field("montant_marche", "double", label="Montant", comment="Section: Montant du marché | col. AU"),
        Field("examen_prealable_approbation_constat", "boolean", label="Constat", comment="Section: Examen préalable à l'approbation | col. AW"),
        Field("examen_prealable_approbation_date_soumission_projet_ma", "date", label="Date de soumission du projet de marché à la DGMP", comment="Section: Examen préalable à l'approbation | col. AX"),
        Field("examen_prealable_approbation_date_validation_projet_ma", "date", label="Date de validation du projet de marché par la DGMP", comment="Section: Examen préalable à l'approbation | col. AY"),
        Field("examen_prealable_approbation_observations", "text", label="Observations", comment="Section: Examen préalable à l'approbation | col. AZ"),
        Field("approbation_marche_constat", "boolean", label="Constat", comment="Section: Approbation du marché | col. BA"),
        Field("approbation_marche_date_approbation", "date", label="Date d'approbation", comment="Section: Approbation du marché | col. BB"),
        Field("approbation_marche_observations", "text", label="Observations", comment="Section: Approbation du marché | col. BC"),
        Field("autorite_approbatrice_organe_approbateur_competent_con", "boolean", label="Constat", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. BD"),
        Field("autorite_approbatrice_organe_approbateur_competent_obs", "text", label="Observations", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. BE"),
        Field("notification_lapprobation_marche_titulaire_constat", "boolean", label="Constat", comment="Section: Notification de l’approbation du marché au titulaire | col. BF"),
        Field("notification_lapprobation_marche_titulaire_date_recept", "date", label="Date de reception par le titulaire", comment="Section: Notification de l’approbation du marché au titulaire | col. BG"),
        Field("notification_lapprobation_marche_titulaire_observation", "text", label="Observations", comment="Section: Notification de l’approbation du marché au titulaire | col. BH"),
        Field("enregistrement_marche_constat", "boolean", label="Constat", comment="Section: Enregistrement du marché | col. BI"),
        Field("enregistrement_marche_observations", "text", label="Observations", comment="Section: Enregistrement du marché | col. BJ"),
        Field("notification_lordre_service_demarrage_constat", "boolean", label="Constat", comment="Section: Notification de l’ordre de service de démarrage | col. BK"),
        Field("notification_lordre_service_demarrage_date_accuse_rece", "date", label="Date sur l'accusé de reception", comment="Section: Notification de l’ordre de service de démarrage | col. BL"),
        Field("notification_lordre_service_demarrage_conforme", "boolean", label="Conforme", comment="Section: Notification de l’ordre de service de démarrage | col. BM"),
        Field("notification_lordre_service_demarrage_observations", "text", label="Observations", comment="Section: Notification de l’ordre de service de démarrage | col. BN"),
        Field("existence_exhaustivite_larchivage_documents_existence", "boolean", label="Existence", comment="Section: Existence et exhaustivité de l’archivage des documents | col. BO"),
        Field("existence_exhaustivite_larchivage_documents_exhaustivi", "boolean", label="Exhaustivité", comment="Section: Existence et exhaustivité de l’archivage des documents | col. BP"),
        Field("existence_exhaustivite_larchivage_documents_observatio", "text", label="Observations", comment="Section: Existence et exhaustivité de l’archivage des documents | col. BQ"),
        *_meta_fields(),
        migrate=True,
    )
    return db.gag_allotissements


def define_all(db):
    """Définit `gag_operations` puis sa sous-table `gag_allotissements` (1-N)."""
    define_operations(db)
    define_allotissements(db)
    return db
