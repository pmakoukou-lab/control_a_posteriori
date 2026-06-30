# -*- coding: utf-8 -*-
"""
Modèle pyDAL — Mode de passation : AOR_FT.

Fichier généré depuis la grille de saisie + le fichier « base de données »
(workdir_files) qui indique, par section, si elle relève de l'opération ou de
l'allotissement (lot). Tables PROPRES au mode (préfixe ``aor_ft_``) :

  - ``aor_ft_operations``     : sections au niveau de l'opération.
  - ``aor_ft_allotissements`` : sections renseignées PAR LOT (relation 1-N).

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
    """Définit la table `aor_ft_operations` (56 champs métier) et la retourne."""
    db.define_table(
        "aor_ft_operations",
        Field("agent_dgmp", "string", label="Nom de l'Agent DGMP", comment="Section: Contrôleur | col. B"),
        Field("date_controle", "date", label="Date de contrôle", comment="Section: Date de contrôle | col. C"),
        Field("ministere", "reference ministere", label="Ministère", comment="Section: Ministère | col. D"),
        Field("autorite_contractante", "reference autorite_contractante", label="Autorité Contractante", comment="Section: Autorité Contractante | col. E"),
        Field("interlocuteur_ac", "string", label="Interlocuteur chez l'AC", comment="Section: Personne Ressource | col. F"),
        Field("imputation_budgetaire", "integer", label="Imputation Budgétaire", comment="Section: Imputation Budgétaire | col. G"),
        Field("montant_dotation_credit", "double", label="Montant", comment="Section: Montant de la dotation / du Crédit | col. H"),
        Field("n_bomp", "string", label="N° de l'AOR", comment="Section: Numéro de l'opération | col. I"),
        Field("objet_operation", "string", label="Objet de l'Opération", comment="Section: Objet de l'Opération | col. J"),
        Field("nature_operation", "reference nature_operation", label="Nature de l'opération", comment="Section: Nature de l'opération | col. K"),
        Field("nature_operation_observation", "text", label="Observations", comment="Section: Nature de l'opération | col. L"),
        Field("nature_operation_nb", "text", label="NB", comment="Section: Nature de l'opération | col. M"),
        Field("preparation_ppm_pspm_existence_ppm_pspm", "boolean", label="Existence du PPM / PSPM", comment="Section: Préparation du PPM / PSPM | col. N"),
        Field("preparation_ppm_pspm_observations", "text", label="Observations", comment="Section: Préparation du PPM / PSPM | col. O"),
        Field("preparation_ppm_pspm_respect_ppm_pspm", "boolean", label="Respect du PPM / PSPM", comment="Section: Préparation du PPM / PSPM | col. P"),
        Field("preparation_ppm_pspm_observations_2", "text", label="Observations", comment="Section: Préparation du PPM / PSPM | col. Q"),
        Field("operation_reservee_pme_constat", "boolean", label="Constat", comment="Section: Opération réservée aux PME | col. S"),
        Field("operation_reservee_pme_observations", "text", label="Observations", comment="Section: Opération réservée aux PME | col. T"),
        Field("mode_selection_entreprises_prequalification_requete_mo", "string", label="Préqualification ou Requête motivée", comment="Section: Mode de sélection des entreprises | col. U"),
        Field("publication_avis_prequalification_bomp_constat", "boolean", label="Constat", comment="Section: Publication de l'avis de préqualification dans le BOMP | col. V"),
        Field("publication_avis_prequalification_bomp_date_publicatio", "date", label="Date de publication", comment="Section: Publication de l'avis de préqualification dans le BOMP | col. W"),
        Field("publication_avis_prequalification_bomp_observations", "text", label="Observations", comment="Section: Publication de l'avis de préqualification dans le BOMP | col. X"),
        Field("autorisation_recourir_aor_constat", "boolean", label="Constat", comment="Section: Autorisation de recourir à l'AOR | col. Y"),
        Field("autorisation_recourir_aor_reference_autorisation", "string", label="Référence de l'autorisation", comment="Section: Autorisation de recourir à l'AOR | col. Z"),
        Field("examen_validation_dao_dgmp_constat", "boolean", label="Constat", comment="Section: Examen et validation du DAO par la DGMP | col. AK"),
        Field("examen_validation_dao_dgmp_date_reception_dao_dgmp", "date", label="Date de reception du DAO par la DGMP", comment="Section: Examen et validation du DAO par la DGMP | col. AL"),
        Field("examen_validation_dao_dgmp_date_validation_dao_dgmp", "date", label="Date de validation du DAO par la DGMP", comment="Section: Examen et validation du DAO par la DGMP | col. AM"),
        Field("examen_validation_dao_dgmp_observations", "text", label="Observations", comment="Section: Examen et validation du DAO par la DGMP | col. AN"),
        Field("existence_cojo_conformite", "boolean", label="Conformite", comment="Section: Existence de la COJO | col. AV"),
        Field("existence_cojo_observations", "text", label="Observations", comment="Section: Existence de la COJO | col. AW"),
        Field("existence_mandats_representants_membres_cojo_constat", "boolean", label="Constat", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AX"),
        Field("existence_mandats_representants_membres_cojo_observati", "text", label="Observations", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AY"),
        Field("existence_proces_verbal_douverture_plis_existence_pv", "boolean", label="Existence du PV", comment="Section: Existence du procès-verbal d’ouverture des plis | col. BB"),
        Field("existence_proces_verbal_douverture_plis_observations", "text", label="Observations", comment="Section: Existence du procès-verbal d’ouverture des plis | col. BC"),
        Field("existence_rapport_danalyse_offres_existence_rapport", "boolean", label="Existence du rapport", comment="Section: Existence du rapport d’analyse des offres | col. BD"),
        Field("existence_rapport_danalyse_offres_observations", "text", label="Observations", comment="Section: Existence du rapport d’analyse des offres | col. BE"),
        Field("conformite_cojo_jugement_constat", "boolean", label="Constat", comment="Section: Conformité de la COJO au jugement | col. BF"),
        Field("conformite_cojo_jugement_observations", "text", label="Observations", comment="Section: Conformité de la COJO au jugement | col. BG"),
        Field("existence_conformite_proces_verbal_jugement_existence_", "boolean", label="Existence du PV", comment="Section: Existence et conformité du procès-verbal de jugement des offres | col. BH"),
        Field("existence_conformite_proces_verbal_jugement_observatio", "text", label="Observations", comment="Section: Existence et conformité du procès-verbal de jugement des offres | col. BI"),
        Field("respect_delai_imparti_cojo_ses_constat", "boolean", label="Constat", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BJ"),
        Field("respect_delai_imparti_cojo_ses_date_ouverture", "date", label="Date d'ouverture", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BK"),
        Field("respect_delai_imparti_cojo_ses_date_jugement", "date", label="Date de jugement", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BL"),
        Field("respect_delai_imparti_cojo_ses_date_dernier_jugement_c", "date", label="Date de dernier jugement en cas de recours", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BM"),
        Field("respect_delai_imparti_cojo_ses_nombre_jugements", "integer", label="Nombre de jugements", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BN"),
        Field("respect_delai_imparti_cojo_ses_respect_delai", "boolean", label="Respect du délai", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BO"),
        Field("respect_delai_imparti_cojo_ses_observations", "text", label="Observations", comment="Section: Respect du délai imparti à la COJO pour ses travaux | col. BP"),
        Field("publication_resultats_cojo_dgmp_constat", "boolean", label="Constat", comment="Section: Publication des résultats de la COJO par la DGMP | col. BW"),
        Field("publication_resultats_cojo_dgmp_date_publication", "date", label="Date de publication", comment="Section: Publication des résultats de la COJO par la DGMP | col. BX"),
        Field("publication_resultats_cojo_dgmp_numero_bomp", "string", label="Numéro du BOMP", comment="Section: Publication des résultats de la COJO par la DGMP | col. BY"),
        Field("publication_resultats_cojo_dgmp_observations", "text", label="Observations", comment="Section: Publication des résultats de la COJO par la DGMP | col. BZ"),
        Field("exigence_quitus_non_redevance_dao_constat", "boolean", label="Constat", comment="Section: Exigence du quitus de non redevance dans le DAO | col. CL"),
        Field("exigence_quitus_non_redevance_dao_observations", "text", label="Observations", comment="Section: Exigence du quitus de non redevance dans le DAO | col. CM"),
        Field("situation_execution_ligne_budgetaire_apres_montant_dis", "double", label="Montant disponible", comment="Section: Situation d'exécution de la ligne budgetaire après passation | col. DC"),
        Field("temps_total_conduite_loperation_nombre_jours", "integer", label="Nombre de jours", comment="Section: Temps total pour la conduite de l’opération | col. EC"),
        Field("temps_total_conduite_loperation_observations", "text", label="Observations", comment="Section: Temps total pour la conduite de l’opération | col. ED"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aor_ft_operations


def define_allotissements(db):
    """Définit la table `aor_ft_allotissements` (77 champs métier, 1-N) et la retourne."""
    db.define_table(
        "aor_ft_allotissements",
        Field("operation", "reference aor_ft_operations", label="Dossier opération", comment="Référence vers la table parente"),
        Field("objet_lot", "string", label="Objet du lot", comment="Objet du lot"),
        Field("numero_lot", "integer", label="N° du lot", comment="Numéro du lot"),
        Field("montant_estimation", "double", label="Montant", comment="Section: Montant de l'estimation | col. R"),
        Field("liste_entreprises_retenues_entreprise_1", "string", label="Entreprise 1", comment="Section: Liste des entreprises retenues | col. AA"),
        Field("liste_entreprises_retenues_ncc", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AB"),
        Field("liste_entreprises_retenues_entreprise_2", "string", label="Entreprise 2", comment="Section: Liste des entreprises retenues | col. AC"),
        Field("liste_entreprises_retenues_ncc_2", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AD"),
        Field("liste_entreprises_retenues_entreprise_3", "string", label="Entreprise 3", comment="Section: Liste des entreprises retenues | col. AE"),
        Field("liste_entreprises_retenues_ncc_3", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AF"),
        Field("liste_entreprises_retenues_entreprise_4", "string", label="Entreprise 4", comment="Section: Liste des entreprises retenues | col. AG"),
        Field("liste_entreprises_retenues_ncc_4", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AH"),
        Field("liste_entreprises_retenues_entreprise_5", "string", label="Entreprise 5", comment="Section: Liste des entreprises retenues | col. AI"),
        Field("liste_entreprises_retenues_ncc_5", "string", label="NCC", comment="Section: Liste des entreprises retenues | col. AJ"),
        Field("garantie_offre_comprise_entre_1_garantie_minimale_1", "string", label="Garantie minimale 1%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AO"),
        Field("garantie_offre_comprise_entre_1_garantie_maximale_1_5", "string", label="Garantie maximale 1,5%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AP"),
        Field("garantie_offre_comprise_entre_1_constat", "boolean", label="Constat", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AQ"),
        Field("garantie_offre_comprise_entre_1_observations", "text", label="Observations", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AR"),
        Field("transmission_lettres_invitation_candidats_retenus_cons", "boolean", label="Constat", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AS"),
        Field("transmission_lettres_invitation_candidats_retenus_date", "date", label="Date de transmission", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AT"),
        Field("transmission_lettres_invitation_candidats_retenus_obse", "text", label="Observations", comment="Section: Transmission des lettres d'invitation aux candidats retenus | col. AU"),
        Field("nombre_plis_recus_ouverture_nombre_plis", "integer", label="Nombre de plis", comment="Section: Nombre de plis reçus à l'ouverture | col. AZ"),
        Field("nombre_plis_recus_ouverture_observations", "text", label="Observations", comment="Section: Nombre de plis reçus à l'ouverture | col. BA"),
        Field("attributaire_nom", "string", label="Raison sociale", comment="Section: Attributaire(s) | col. BQ"),
        Field("attributaire_ncc", "string", label="NCC attributaire", comment="Section: Attributaire(s) | col. BR"),
        Field("attributaire_lot", "string", label="Lot", comment="Section: Attributaire(s) | col. BS"),
        Field("attributaire_objet", "string", label="Objet", comment="Section: Attributaire(s) | col. BT"),
        Field("attributaire_montant", "double", label="Montant", comment="Section: Attributaire(s) | col. BU"),
        Field("attributaire_observation", "text", label="Observations", comment="Section: Attributaire(s) | col. BV"),
        Field("notification_resultats_attributaires_constat", "boolean", label="Constat", comment="Section: Notification des résultats aux attributaires | col. CA"),
        Field("notification_resultats_attributaires_date", "date", label="Date", comment="Section: Notification des résultats aux attributaires | col. CB"),
        Field("notification_resultats_attributaires_observations", "text", label="Observations", comment="Section: Notification des résultats aux attributaires | col. CC"),
        Field("information_soumissionnaires_non_retenus_constat", "boolean", label="Constat", comment="Section: Information des soumissionnaires non retenus | col. CD"),
        Field("information_soumissionnaires_non_retenus_observations", "text", label="Observations", comment="Section: Information des soumissionnaires non retenus | col. CE"),
        Field("respect_delai_recours_eventuels_constat", "boolean", label="Constat", comment="Section: Respect du délai de recours éventuels | col. CF"),
        Field("respect_delai_recours_eventuels_observations", "text", label="Observations", comment="Section: Respect du délai de recours éventuels | col. CG"),
        Field("existence_dun_marche_constat", "boolean", label="Constat", comment="Section: Existence d’un marché | col. CH"),
        Field("existence_dun_marche_observations", "text", label="Observations", comment="Section: Existence d’un marché | col. CI"),
        Field("production_pieces_fiscales_sociales_lattributaire_cons", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CJ"),
        Field("production_pieces_fiscales_sociales_lattributaire_obse", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. CK"),
        Field("conformite_contenu_marche_constat", "boolean", label="Constat", comment="Section: Conformité du contenu du marché | col. CN"),
        Field("conformite_contenu_marche_observations", "text", label="Observations", comment="Section: Conformité du contenu du marché | col. CO"),
        Field("signature_marche_lattributaire_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’attributaire | col. CP"),
        Field("signature_marche_lattributaire_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’attributaire | col. CQ"),
        Field("signature_marche_lattributaire_observations", "text", label="Observations", comment="Section: Signature du marché par l’attributaire | col. CR"),
        Field("signature_marche_lautorite_contractante_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’Autorité Contractante | col. CS"),
        Field("signature_marche_lautorite_contractante_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’Autorité Contractante | col. CT"),
        Field("signature_marche_lautorite_contractante_observations", "text", label="Observations", comment="Section: Signature du marché par l’Autorité Contractante | col. CU"),
        Field("signature_lautorite_competente_constat", "boolean", label="Constat", comment="Section: Signature de l’autorité compétente | col. CV"),
        Field("signature_lautorite_competente_observations", "text", label="Observations", comment="Section: Signature de l’autorité compétente | col. CW"),
        Field("numerotation_marche_constat", "boolean", label="Constat", comment="Section: Numérotation du marché | col. CX"),
        Field("numerotation_marche_numero", "string", label="Numéro", comment="Section: Numérotation du marché | col. CY"),
        Field("numerotation_marche_observations", "text", label="Observations", comment="Section: Numérotation du marché | col. CZ"),
        Field("montant_marche", "double", label="Montant", comment="Section: Montant du marché | col. DA"),
        Field("ecart_entre_montant_estimatif", "double", label="Montant", comment="Section: Ecart entre montant estimatif et montant attribué | col. DB"),
        Field("examen_prealable_approbation_constat", "boolean", label="Constat", comment="Section: Examen préalable à l'approbation | col. DD"),
        Field("examen_prealable_approbation_date_soumission_projet_ma", "date", label="Date de soumission du projet de marché à la DGMP", comment="Section: Examen préalable à l'approbation | col. DE"),
        Field("examen_prealable_approbation_date_validation_projet_ma", "date", label="Date de validation du projet de marché par la DGMP", comment="Section: Examen préalable à l'approbation | col. DF"),
        Field("examen_prealable_approbation_observations", "text", label="Observations", comment="Section: Examen préalable à l'approbation | col. DG"),
        Field("approbation_marche_constat", "boolean", label="Constat", comment="Section: Approbation du marché | col. DH"),
        Field("approbation_marche_date_approbation", "date", label="Date d'approbation", comment="Section: Approbation du marché | col. DI"),
        Field("approbation_marche_observations", "text", label="Observations", comment="Section: Approbation du marché | col. DJ"),
        Field("autorite_approbatrice_organe_approbateur_competent_con", "boolean", label="Constat", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. DK"),
        Field("autorite_approbatrice_organe_approbateur_competent_obs", "text", label="Observations", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. DL"),
        Field("notification_lapprobation_marche_titulaire_constat", "boolean", label="Constat", comment="Section: Notification de l’approbation du marché au titulaire | col. DM"),
        Field("notification_lapprobation_marche_titulaire_date_recept", "date", label="Date de reception par le titulaire", comment="Section: Notification de l’approbation du marché au titulaire | col. DN"),
        Field("notification_lapprobation_marche_titulaire_observation", "text", label="Observations", comment="Section: Notification de l’approbation du marché au titulaire | col. DO"),
        Field("garantie_bonne_execution_constat", "boolean", label="Constat", comment="Section: Garantie de bonne exécution | col. DP"),
        Field("garantie_bonne_execution_observations", "text", label="Observations", comment="Section: Garantie de bonne exécution | col. DQ"),
        Field("enregistrement_marche_constat", "boolean", label="Constat", comment="Section: Enregistrement du marché | col. DR"),
        Field("enregistrement_marche_observations", "text", label="Observations", comment="Section: Enregistrement du marché | col. DS"),
        Field("transmission_02_exemplaires_contrat_dgmp_constat", "boolean", label="Constat", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DT"),
        Field("transmission_02_exemplaires_contrat_dgmp_observations", "text", label="Observations", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DU"),
        Field("notification_lordre_service_demarrage_constat", "boolean", label="Constat", comment="Section: Notification de l’ordre de service de démarrage | col. DV"),
        Field("notification_lordre_service_demarrage_date_accuse_rece", "date", label="Date sur l'accusé de reception", comment="Section: Notification de l’ordre de service de démarrage | col. DW"),
        Field("notification_lordre_service_demarrage_conforme", "boolean", label="Conforme", comment="Section: Notification de l’ordre de service de démarrage | col. DX"),
        Field("notification_lordre_service_demarrage_observations", "text", label="Observations", comment="Section: Notification de l’ordre de service de démarrage | col. DY"),
        Field("existence_exhaustivite_larchivage_documents_existence", "boolean", label="Existence", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DZ"),
        Field("existence_exhaustivite_larchivage_documents_exhaustivi", "boolean", label="Exhaustivité", comment="Section: Existence et exhaustivité de l’archivage des documents | col. EA"),
        Field("existence_exhaustivite_larchivage_documents_observatio", "text", label="Observations", comment="Section: Existence et exhaustivité de l’archivage des documents | col. EB"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aor_ft_allotissements


def define_all(db):
    """Définit `aor_ft_operations` puis sa sous-table `aor_ft_allotissements` (1-N)."""
    define_operations(db)
    define_allotissements(db)
    return db
