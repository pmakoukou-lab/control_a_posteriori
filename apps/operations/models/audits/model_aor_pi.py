# -*- coding: utf-8 -*-
"""
Modèle pyDAL — Mode de passation : AOR_PI.

Fichier généré depuis la grille de saisie + le fichier « base de données »
(workdir_files) qui indique, par section, si elle relève de l'opération ou de
l'allotissement (lot). Tables PROPRES au mode (préfixe ``aor_pi_``) :

  - ``aor_pi_operations``     : sections au niveau de l'opération.
  - ``aor_pi_allotissements`` : sections renseignées PAR LOT (relation 1-N).

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
    """Définit la table `aor_pi_operations` (64 champs métier) et la retourne."""
    db.define_table(
        "aor_pi_operations",
        Field("agent_dgmp", "string", label="Nom de l'Agent DGMP", comment="Section: Contrôleur | col. B"),
        Field("date_controle", "date", label="Date de contrôle", comment="Section: Date de contrôle | col. C"),
        Field("ministere", "reference ministere", label="Ministère", comment="Section: Ministère | col. D"),
        Field("autorite_contractante", "reference autorite_contractante", label="Autorité Contractante", comment="Section: Autorité Contractante | col. E"),
        Field("interlocuteur_ac", "string", label="Interlocuteur chez l'AC", comment="Section: Personne Ressource | col. F"),
        Field("imputation_budgetaire", "integer", label="Imputation Budgétaire", comment="Section: Imputation Budgétaire | col. G"),
        Field("montant_dotation_credit", "double", label="Montant", comment="Section: Montant de la dotation / du Crédit | col. H"),
        Field("n_bomp", "string", label="N° de l'AOR", comment="Section: Numéro de l'opération | col. I"),
        Field("objet_operation", "string", label="Objet de l'Opération", comment="Section: Objet de l'Opération | col. J"),
        Field("objet_operation_observation", "text", label="Observations", comment="Section: Objet de l'Opération | col. K"),
        Field("preparation_ppm_pspm_existence_ppm_pspm", "boolean", label="Existence du PPM / PSPM", comment="Section: Préparation du PPM / PSPM | col. L"),
        Field("preparation_ppm_pspm_observations", "text", label="Observations", comment="Section: Préparation du PPM / PSPM | col. M"),
        Field("preparation_ppm_pspm_respect_ppm_pspm", "boolean", label="Respect du PPM / PSPM", comment="Section: Préparation du PPM / PSPM | col. N"),
        Field("preparation_ppm_pspm_observations_2", "text", label="Observations", comment="Section: Préparation du PPM / PSPM | col. O"),
        Field("operation_reservee_pme_constat", "boolean", label="Constat", comment="Section: Opération réservée aux PME | col. Q"),
        Field("operation_reservee_pme_observations", "text", label="Observations", comment="Section: Opération réservée aux PME | col. R"),
        Field("mode_selection_entreprises_ami_requete_motivee", "string", label="AMI ou Requête motivée", comment="Section: Mode de sélection des entreprises | col. S"),
        Field("publication_ami_bomp_constat", "boolean", label="Constat", comment="Section: Publication de l'AMI dans le BOMP | col. T"),
        Field("publication_ami_bomp_date_publication", "date", label="Date de publication", comment="Section: Publication de l'AMI dans le BOMP | col. U"),
        Field("publication_ami_bomp_observations", "text", label="Observations", comment="Section: Publication de l'AMI dans le BOMP | col. V"),
        Field("autorisation_recourir_aor_constat", "boolean", label="Constat", comment="Section: Autorisation de recourir à l'AOR | col. W"),
        Field("autorisation_recourir_aor_reference_autorisation", "string", label="Référence de l'autorisation", comment="Section: Autorisation de recourir à l'AOR | col. X"),
        Field("examen_validation_dp_dgmp_constat", "boolean", label="Constat", comment="Section: Examen et validation de la DP par la DGMP | col. AI"),
        Field("examen_validation_dp_dgmp_date_reception_dp_dgmp", "date", label="Date de reception de la DP à la DGMP", comment="Section: Examen et validation de la DP par la DGMP | col. AJ"),
        Field("examen_validation_dp_dgmp_date_validation_dp", "date", label="Date de validation de la DP", comment="Section: Examen et validation de la DP par la DGMP | col. AK"),
        Field("examen_validation_dp_dgmp_observations", "text", label="Observations", comment="Section: Examen et validation de la DP par la DGMP | col. AL"),
        Field("existence_cojo_conformite", "boolean", label="Conformite", comment="Section: Existence de la COJO | col. AP"),
        Field("existence_cojo_observations", "text", label="Observations", comment="Section: Existence de la COJO | col. AQ"),
        Field("existence_mandats_representants_membres_cojo_constat", "boolean", label="Constat", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AR"),
        Field("existence_mandats_representants_membres_cojo_observati", "text", label="Observations", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AS"),
        Field("existence_proces_verbal_douverture_plis_existence_pv", "boolean", label="Existence du PV", comment="Section: Existence du procès-verbal d’ouverture des plis techniques | col. AV"),
        Field("existence_proces_verbal_douverture_plis_observations", "text", label="Observations", comment="Section: Existence du procès-verbal d’ouverture des plis techniques | col. AW"),
        Field("existence_rapport_danalyse_offres_techniques_existence", "boolean", label="Existence du rapport", comment="Section: Existence du rapport d’analyse des offres techniques | col. AX"),
        Field("existence_rapport_danalyse_offres_techniques_observati", "text", label="Observations", comment="Section: Existence du rapport d’analyse des offres techniques | col. AY"),
        Field("conformite_cojo_jugement_offres_techniques_constat", "boolean", label="Constat", comment="Section: Conformité de la COJO au jugement des offres techniques | col. AZ"),
        Field("conformite_cojo_jugement_offres_techniques_observation", "text", label="Observations", comment="Section: Conformité de la COJO au jugement des offres techniques | col. BA"),
        Field("existence_proces_verbal_jugement_offres_existence_rapp", "boolean", label="Existence du rapport", comment="Section: Existence du procès-verbal de jugement des offres techniques | col. BB"),
        Field("existence_proces_verbal_jugement_offres_observations", "text", label="Observations", comment="Section: Existence du procès-verbal de jugement des offres techniques | col. BC"),
        Field("existence_proces_verbal_douverture_plis_existence_pv_2", "boolean", label="Existence du PV", comment="Section: Existence du procès-verbal d’ouverture des plis financiers | col. BD"),
        Field("existence_proces_verbal_douverture_plis_observations_2", "text", label="Observations", comment="Section: Existence du procès-verbal d’ouverture des plis financiers | col. BE"),
        Field("existence_rapport_danalyse_offres_financiers_existence", "boolean", label="Existence du rapport", comment="Section: Existence du rapport d’analyse des offres financiers | col. BF"),
        Field("existence_rapport_danalyse_offres_financiers_observati", "text", label="Observations", comment="Section: Existence du rapport d’analyse des offres financiers | col. BG"),
        Field("conformite_cojo_jugement_combine_offres_constat", "boolean", label="Constat", comment="Section: Conformité de la COJO au jugement combiné des offres financières | col. BH"),
        Field("conformite_cojo_jugement_combine_offres_observations", "text", label="Observations", comment="Section: Conformité de la COJO au jugement combiné des offres financières | col. BI"),
        Field("existence_proces_verbal_jugement_combine_existence_rap", "boolean", label="Existence du rapport", comment="Section: Existence du procès-verbal de jugement combiné des offres financières | col. BJ"),
        Field("existence_proces_verbal_jugement_combine_observations", "text", label="Observations", comment="Section: Existence du procès-verbal de jugement combiné des offres financières | col. BK"),
        Field("respect_delai_imparti_cojo_ses_constat", "boolean", label="Constat", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BL"),
        Field("respect_delai_imparti_cojo_ses_date_ouverture_plis_tec", "date", label="Date d'ouverture des plis techniques", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BM"),
        Field("respect_delai_imparti_cojo_ses_date_jugement_plis_tech", "date", label="Date de jugement des plis techniques", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BN"),
        Field("respect_delai_imparti_cojo_ses_date_ouverture_plis_fin", "date", label="Date d'ouverture des plis financiers", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BO"),
        Field("respect_delai_imparti_cojo_ses_date_jugement_plis_fina", "date", label="Date de jugement des plis financiers", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BP"),
        Field("respect_delai_imparti_cojo_ses_date_dernier_jugement_c", "date", label="Date de dernier jugement en cas de recours", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BQ"),
        Field("respect_delai_imparti_cojo_ses_nombre_jugements", "integer", label="Nombre de jugements", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BR"),
        Field("respect_delai_imparti_cojo_ses_respect_delai", "boolean", label="Respect du délai", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BS"),
        Field("respect_delai_imparti_cojo_ses_observations", "text", label="Observations", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BT"),
        Field("publication_resultats_cojo_dgmp_constat", "boolean", label="Constat", comment="Section: Publication des résultats de la COJO par la DGMP | col. CA"),
        Field("publication_resultats_cojo_dgmp_date_publication", "date", label="Date de publication", comment="Section: Publication des résultats de la COJO par la DGMP | col. CB"),
        Field("publication_resultats_cojo_dgmp_numero_bomp", "string", label="Numéro du BOMP", comment="Section: Publication des résultats de la COJO par la DGMP | col. CC"),
        Field("publication_resultats_cojo_dgmp_observations", "text", label="Observations", comment="Section: Publication des résultats de la COJO par la DGMP | col. CD"),
        Field("exigence_quitus_non_redevance_dao_constat", "boolean", label="Constat", comment="Section: Exigence du quitus de non redevance dans le DAO | col. CR"),
        Field("exigence_quitus_non_redevance_dao_observations", "text", label="Observations", comment="Section: Exigence du quitus de non redevance dans le DAO | col. CS"),
        Field("situation_execution_ligne_budgetaire_apres_montant_dis", "double", label="Montant disponible", comment="Section: Situation d'exécution de la ligne budgetaire après passation | col. DI"),
        Field("temps_total_conduite_loperation_nombre_jours", "integer", label="Nombre de jours", comment="Section: Temps total pour la conduite de l’opération | col. EG"),
        Field("temps_total_conduite_loperation_observations", "text", label="Observations", comment="Section: Temps total pour la conduite de l’opération | col. EH"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aor_pi_operations


def define_allotissements(db):
    """Définit la table `aor_pi_allotissements` (73 champs métier, 1-N) et la retourne."""
    db.define_table(
        "aor_pi_allotissements",
        Field("operation", "reference aor_pi_operations", label="Dossier opération", comment="Référence vers la table parente"),
        Field("objet_lot", "string", label="Objet du lot", comment="Objet du lot"),
        Field("numero_lot", "integer", label="N° du lot", comment="Numéro du lot"),
        Field("montant_estimation", "double", label="Montant", comment="Section: Montant de l'estimation | col. P"),
        Field("liste_entreprises_retenues_cabinet_1", "string", label="Cabinet 1", comment="Section: Liste des entreprises retenues | col. Y"),
        Field("liste_entreprises_retenues_ncc", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. Z"),
        Field("liste_entreprises_retenues_cabinet_2", "string", label="Cabinet 2", comment="Section: Liste des entreprises retenues | col. AA"),
        Field("liste_entreprises_retenues_ncc_2", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AB"),
        Field("liste_entreprises_retenues_cabinet_3", "string", label="Cabinet 3", comment="Section: Liste des entreprises retenues | col. AC"),
        Field("liste_entreprises_retenues_ncc_3", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AD"),
        Field("liste_entreprises_retenues_cabinet_4", "string", label="Cabinet 4", comment="Section: Liste des entreprises retenues | col. AE"),
        Field("liste_entreprises_retenues_ncc_4", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AF"),
        Field("liste_entreprises_retenues_cabinet_5", "string", label="Cabinet 5", comment="Section: Liste des entreprises retenues | col. AG"),
        Field("liste_entreprises_retenues_ncc_5", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AH"),
        Field("transmission_lettres_invitation_candidats_retenus_cons", "boolean", label="Constat", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AM"),
        Field("transmission_lettres_invitation_candidats_retenus_date", "date", label="Date de transmission", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AN"),
        Field("transmission_lettres_invitation_candidats_retenus_obse", "text", label="Observations", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AO"),
        Field("nombre_plis_recus_ouverture_nombre_plis", "integer", label="Nombre de plis", comment="Section: Nombre de plis reçus à l'ouverture | col. AT"),
        Field("nombre_plis_recus_ouverture_observations", "text", label="Observations", comment="Section: Nombre de plis reçus à l'ouverture | col. AU"),
        Field("attributaire_nom", "string", label="Raison sociale", comment="Section: Attributaire(s) | col. BU"),
        Field("attributaire_ncc", "string", label="NCC attributaire", comment="Section: Attributaire(s) | col. BV"),
        Field("attributaire_lot", "string", label="Lot", comment="Section: Attributaire(s) | col. BW"),
        Field("attributaire_objet", "string", label="Objet", comment="Section: Attributaire(s) | col. BX"),
        Field("attributaire_montant", "double", label="Montant", comment="Section: Attributaire(s) | col. BY"),
        Field("attributaire_observation", "text", label="Observations", comment="Section: Attributaire(s) | col. BZ"),
        Field("notification_resultats_attributaires_constat", "boolean", label="Constat", comment="Section: Notification des résultats aux attributaires | col. CE"),
        Field("notification_resultats_attributaires_date", "date", label="Date", comment="Section: Notification des résultats aux attributaires | col. CF"),
        Field("notification_resultats_attributaires_observations", "text", label="Observations", comment="Section: Notification des résultats aux attributaires | col. CG"),
        Field("information_soumissionnaires_non_retenus_constat", "boolean", label="Constat", comment="Section: Information des soumissionnaires non retenus | col. CH"),
        Field("information_soumissionnaires_non_retenus_observations", "text", label="Observations", comment="Section: Information des soumissionnaires non retenus | col. CI"),
        Field("respect_delai_recours_eventuels_constat", "boolean", label="Constat", comment="Section: Respect du délai de recours éventuels | col. CJ"),
        Field("respect_delai_recours_eventuels_observations", "text", label="Observations", comment="Section: Respect du délai de recours éventuels | col. CK"),
        Field("production_pieces_fiscales_sociales_lattributaire_cons", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CL"),
        Field("production_pieces_fiscales_sociales_lattributaire_obse", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CM"),
        Field("existence_dun_marche_constat", "boolean", label="Constat", comment="Section: Existence d’un marché | col. CN"),
        Field("existence_dun_marche_observations", "text", label="Observations", comment="Section: Existence d’un marché | col. CO"),
        Field("production_pieces_fiscales_sociales_lattributaire_cons_2", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CP"),
        Field("production_pieces_fiscales_sociales_lattributaire_obse_2", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CQ"),
        Field("conformite_contenu_marche_constat", "boolean", label="Constat", comment="Section: Conformité du contenu du marché | col. CT"),
        Field("conformite_contenu_marche_observations", "text", label="Observations", comment="Section: Conformité du contenu du marché | col. CU"),
        Field("signature_marche_lattributaire_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’attributaire | col. CV"),
        Field("signature_marche_lattributaire_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’attributaire | col. CW"),
        Field("signature_marche_lattributaire_observations", "text", label="Observations", comment="Section: Signature du marché par l’attributaire | col. CX"),
        Field("signature_marche_lautorite_contractante_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’Autorité Contractante | col. CY"),
        Field("signature_marche_lautorite_contractante_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’Autorité Contractante | col. CZ"),
        Field("signature_marche_lautorite_contractante_observations", "text", label="Observations", comment="Section: Signature du marché par l’Autorité Contractante | col. DA"),
        Field("signature_lautorite_competente_constat", "boolean", label="Constat", comment="Section: Signature de l’autorité compétente | col. DB"),
        Field("signature_lautorite_competente_observations", "text", label="Observations", comment="Section: Signature de l’autorité compétente | col. DC"),
        Field("numerotation_marche_constat", "boolean", label="Constat", comment="Section: Numérotation du marché | col. DD"),
        Field("numerotation_marche_numero", "string", label="Numéro", comment="Section: Numérotation du marché | col. DE"),
        Field("numerotation_marche_observations", "text", label="Observations", comment="Section: Numérotation du marché | col. DF"),
        Field("montant_marche", "double", label="Montant", comment="Section: Montant du marché | col. DG"),
        Field("ecart_entre_montant_estimatif", "double", label="Montant", comment="Section: Ecart entre montant estimatif et montant attribué | col. DH"),
        Field("examen_prealable_approbation_constat", "boolean", label="Constat", comment="Section: Examen préalable à l'approbation | col. DJ"),
        Field("examen_prealable_approbation_date_soumission_projet_ma", "date", label="Date de soumission du projet de marché à la DGMP", comment="Section: Examen préalable à l'approbation | col. DK"),
        Field("examen_prealable_approbation_date_validation_projet_ma", "date", label="Date de validation du projet de marché par la DGMP", comment="Section: Examen préalable à l'approbation | col. DL"),
        Field("examen_prealable_approbation_observations", "text", label="Observations", comment="Section: Examen préalable à l'approbation | col. DM"),
        Field("approbation_marche_constat", "boolean", label="Constat", comment="Section: Approbation du marché | col. DN"),
        Field("approbation_marche_date_approbation", "date", label="Date d'approbation", comment="Section: Approbation du marché | col. DO"),
        Field("approbation_marche_observations", "text", label="Observations", comment="Section: Approbation du marché | col. DP"),
        Field("autorite_approbatrice_organe_approbateur_competent_con", "boolean", label="Constat", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. DQ"),
        Field("autorite_approbatrice_organe_approbateur_competent_obs", "text", label="Observations", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. DR"),
        Field("notification_lapprobation_marche_titulaire_constat", "boolean", label="Constat", comment="Section: Notification de l’approbation du marché au titulaire | col. DS"),
        Field("notification_lapprobation_marche_titulaire_date_recept", "date", label="Date de reception par le titulaire", comment="Section: Notification de l’approbation du marché au titulaire | col. DT"),
        Field("notification_lapprobation_marche_titulaire_observation", "text", label="Observations", comment="Section: Notification de l’approbation du marché au titulaire | col. DU"),
        Field("enregistrement_marche_constat", "boolean", label="Constat", comment="Section: Enregistrement du marché | col. DV"),
        Field("enregistrement_marche_observations", "text", label="Observations", comment="Section: Enregistrement du marché | col. DW"),
        Field("transmission_02_exemplaires_contrat_dgmp_constat", "boolean", label="Constat", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DX"),
        Field("transmission_02_exemplaires_contrat_dgmp_observations", "text", label="Observations", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DY"),
        Field("notification_lordre_service_demarrage_constat", "boolean", label="Constat", comment="Section: Notification de l’ordre de service de démarrage | col. DZ"),
        Field("notification_lordre_service_demarrage_date_accuse_rece", "date", label="Date sur l'accusé de reception", comment="Section: Notification de l’ordre de service de démarrage | col. EA"),
        Field("notification_lordre_service_demarrage_conforme", "boolean", label="Conforme", comment="Section: Notification de l’ordre de service de démarrage | col. EB"),
        Field("notification_lordre_service_demarrage_observations", "text", label="Observations", comment="Section: Notification de l’ordre de service de démarrage | col. EC"),
        Field("existence_exhaustivite_larchivage_documents_existence", "boolean", label="Existence", comment="Section: Existence et exhaustivité de l’archivage des documents | col. ED"),
        Field("existence_exhaustivite_larchivage_documents_exhaustivi", "boolean", label="Exhaustivité", comment="Section: Existence et exhaustivité de l’archivage des documents | col. EE"),
        Field("existence_exhaustivite_larchivage_documents_observatio", "text", label="Observations", comment="Section: Existence et exhaustivité de l’archivage des documents | col. EF"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aor_pi_allotissements


def define_all(db):
    """Définit `aor_pi_operations` puis sa sous-table `aor_pi_allotissements` (1-N)."""
    define_operations(db)
    define_allotissements(db)
    return db
