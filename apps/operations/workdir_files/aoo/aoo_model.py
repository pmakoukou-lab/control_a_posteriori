# -*- coding: utf-8 -*-
"""
Modèle pyDAL — Mode de passation : AOO — Appel d'Offres Ouvert
Source : 1-Saisie_AOO_nv.xls  (feuille « Nouv »)
Tables : réf: nature_operation | mp_aoo + attributaire  (120 champs au total).

  label   : libellé exact de la sous-section
  comment : section d'origine + colonne Excel (traçabilité)
"""
from pydal import Field
from pydal.validators import IS_IN_SET


def define_nature_operation(db):
    """Table de référence `nature_operation`."""
    db.define_table(
        "nature_operation",
        Field("operation_nom", "string", label="Operation nom"),
        Field("operation_code", "string", label="Operation code"),
        format="%(operation_nom)s",
        migrate=True,
    )
    return db.nature_operation

def seed_nature_operation(db):
    """Insère les valeurs de référence si la table est vide."""
    if db(db.nature_operation).isempty():
        for _r in [
            dict(operation_nom="Travaux", operation_code="trv"),
            dict(operation_nom="Fournitures", operation_code="frt"),
            dict(operation_nom="Prestations", operation_code="prt"),
        ]:
            db.nature_operation.insert(**_r)
        db.commit()


def define_mp_aoo(db):
    """Définit la table `mp_aoo` et la retourne."""
    db.define_table(
        "mp_aoo",
        # --- N° ---
        Field("numero_ordre", "integer", label="N°", comment="Section: N° | col. A"),
        # --- Contrôleur ---
        Field("agent_dgmp", "string", label="Nom de l'Agent DGMP", comment="Section: Contrôleur | col. B"),
        # --- Date de contrôle ---
        Field("date_controle", "date", label="Date de contrôle", comment="Section: Date de contrôle | col. C"),
        # --- Ministère ---
        Field("ministere", "string", label="Ministère", comment="Section: Ministère | col. D"),
        # --- Autorité Contractante ---
        Field("autorite_contractante", "string", label="Autorité Contractante", comment="Section: Autorité Contractante | col. E"),
        # --- Personne Ressource ---
        Field("interlocuteur_ac", "string", label="Interlocuteur chez l'AC", comment="Section: Personne Ressource | col. F"),
        # --- Imputation Budgétaire ---
        Field("imputation_budgetaire", "string", label="Imputation Budgétaire", comment="Section: Imputation Budgétaire | col. G"),
        # --- Montant de la dotation / du Crédit ---
        Field("montant_dotation_credit", "double", label="Montant", comment="Section: Montant de la dotation / du Crédit | col. H"),
        # --- Numéro de l'opération ---
        Field("n_aoo", "string", label="N° de l'AOO", comment="Section: Numéro de l'opération | col. I"),
        # --- Objet de l'Opération ---
        Field("objet_operation", "string", label="Objet de l'Opération", comment="Section: Objet de l'Opération | col. J"),
        # --- Nature de l'opération ---
        Field("nature_operation", "reference nature_operation", label="Travaux/ Fournitures/ Prestations", comment="Section: Nature de l'opération | col. K"),
        Field("nature_operation_observation", "text", label="Observations", comment="Section: Nature de l'opération | col. L"),
        # --- Préparation du PPM ---
        Field("ppm_existence", "boolean", label="Existence du PPM", comment="Section: Préparation du PPM | col. M"),
        Field("ppm_existence_observation", "text", label="Observations", comment="Section: Préparation du PPM | col. N"),
        Field("ppm_respect", "boolean", label="Respect du PPM", comment="Section: Préparation du PPM | col. O"),
        Field("ppm_respect_observation", "text", label="Observations", comment="Section: Préparation du PPM | col. P"),
        # --- Montant de l'estimation ---
        Field("montant_estimation", "double", label="Montant", comment="Section: Montant de l'estimation | col. Q"),
        # --- Opération réservée aux PME ---
        Field("operation_reservee_pme_constat", "boolean", label="Constat", comment="Section: Opération réservée aux PME | col. R"),
        Field("operation_reservee_pme_observations", "text", label="Observations", comment="Section: Opération réservée aux PME | col. S"),
        # --- Examen et validation du DAO par la DGMP ---
        Field("examen_validation_dao_dgmp_constat", "boolean", label="Constat", comment="Section: Examen et validation du DAO par la DGMP | col. T"),
        Field("examen_validation_dao_dgmp_date_reception", "date", label="Date de reception du DAO à la DGMP", comment="Section: Examen et validation du DAO par la DGMP | col. U"),
        Field("examen_validation_dao_dgmp_date_validation", "date", label="Date de validation du DAO", comment="Section: Examen et validation du DAO par la DGMP | col. V"),
        Field("examen_validation_dao_dgmp_observation", "text", label="Observations", comment="Section: Examen et validation du DAO par la DGMP | col. W"),
        # --- Garantie de l'offre comprise entre 1 et 1,5% ---
        Field("garantie_offre_minimale", "decimal(14,2)", label="Garantie minimale 1%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. X"),
        Field("garantie_offre_maximale", "decimal(14,2)", label="Garantie maximale 1,5%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. Y"),
        Field("garantie_offre_constat", "boolean", label="Constat", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. Z"),
        Field("garantie_offre_observation", "text", label="Observations", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AA"),
        # --- Publication de l'avis d'appel d'offres (AAO) ---
        Field("publication_aao_constat", "boolean", label="Constat", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AB"),
        Field("publication_aao_date", "date", label="Date de publication", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AC"),
        Field("publication_aao_num", "string", label="Numéro de l'Avis d'Appel d'Offres", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AD"),
        Field("publication_aao_duree", "integer", label="Durée de publication", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AE"),
        Field("publication_aao_nb_report", "integer", label="Nombre de reports", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AF"),
        Field("publication_aao_observation", "text", label="Observations", comment="Section: Publication de l'avis d'appel d'offres (AAO) | col. AG"),
        # --- Existence de la COJO ---
        Field("existence_cojo_conformite", "boolean", label="Conformité", comment="Section: Existence de la COJO | col. AH"),
        Field("existence_cojo_observations", "text", label="Observations", comment="Section: Existence de la COJO | col. AI"),
        # --- Existence des mandats des répresentants des membres de la COJO ---
        Field("existence_mandats_representants_membres_constat", "boolean", label="Constat", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AJ"),
        Field("existence_mandats_representants_membres_observations", "text", label="Observations", comment="Section: Existence des mandats des répresentants des membres de la COJO | col. AK"),
        # --- Existence du procès-verbal d’ouverture des plis ---
        Field("existence_pv_ouv_exist", "boolean", label="Existence du PV", comment="Section: Existence du procès-verbal d’ouverture des plis | col. AL"),
        Field("existence_pv_ouv_obs", "text", label="Observations", comment="Section: Existence du procès-verbal d’ouverture des plis | col. AM"),
        # --- Existence du rapport d’analyse des offres ---
        Field("existence_rapport_analyse_offres", "boolean", label="Existence du rapport", comment="Section: Existence du rapport d’analyse des offres | col. AN"),
        Field("existence_rapport_analyse_offres_observations", "text", label="Observations", comment="Section: Existence du rapport d’analyse des offres | col. AO"),
        # --- Existence de la COJO au jugement ---
        Field("existence_cojo_jugement_conformite", "boolean", label="Conformité", comment="Section: Existence de la COJO au jugement | col. AP"),
        Field("existence_cojo_jugement_observations", "text", label="Observations", comment="Section: Existence de la COJO au jugement | col. AQ"),
        # --- Existence du procès-verbal de jugement des offres ---
        Field("existence_pv_jug_exist", "boolean", label="Existence du PV", comment="Section: Existence du procès-verbal de jugement des offres | col. AR"),
        Field("existence_pv_jug_obs", "text", label="Observations", comment="Section: Existence du procès-verbal de jugement des offres | col. AS"),
        # --- Délai imparti à la COJO pour ses travaux ---
        Field("delai_impart_cojo_trvx_date_ouv", "date", label="Date d'ouverture", comment="Section: Délai imparti à la COJO pour ses travaux | col. AT"),
        Field("delai_impart_cojo_trvx_date_jug", "date", label="Date de jugement", comment="Section: Délai imparti à la COJO pour ses travaux | col. AU"),
        Field("delai_impart_cojo_trvx_dern_recours", "date", label="Date de dernier jugement en cas de recours", comment="Section: Délai imparti à la COJO pour ses travaux | col. AV"),
        Field("delai_impart_cojo_trvx_nb_jug", "integer", label="Nombre de jugements", comment="Section: Délai imparti à la COJO pour ses travaux | col. AW"),
        Field("delai_impart_cojo_trvx_respect_delai", "boolean", label="Respect du délai", comment="Section: Délai imparti à la COJO pour ses travaux | col. AX"),
        Field("delai_impart_cojo_trvx_observation", "text", label="Observations", comment="Section: Délai imparti à la COJO pour ses travaux | col. AY"),
        # --- Affichage des résultats des travaux de la COJO ---
        Field("affich_resultat_trvx_cojo_constat", "boolean", label="Constat", comment="Section: Affichage des résultats des travaux de la COJO | col. BE"),
        Field("affich_resultat_trvx_cojo_respect_delai", "boolean", label="Respect du délai d'affichage", comment="Section: Affichage des résultats des travaux de la COJO | col. BF"),
        Field("affich_resultat_trvx_cojo_observation", "text", label="Observations", comment="Section: Affichage des résultats des travaux de la COJO | col. BG"),
        # --- Publication des résultats des travaux de la COJO ---
        Field("pub_resultat_trvx_cojo_constat", "boolean", label="Constat", comment="Section: Publication des résultats des travaux de la COJO | col. BH"),
        Field("pub_resultat_trvx_cojo_date", "date", label="Date de publication", comment="Section: Publication des résultats des travaux de la COJO | col. BI"),
        Field("pub_resultat_trvx_cojo_support_pub", "string", label="Support de publication", comment="Section: Publication des résultats des travaux de la COJO | col. BJ"),
        Field("pub_resultat_trvx_cojo_observation", "text", label="Observations", comment="Section: Publication des résultats des travaux de la COJO | col. BK"),
        # --- Notification des résultats aux attributaires ---
        Field("notification_resultats_attributaires_constat", "boolean", label="Constat", comment="Section: Notification des résultats aux attributaires | col. BL"),
        Field("notification_resultats_attributaires_date", "date", label="Date", comment="Section: Notification des résultats aux attributaires | col. BM"),
        Field("notification_resultats_attributaires_observations", "text", label="Observations", comment="Section: Notification des résultats aux attributaires | col. BN"),
        # --- Information des soumissionnaires non retenus ---
        Field("information_soumissionnaires_non_retenus_constat", "boolean", label="Constat", comment="Section: Information des soumissionnaires non retenus | col. BO"),
        Field("information_soumissionnaires_non_retenus_observations", "text", label="Observations", comment="Section: Information des soumissionnaires non retenus | col. BP"),
        # --- Respect du délai de recours éventuels ---
        Field("respect_delai_recours_eventuels_constat", "boolean", label="Constat", comment="Section: Respect du délai de recours éventuels | col. BQ"),
        Field("respect_delai_recours_eventuels_observations", "text", label="Observations", comment="Section: Respect du délai de recours éventuels | col. BR"),
        # --- Existence d’un marché ---
        Field("existence_marche_constat", "boolean", label="Constat", comment="Section: Existence d’un marché | col. BS"),
        Field("existence_marche_observations", "text", label="Observations", comment="Section: Existence d’un marché | col. BT"),
        # --- Production des pièces fiscales et sociales par l’attributaire ---
        Field("production_pieces_fiscales_sociales_constat", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. BU"),
        Field("production_pieces_fiscales_sociales_observations", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. BV"),
        # --- Exigence du quitus de non redevance dans le DAO ---
        Field("exigence_quitus_non_redevance_constat", "boolean", label="Constat", comment="Section: Exigence du quitus de non redevance dans le DAO | col. BW"),
        Field("exigence_quitus_non_redevance_observations", "text", label="Observations", comment="Section: Exigence du quitus de non redevance dans le DAO | col. BX"),
        # --- Conformité du contenu du marché ---
        Field("conformite_contenu_marche_constat", "boolean", label="Constat", comment="Section: Conformité du contenu du marché | col. BY"),
        Field("conformite_contenu_marche_observations", "text", label="Observations", comment="Section: Conformité du contenu du marché | col. BZ"),
        # --- Signature du marché par l’attributaire ---
        Field("signature_marche_attributaire_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’attributaire | col. CA"),
        Field("signature_marche_attributaire_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’attributaire | col. CB"),
        Field("signature_marche_attributaire_observations", "text", label="Observations", comment="Section: Signature du marché par l’attributaire | col. CC"),
        # --- Signature du marché par l’Autorité Contractante ---
        Field("signature_marche_autorite_contractante_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’Autorité Contractante | col. CD"),
        Field("signature_marche_autorite_contractante_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’Autorité Contractante | col. CE"),
        Field("signature_marche_autorite_contractante_observations", "text", label="Observations", comment="Section: Signature du marché par l’Autorité Contractante | col. CF"),
        # --- Signature par l’autorité compétente ---
        Field("signature_autorite_competente_constat", "boolean", label="Constat", comment="Section: Signature par l’autorité compétente | col. CG"),
        Field("signature_autorite_competente_observations", "text", label="Observations", comment="Section: Signature par l’autorité compétente | col. CH"),
        # --- Numérotation du marché ---
        Field("numerotation_marche_constat", "boolean", label="Constat", comment="Section: Numérotation du marché | col. CI"),
        Field("numerotation_marche", "string", label="Numéro du marché", comment="Section: Numérotation du marché | col. CJ"),
        Field("numerotation_marche_observation", "text", label="Observations", comment="Section: Numérotation du marché | col. CK"),
        # --- Montant du marché ---
        Field("montant_marche", "double", label="Montant", comment="Section: Montant du marché | col. CL"),
        # --- Ecart entre montant estimatif et montant attribué ---
        Field("ecart_entre_montant_estimatif", "double", label="Montant", comment="Section: Ecart entre montant estimatif et montant attribué | col. CM"),
        # --- Situation d'exécution de la ligne budgetaire après passation ---
        Field("situation_execution_ligne_budgetaire_montant_disponible", "double", label="Montant disponible", comment="Section: Situation d'exécution de la ligne budgetaire après passation | col. CN"),
        # --- Examen préalable à l'approbation ---
        Field("exam_prealable_approb_constat", "boolean", label="Constat", comment="Section: Examen préalable à l'approbation | col. CO"),
        Field("exam_prealable_approb_date_soumission", "date", label="Date de soumission du projet de marché à la DGMP", comment="Section: Examen préalable à l'approbation | col. CP"),
        Field("exam_prealable_approb_date_validation", "date", label="Date de vaidation du projet de marché par la DGMP", comment="Section: Examen préalable à l'approbation | col. CQ"),
        Field("exam_prealable_approb_observation", "text", label="Observations", comment="Section: Examen préalable à l'approbation | col. CR"),
        # --- Approbation du marché ---
        Field("approbation_marche_constat", "boolean", label="Constat", comment="Section: Approbation du marché | col. CS"),
        Field("approbation_marche_date", "date", label="Date d'approbation", comment="Section: Approbation du marché | col. CT"),
        Field("approbation_marche_observation", "text", label="Observations", comment="Section: Approbation du marché | col. CU"),
        # --- Autorité approbatrice ou organe approbateur compétent ---
        Field("organe_approbateur_constat", "boolean", label="Constat", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. CV"),
        Field("organe_approbateur_observation", "text", label="Observations", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. CW"),
        # --- Notification de l’approbation du marché au titulaire ---
        Field("notif_approbation_titulaire_constat", "boolean", label="Constat", comment="Section: Notification de l’approbation du marché au titulaire | col. CX"),
        Field("notif_approbation_titulaire_date", "date", label="Date de reception par le titulaire", comment="Section: Notification de l’approbation du marché au titulaire | col. CY"),
        Field("notif_approbation_titulaire_observation", "text", label="Observations", comment="Section: Notification de l’approbation du marché au titulaire | col. CZ"),
        # --- Garantie de bonne exécution ---
        Field("garantie_bonne_execution_constat", "boolean", label="Constat", comment="Section: Garantie de bonne exécution | col. DA"),
        Field("garantie_bonne_execution_observations", "text", label="Observations", comment="Section: Garantie de bonne exécution | col. DB"),
        # --- Enregistrement du marché ---
        Field("enregistrement_marche_constat", "boolean", label="Constat", comment="Section: Enregistrement du marché | col. DC"),
        Field("enregistrement_marche_date", "date", label="Date d'enregistrement", comment="Section: Enregistrement du marché | col. DD"),
        Field("enregistrement_marche_observation", "text", label="Observations", comment="Section: Enregistrement du marché | col. DE"),
        # --- Transmission de 02 exemplaires du contrat à la DGMP ---
        Field("transmission_02_exemplaires_contrat_constat", "boolean", label="Constat", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DF"),
        Field("transmission_02_exemplaires_contrat_observations", "text", label="Observations", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DG"),
        # --- Notification de l’ordre de service de démarrage ---
        Field("notif_ordre_demarrage_constat", "boolean", label="Constat", comment="Section: Notification de l’ordre de service de démarrage | col. DH"),
        Field("notif_ordre_demarrage_date_accuse_recept", "date", label="Date sur l'accusé de reception", comment="Section: Notification de l’ordre de service de démarrage | col. DI"),
        Field("notif_ordre_demarrage_conforme", "boolean", label="Conforme", comment="Section: Notification de l’ordre de service de démarrage | col. DJ"),
        Field("notif_ordre_demarrage_observation", "text", label="Observations", comment="Section: Notification de l’ordre de service de démarrage | col. DK"),
        # --- Existence et exhaustivité de l’archivage des documents ---
        Field("existence_exhaustivite_existence", "boolean", label="Existence", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DL"),
        Field("existence_exhaustivite_exhaustivite", "boolean", label="Exhaustivité", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DM"),
        Field("existence_exhaustivite_observation", "text", label="Observations", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DN"),
        # --- Temps total pour la conduite de l’opération ---
        Field("temps_total_operation_nb_jours", "integer", label="Nombre de jours", comment="Section: Temps total pour la conduite de l’opération | col. DO"),
        Field("temps_total_operation_observation", "text", label="Observations", comment="Section: Temps total pour la conduite de l’opération | col. DP"),
        migrate=True,
    )
    return db.mp_aoo


def define_attributaire(db):
    """Définit la table `attributaire` et la retourne."""
    db.define_table(
        "attributaire",
        Field("mp_aoo", "reference mp_aoo", label="Dossier mp_aoo", comment="Référence vers la table parente"),
        # --- Attributaire(s) ---
        Field("attributaire_nom", "string", label="Raison sociale", comment="Section: Attributaire(s) | col. AZ"),
        Field("attributaire_ncc", "string", label="NCC attributaire", comment="Section: Attributaire(s) | col. BA"),
        Field("attributaire_lot", "string", label="Lot", comment="Section: Attributaire(s) | col. BB"),
        Field("attributaire_montant", "double", label="Montant", comment="Section: Attributaire(s) | col. BC"),
        Field("attributaire_observation", "text", label="Observations", comment="Section: Attributaire(s) | col. BD"),
        migrate=True,
    )
    return db.attributaire


def define_all(db):
    """Définit les tables de référence, la table principale, puis les tables enfants."""
    define_nature_operation(db)
    define_mp_aoo(db)
    define_attributaire(db)
    seed_nature_operation(db)
    return db