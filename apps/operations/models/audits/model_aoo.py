# -*- coding: utf-8 -*-
"""
Modèle pyDAL — Mode de passation : AOO — Appel d'Offres Ouvert.

Fichier CENTRAL du mode AOO (issu de la grille ``1-Saisie_AOO_nv.xlsx``). Il
remplace et fusionne les anciens ``aoo_model.py`` (table ``mp_aoo``) et
``aoo_attributaire_model.py`` (table ``attributaire``).

Découpage aoo_operations / aoo_allotissements
---------------------------------------------
Tables PROPRES au mode AOO (préfixe ``aoo_``) : chaque mode de passation a son
modèle et son allotissement dédiés.

Source : ``workdir_files/aoo/base de données -aoo_vf.xlsx`` (feuille « Feuil1 »).
La 1re colonne liste les sections ; deux colonnes « Operation » / « lots »
indiquent, par un « oui », où chaque section atterrit :

  - ``aoo_operations``    : sections au niveau de l'opération (colonne Operation = oui).
  - ``aoo_allotissements``: sections renseignées PAR LOT (colonne lots = oui), reliées
                        à ``aoo_operations`` par une relation 1-N. Reprend les champs de
                        l'ancien modèle ``attributaire`` (section « Attributaire(s) »)
                        + toutes les autres sections marquées « lots ».

La table de référence ``nature_operation`` est définie en amont par
``table_parametres_models.define_all`` — elle n'est PAS redéfinie ici.

  label   : libellé exact de la sous-section
  comment : section d'origine + colonne Excel (traçabilité)
"""
from datetime import datetime, timezone

from pydal import Field

from ...common import auth


def _meta_fields():
    """Champs de traçabilité communs (soft delete + audit). Recréés à chaque
    table : un objet Field pydal ne peut pas être partagé entre tables."""
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
    """Définit la table `aoo_operations` (sections au niveau de l'opération) et la retourne."""
    db.define_table(
        "aoo_operations",
        # --- N° ---
        # Field("numero_ordre", "integer", label="N°", comment="Section: N° | col. A"),
        # --- Contrôleur ---
        Field("agent_dgmp", "string", label="Nom de l'Agent DGMP", comment="Section: Contrôleur | col. B"),
        # --- Date de contrôle ---
        Field("date_controle", "date", label="Date de contrôle", comment="Section: Date de contrôle | col. C"),
        # --- Ministère ---
        Field("ministere", "reference ministere", label="Ministère", comment="Section: Ministère | col. D"),
        # --- Autorité Contractante ---
        Field("autorite_contractante", "reference autorite_contractante", label="Autorité Contractante", comment="Section: Autorité Contractante | col. E"),
        # --- Personne Ressource ---
        Field("interlocuteur_ac", "string", label="Interlocuteur chez l'AC", comment="Section: Personne Ressource | col. F"),
        # --- Imputation Budgétaire ---
        Field("imputation_budgetaire", "integer", label="Imputation Budgétaire", comment="Section: Imputation Budgétaire | col. G"),
        # --- Montant de la dotation / du Crédit ---
        Field("montant_dotation_credit", "double", label="Montant", comment="Section: Montant de la dotation / du Crédit | col. H"),
        # --- Numéro de l'opération ---
        Field("n_bomp", "string", label="N° BOMP", comment="Section: Numéro de l'opération | col. I"),
        # --- Objet de l'Opération ---
        Field("objet_operation", "string", label="Objet de l'Opération", comment="Section: Objet de l'Opération | col. J"),
        # --- Nature de l'opération ---
        Field("nature_operation", "reference nature_operation", label="Nature de l'opération", comment="Section: Nature de l'opération | col. K"),
        Field("nature_operation_observation", "text", label="Observations", comment="Section: Nature de l'opération | col. L"),
        # --- Préparation du PPM ---
        Field("ppm_existence", "boolean", label="Existence du PPM", comment="Section: Préparation du PPM | col. M"),
        Field("ppm_existence_observation", "text", label="Observations", comment="Section: Préparation du PPM | col. N"),
        Field("ppm_respect", "boolean", label="Respect du PPM", comment="Section: Préparation du PPM | col. O"),
        Field("ppm_respect_observation", "text", label="Observations", comment="Section: Préparation du PPM | col. P"),
        # --- Opération réservée aux PME ---
        Field("operation_reservee_pme_constat", "boolean", label="Constat", comment="Section: Opération réservée aux PME | col. R"),
        Field("operation_reservee_pme_observations", "text", label="Observations", comment="Section: Opération réservée aux PME | col. S"),
        # --- Examen et validation du DAO par la DGMP ---
        Field("examen_validation_dao_dgmp_constat", "boolean", label="Constat", comment="Section: Examen et validation du DAO par la DGMP | col. T"),
        Field("examen_validation_dao_dgmp_date_reception", "date", label="Date de reception du DAO à la DGMP", comment="Section: Examen et validation du DAO par la DGMP | col. U"),
        Field("examen_validation_dao_dgmp_date_validation", "date", label="Date de validation du DAO", comment="Section: Examen et validation du DAO par la DGMP | col. V"),
        Field("examen_validation_dao_dgmp_observation", "text", label="Observations", comment="Section: Examen et validation du DAO par la DGMP | col. W"),
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
        Field("affich_resultat_trvx_cojo_constat", "boolean", label="Constat", comment="Section: Affichage des résultats des travaux de la COJO | col. BF"),
        Field("affich_resultat_trvx_cojo_respect_delai", "boolean", label="Respect du délai d'affichage", comment="Section: Affichage des résultats des travaux de la COJO | col. BG"),
        Field("affich_resultat_trvx_cojo_observation", "text", label="Observations", comment="Section: Affichage des résultats des travaux de la COJO | col. BH"),
        # --- Publication des résultats des travaux de la COJO ---
        Field("pub_resultat_trvx_cojo_constat", "boolean", label="Constat", comment="Section: Publication des résultats des travaux de la COJO | col. BI"),
        Field("pub_resultat_trvx_cojo_date", "date", label="Date de publication", comment="Section: Publication des résultats des travaux de la COJO | col. BJ"),
        Field("pub_resultat_trvx_cojo_support_pub", "string", label="Support de publication", comment="Section: Publication des résultats des travaux de la COJO | col. BK"),
        Field("pub_resultat_trvx_cojo_observation", "text", label="Observations", comment="Section: Publication des résultats des travaux de la COJO | col. BL"),
        # --- Exigence du quitus de non redevance dans le DAO ---
        Field("exigence_quitus_non_redevance_constat", "boolean", label="Constat", comment="Section: Exigence du quitus de non redevance dans le DAO | col. BX"),
        Field("exigence_quitus_non_redevance_observations", "text", label="Observations", comment="Section: Exigence du quitus de non redevance dans le DAO | col. BY"),
        # --- Situation d'exécution de la ligne budgetaire après passation ---
        Field("situation_execution_ligne_budgetaire_montant_disponible", "double", label="Montant disponible", comment="Section: Situation d'exécution de la ligne budgetaire après passation | col. CO"),
        # --- Temps total pour la conduite de l’opération ---
        Field("temps_total_operation_nb_jours", "integer", label="Nombre de jours", comment="Section: Temps total pour la conduite de l’opération | col. DP"),
        Field("temps_total_operation_observation", "text", label="Observations", comment="Section: Temps total pour la conduite de l’opération | col. DQ"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aoo_operations


def define_allotissements(db):
    """Définit la table `aoo_allotissements` (sections renseignées par lot) et la retourne.

    Relation 1-N : chaque opération porte un ou plusieurs allotissements (un par lot).
    Reprend les champs de l'ancien modèle `attributaire` + les sections marquées
    « lots » dans la grille.
    """
    db.define_table(
        "aoo_allotissements",
        Field("operation", "reference aoo_operations", label="Dossier opération", comment="Référence vers la table parente"),
        # Objet propre au lot — saisi dans la section « Opérations » du formulaire
        # (1 champ par lot si N>1 ; recopié de l'objet de l'opération si N=1).
        Field("objet_lot", "string", label="Objet du lot", comment="Objet du lot"),
        # Numéro du lot (1..N) — renseigné automatiquement par le contrôleur.
        Field("numero_lot", "integer", label="N° du lot", comment="Numéro du lot"),
        # --- Montant de l'estimation ---
        Field("montant_estimation", "integer", label="Montant", comment="Section: Montant de l'estimation | col. Q"),
        # --- Garantie de l'offre comprise entre 1 et 1,5% ---
        Field("garantie_offre_minimale", "decimal(14,2)", label="Garantie minimale 1%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. X"),
        Field("garantie_offre_maximale", "decimal(14,2)", label="Garantie maximale 1,5%", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. Y"),
        Field("garantie_offre_constat", "boolean", label="Constat", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. Z"),
        Field("garantie_offre_observation", "text", label="Observations", comment="Section: Garantie de l'offre comprise entre 1 et 1,5% | col. AA"),
        # --- Attributaire(s) ---
        Field("attributaire_nom", "string", label="Raison sociale", comment="Section: Attributaire(s) | col. AZ"),
        Field("attributaire_ncc", "string", label="NCC attributaire", comment="Section: Attributaire(s) | col. BA"),
        Field("attributaire_lot", "string", label="Lot", comment="Section: Attributaire(s) | col. BB"),
        # Objet du lot, recopié de la section « Opérations » (= objet de l'opération si lot unique).
        Field("attributaire_objet", "string", label="Objet", comment="Section: Attributaire(s) | col. BC"),
        Field("attributaire_montant", "double", label="Montant", comment="Section: Attributaire(s) | col. BD"),
        Field("attributaire_observation", "text", label="Observations", comment="Section: Attributaire(s) | col. BE"),
        # --- Notification des résultats aux attributaires ---
        Field("notification_resultats_attributaires_constat", "boolean", label="Constat", comment="Section: Notification des résultats aux attributaires | col. BM"),
        Field("notification_resultats_attributaires_date", "date", label="Date", comment="Section: Notification des résultats aux attributaires | col. BN"),
        Field("notification_resultats_attributaires_observations", "text", label="Observations", comment="Section: Notification des résultats aux attributaires | col. BO"),
        # --- Information des soumissionnaires non retenus ---
        Field("information_soumissionnaires_non_retenus_constat", "boolean", label="Constat", comment="Section: Information des soumissionnaires non retenus | col. BP"),
        Field("information_soumissionnaires_non_retenus_observations", "text", label="Observations", comment="Section: Information des soumissionnaires non retenus | col. BQ"),
        # --- Respect du délai de recours éventuels ---
        Field("respect_delai_recours_eventuels_constat", "boolean", label="Constat", comment="Section: Respect du délai de recours éventuels | col. BR"),
        Field("respect_delai_recours_eventuels_observations", "text", label="Observations", comment="Section: Respect du délai de recours éventuels | col. BS"),
        # --- Existence d’un marché ---
        Field("existence_marche_constat", "boolean", label="Constat", comment="Section: Existence d’un marché | col. BT"),
        Field("existence_marche_observations", "text", label="Observations", comment="Section: Existence d’un marché | col. BU"),
        # --- Production des pièces fiscales et sociales par l’attributaire ---
        Field("production_pieces_fiscales_sociales_constat", "boolean", label="Constat", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. BV"),
        Field("production_pieces_fiscales_sociales_observations", "text", label="Observations", comment="Section: Production des pièces fiscales et sociales par l’attributaire | col. BW"),
        # --- Conformité du contenu du marché ---
        Field("conformite_contenu_marche_constat", "boolean", label="Constat", comment="Section: Conformité du contenu du marché | col. BZ"),
        Field("conformite_contenu_marche_observations", "text", label="Observations", comment="Section: Conformité du contenu du marché | col. CA"),
        # --- Signature du marché par l’attributaire ---
        Field("signature_marche_attributaire_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’attributaire | col. CB"),
        Field("signature_marche_attributaire_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’attributaire | col. CC"),
        Field("signature_marche_attributaire_observations", "text", label="Observations", comment="Section: Signature du marché par l’attributaire | col. CD"),
        # --- Signature du marché par l’Autorité Contractante ---
        Field("signature_marche_autorite_contractante_constat", "boolean", label="Constat", comment="Section: Signature du marché par l’Autorité Contractante | col. CE"),
        Field("signature_marche_autorite_contractante_date_signature", "date", label="Date de signature", comment="Section: Signature du marché par l’Autorité Contractante | col. CF"),
        Field("signature_marche_autorite_contractante_observations", "text", label="Observations", comment="Section: Signature du marché par l’Autorité Contractante | col. CG"),
        # --- Signature par l’autorité compétente ---
        Field("signature_autorite_competente_constat", "boolean", label="Constat", comment="Section: Signature par l’autorité compétente | col. CH"),
        Field("signature_autorite_competente_observations", "text", label="Observations", comment="Section: Signature par l’autorité compétente | col. CI"),
        # --- Numérotation du marché ---
        Field("numerotation_marche_constat", "boolean", label="Constat", comment="Section: Numérotation du marché | col. CJ"),
        Field("numerotation_marche", "string", label="Numéro du marché", comment="Section: Numérotation du marché | col. CK"),
        Field("numerotation_marche_observation", "text", label="Observations", comment="Section: Numérotation du marché | col. CL"),
        # --- Montant du marché ---
        Field("montant_marche", "double", label="Montant", comment="Section: Montant du marché | col. CM"),
        # --- Ecart entre montant estimatif et montant attribué ---
        Field("ecart_entre_montant_estimatif", "double", label="Montant", comment="Section: Ecart entre montant estimatif et montant attribué | col. CN"),
        # --- Examen préalable à l'approbation ---
        Field("exam_prealable_approb_constat", "boolean", label="Constat", comment="Section: Examen préalable à l'approbation | col. CP"),
        Field("exam_prealable_approb_date_soumission", "date", label="Date de soumission du projet de marché à la DGMP", comment="Section: Examen préalable à l'approbation | col. CQ"),
        Field("exam_prealable_approb_date_validation", "date", label="Date de vaidation du projet de marché par la DGMP", comment="Section: Examen préalable à l'approbation | col. CR"),
        Field("exam_prealable_approb_observation", "text", label="Observations", comment="Section: Examen préalable à l'approbation | col. CS"),
        # --- Approbation du marché ---
        Field("approbation_marche_constat", "boolean", label="Constat", comment="Section: Approbation du marché | col. CT"),
        Field("approbation_marche_date", "date", label="Date d'approbation", comment="Section: Approbation du marché | col. CU"),
        Field("approbation_marche_observation", "text", label="Observations", comment="Section: Approbation du marché | col. CV"),
        # --- Autorité approbatrice ou organe approbateur compétent ---
        Field("organe_approbateur_constat", "boolean", label="Constat", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. CW"),
        Field("organe_approbateur_observation", "text", label="Observations", comment="Section: Autorité approbatrice ou organe approbateur compétent | col. CX"),
        # --- Notification de l’approbation du marché au titulaire ---
        Field("notif_approbation_titulaire_constat", "boolean", label="Constat", comment="Section: Notification de l’approbation du marché au titulaire | col. CY"),
        Field("notif_approbation_titulaire_date", "date", label="Date de reception par le titulaire", comment="Section: Notification de l’approbation du marché au titulaire | col. CZ"),
        Field("notif_approbation_titulaire_observation", "text", label="Observations", comment="Section: Notification de l’approbation du marché au titulaire | col. DA"),
        # --- Garantie de bonne exécution ---
        Field("garantie_bonne_execution_constat", "boolean", label="Constat", comment="Section: Garantie de bonne exécution | col. DB"),
        Field("garantie_bonne_execution_observations", "text", label="Observations", comment="Section: Garantie de bonne exécution | col. DC"),
        # --- Enregistrement du marché ---
        Field("enregistrement_marche_constat", "boolean", label="Constat", comment="Section: Enregistrement du marché | col. DD"),
        Field("enregistrement_marche_date", "date", label="Date d'enregistrement", comment="Section: Enregistrement du marché | col. DE"),
        Field("enregistrement_marche_observation", "text", label="Observations", comment="Section: Enregistrement du marché | col. DF"),
        # --- Transmission de 02 exemplaires du contrat à la DGMP ---
        Field("transmission_02_exemplaires_contrat_constat", "boolean", label="Constat", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DG"),
        Field("transmission_02_exemplaires_contrat_observations", "text", label="Observations", comment="Section: Transmission de 02 exemplaires du contrat à la DGMP | col. DH"),
        # --- Notification de l’ordre de service de démarrage ---
        Field("notif_ordre_demarrage_constat", "boolean", label="Constat", comment="Section: Notification de l’ordre de service de démarrage | col. DI"),
        Field("notif_ordre_demarrage_date_accuse_recept", "date", label="Date sur l'accusé de reception", comment="Section: Notification de l’ordre de service de démarrage | col. DJ"),
        Field("notif_ordre_demarrage_conforme", "boolean", label="Conforme", comment="Section: Notification de l’ordre de service de démarrage | col. DK"),
        Field("notif_ordre_demarrage_observation", "text", label="Observations", comment="Section: Notification de l’ordre de service de démarrage | col. DL"),
        # --- Existence et exhaustivité de l’archivage des documents ---
        Field("existence_exhaustivite_existence", "boolean", label="Existence", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DM"),
        Field("existence_exhaustivite_exhaustivite", "boolean", label="Exhaustivité", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DN"),
        Field("existence_exhaustivite_observation", "text", label="Observations", comment="Section: Existence et exhaustivité de l’archivage des documents | col. DO"),
        *_meta_fields(),
        migrate=True,
    )
    return db.aoo_allotissements


def define_all(db):
    """Définit la table `aoo_operations` puis sa sous-table `aoo_allotissements` (1-N).

    Les tables de référence (ministere, autorite_contractante, nature_operation…)
    sont définies en amont par ``table_parametres_models.define_all``.
    """
    define_operations(db)   # → db.aoo_operations
    define_allotissements(db)  # → db.aoo_allotissements
    return db
