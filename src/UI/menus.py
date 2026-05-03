import sys
from pathlib import Path
from typing import Any

from src.Analysis.statistiques import calculer_statistiques_globales
from src.Core.app_controller import AppController
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.UI.affichage import (
    afficher_a_propos,
    afficher_bilan_historique,
    afficher_details_match,
    afficher_profil,
    afficher_resultats_competition,
    afficher_statistiques_globales,
)

# =============================================================================
#  OUTILS DE BASE (GESTION DES ENTRÉES)
# =============================================================================


def demander_saisie(message: str) -> str:
    """
    Capte une entrée clavier et permet de quitter proprement à tout moment.

    Cette fonction est le point de passage obligé pour chaque question posée
    à l'utilisateur. Elle centralise la gestion de l'arrêt du programme via 'q'.

    Parameters
    ----------
    message : str
        Le texte de la question à afficher à l'écran.

    Returns
    -------
    str
        Le texte saisi par l'utilisateur, nettoyé des espaces inutiles.
    """
    choix = input(message).strip()
    if choix.lower() in ["q", "quitter"]:
        print("\nArrêt du programme. Au revoir !")
        sys.exit(0)
    return choix


def lister_configurations_disponibles() -> list[Path]:
    """
    Scanne le dossier des configurations pour trouver les sports disponibles.

    Returns
    -------
    list[Path]
        Une liste de chemins vers les fichiers JSON trouvés dans 'configs/'.
    """
    dossier = Path("configs")
    return sorted(dossier.glob("*.json")) if dossier.exists() else []


# =============================================================================
#  INITIALISATION (AU LANCEMENT DU PROGRAMME)
# =============================================================================


def selectionner_role() -> str:
    """
    Définit si l'utilisateur est un simple spectateur ou un administrateur.

    Returns
    -------
    str
        'admin' ou 'spectateur' selon le choix effectué.
    """
    print("\n--- AUTHENTIFICATION ---")
    print("1. Administrateur")
    print("2. Spectateur")

    choix = ""
    while choix not in ["1", "2"]:
        choix = demander_saisie("Veuillez sélectionner votre profil (1 ou 2) : ")
    return "admin" if choix == "1" else "spectateur"


def selectionner_sport(fichiers: list[Path]) -> str | None:
    """
    Affiche la liste des sports et récupère le nom du fichier de configuration.

    Parameters
    ----------
    fichiers : list[Path]
        La liste des fichiers JSON disponibles.

    Returns
    -------
    str | None
        Le nom du fichier choisi (ex: 'config_football.json') ou None pour quitter.
    """
    if not fichiers:
        return None

    print("\n--- SPORTS DISPONIBLES ---")
    for i, f in enumerate(fichiers, 1):
        # On rend le nom du fichier joli (ex: config_basket.json -> Basket)
        nom = f.stem.replace("config_", "").replace("_", " ").capitalize()
        print(f"{i}. {nom}")
    print("0. Quitter")

    while True:
        s = demander_saisie("\nChoisir un numéro : ")
        if s == "0":
            return None
        if s.isdigit() and 1 <= int(s) <= len(fichiers):
            return fichiers[int(s) - 1].name
        print("\n❌ Saisie invalide : veuillez taper un numéro de la liste.")


# =============================================================================
#  NAVIGATION PRINCIPALE
# =============================================================================


def afficher_menu_principal(role: str, controller: AppController) -> str:
    """
    Affiche le menu de base de l'application de manière dynamique.

    La fonction interroge le contrôleur pour récupérer l'objet compétition
    actuellement chargé et extraire son nom. Elle adapte également
    l'affichage des options selon les droits d'accès de l'utilisateur.

    Parameters
    ----------
    role : str
        Le niveau de privilège de la session actuelle ('admin' ou 'spectateur').
    controller : AppController
        L'instance du contrôleur permettant d'accéder aux données en mémoire.

    Returns
    -------
    str
        Le caractère ou numéro saisi par l'utilisateur.
    """
    # Récupération de l'objet compétition actuel via le contrôleur
    competition_actuelle = controller.obtenir_resultats()
    nom_sport = competition_actuelle.nom.upper() if competition_actuelle else "INCONNU"

    print("\n" + "=" * 55)
    titre_menu = f"MENU PRINCIPAL : {nom_sport}"
    print(f"{titre_menu:^55}")
    print("=" * 55)

    print("1. Recherche de profil (Equipe & Joueur)")
    print("2. Consulter les résultats des matchs")
    print("3. Statistiques et records")
    print("4. Visualisations graphiques")

    if role == "admin":
        print("5. [ADMIN] Espace administration")

    print("-" * 55)
    print("8. Changer de sport")
    print("9. À propos")
    print("0. Quitter")

    return demander_saisie("\nVotre choix : ")


def executer_action_menu(choix: str, controller: AppController, role: str) -> bool:
    """
    Appelle la fonctionnalité correspondante au choix du menu principal.

    C'est ici que l'articulation se fait : la fonction récupère les données via le
    contrôleur et les envoie aux différents sous-menus pour traitement.

    Parameters
    ----------
    choix : str
        Le chiffre saisi par l'utilisateur.
    controller : AppController
        Le chef d'orchestre qui gère les données.
    role : str
        Le niveau d'accès de l'utilisateur.

    Returns
    -------
    bool
        True si on reste sur ce sport, False si on veut changer de sport (choix 8).
    """
    competition = controller.obtenir_resultats()

    if choix == "1":
        menu_recherche_profil(controller)
    elif choix == "2" and competition:
        menu_competition(competition, controller)
    elif choix == "3":
        menu_statistiques(controller)
    elif choix == "4" and competition:
        menu_graphiques(competition, controller)
    elif choix == "5" and role == "admin":
        menu_admin(controller)
    elif choix == "8":
        return False  # Indique au 'main.py' de remonter d'un niveau pour changer de sport
    elif choix == "9":
        afficher_a_propos()
        demander_saisie("Appuyez sur Entrée pour continuer...")
    elif choix == "0":
        sys.exit(0)
    else:
        print("\n❌ Saisie invalide.")
    return True


# =============================================================================
#  FONCTIONNALITÉS UTILISATEURS (CONSULTATION)
# =============================================================================


def menu_recherche_profil(controller: AppController) -> None:
    """
    Gère l'interface d'exploration et de recherche des participants.

    Cette fonction permet de lister les participants par catégorie ou de
    rechercher un nom précis. Elle coordonne l'affichage des fiches d'identité
    et des bilans statistiques de carrière.

    Parameters
    ----------
    controller : AppController
        L'instance du contrôleur central pour accéder aux données et aux calculs.

    Returns
    -------
    None
    """
    while True:
        # Récupération et tri des données via le contrôleur pour l'affichage initial
        tous_participants = controller.obtenir_tous_les_participants()
        equipes = sorted([e for e in tous_participants if isinstance(e, Equipe)], key=lambda x: str(x.nom))
        joueurs = sorted([e for e in tous_participants if not isinstance(e, Equipe)], key=lambda x: str(x.nom))

        print("\n" + "=" * 55)
        print(f"{'EXPLORATEUR : EQUIPES & JOUEURS':^55}")
        print("=" * 55)
        print("1. Rechercher par nom")

        # Attribution dynamique des chiffres pour éviter les trous dans le menu (passer de 1. à 3.)
        num_eq, num_jo, compteur = None, None, 2
        if equipes:
            print(f"{compteur}. Afficher la liste des équipes")
            num_eq, compteur = str(compteur), compteur + 1
        if joueurs:
            print(f"{compteur}. Afficher la liste des joueurs")
            num_jo = str(compteur)
        print("0. Retour au menu principal")

        choix = demander_saisie("\nVotre choix : ")
        if choix == "0":
            break

        # Traitement du choix utilisateur pour constituer la liste des résultats
        resultats_recherche = []

        if choix == "1":
            nom_saisi = demander_saisie("Nom à chercher : ")
            resultats_recherche = controller.rechercher_participants_par_nom(nom_saisi)
        elif num_eq and choix == num_eq:
            resultats_recherche = equipes
        elif num_jo and choix == num_jo:
            resultats_recherche = joueurs
        else:
            continue

        if not resultats_recherche:
            print("\nAucun résultat trouvé.")
            continue

        # Affichage de la liste des résultats numérotée pour la sélection
        for index, participant in enumerate(resultats_recherche, 1):
            print(f"{index:2d}. {participant.nom}")

        choix_numero = demander_saisie("\nNuméro pour voir le profil (0 pour retour) : ")

        # Validation de la saisie (vérification qu'il s'agit d'un nombre dans les bornes)
        if choix_numero.isdigit() and 1 <= int(choix_numero) <= len(resultats_recherche):
            # Extraction de l'objet ciblé (en ajustant l'index pour la base 0 des listes Python)
            participant_selectionne = resultats_recherche[int(choix_numero) - 1]

            # Le contrôleur compile les performances et le palmarès sur l'ensemble de la carrière
            moyennes_joueur = controller.calculer_moyennes_participant(participant_selectionne)
            palmares_obtenu = controller.calculer_palmares(participant_selectionne)

            # On affiche la fiche du profil avec les statistiques
            afficher_profil(participant_selectionne, palmares_obtenu, moyennes_joueur)

            # Récupération et affichage du tableau récapitulatif des victoires/défaites
            stats_bilan, matchs_historique = controller.calculer_bilan_historique(participant_selectionne)
            afficher_bilan_historique(participant_selectionne.nom, stats_bilan, matchs_historique)

            # Possibilité de consulter le détail technique d'un match de l'historique
            derniers_matchs_a_afficher = matchs_historique[:15]
            if derniers_matchs_a_afficher:
                while True:
                    m_num = demander_saisie("\nNuméro du match pour les stats (0 pour retour) : ")
                    if m_num == "0":
                        break
                    if m_num.isdigit() and 1 <= int(m_num) <= len(derniers_matchs_a_afficher):
                        match_obj = derniers_matchs_a_afficher[int(m_num) - 1].get("match")
                        if match_obj:
                            afficher_details_match(match_obj)


def menu_competition(competition: Competition, controller: AppController) -> None:
    """
    Gère la navigation dans la structure du tournoi.

    Si le tournoi est divisé en sous-groupes, elle propose de les explorer
    ou de consulter le Tableau Principal listé comme une option à part entière.

    Parameters
    ----------
    competition : Competition
        L'objet compétition ou sous-compétition à consulter.

    Returns
    -------
    None
    """
    # Cas où la section est totalement vide (aucune sous compétition, aucun match)
    if not competition.sous_competitions and not competition.liste_match:
        print(f"\n⚠️  Aucun match n'a encore été enregistré pour : {competition.nom}")
        demander_saisie("Appuyez sur Entrée pour continuer...")
        return

    # Si la compétition ne possède pas de sous compétitions, on affiche directement le contenu
    if not competition.sous_competitions:
        _afficher_contenu_competition(competition, controller)
        return

    # Boucle d'affichage pour les tournois contenant des sous compétitions
    while True:
        print("\n" + "=" * 55)
        print(f"{'Compétition : ' + competition.nom.upper():^55}")
        print("=" * 55)
        print("Ce tournoi est divisé en sous compétition")

        noms_phases = list(competition.sous_competitions.keys())

        # On liste d'abord l'intégralité des sections ou poules existantes
        for i, nom in enumerate(noms_phases, 1):
            print(f"{i}. {nom}")

        # Vérification intelligente : on n'affiche le Tableau Principal QUE s'il possède des matchs
        index_principal = len(noms_phases) + 1
        afficher_tableau_principal = len(competition.liste_match) > 0

        if afficher_tableau_principal:
            print(f"{index_principal}. Tableau Principal")

        print("0. Retour")

        choix_sc = demander_saisie("\nChoisissez une sous compétition : ")

        if choix_sc == "0":
            break
        elif choix_sc.isdigit():
            choix_int = int(choix_sc)

            # Cas où l'utilisateur sélectionne une section spécifique
            if 1 <= choix_int <= len(noms_phases):
                menu_competition(competition.sous_competitions[noms_phases[choix_int - 1]], controller)

            # Cas où l'utilisateur sélectionne le Tableau Principal (si l'option est active)
            elif afficher_tableau_principal and choix_int == index_principal:
                _afficher_contenu_competition(competition, controller)

            else:
                print("❌ Saisie invalide.")
        else:
            print("❌ Saisie invalide.")


def _afficher_contenu_competition(competition: Competition, controller: AppController) -> None:
    """
    Gère l'affichage du classement et la consultation détaillée des matchs.

    Cette sous-fonction a été séparée du menu de navigation pour isoler
    la logique d'affichage. Elle fait le lien entre les données de la
    compétition et les fonctions de dessin à l'écran.

    Parameters
    ----------
    competition : Competition
        L'objet précis dont on souhaite afficher les scores et l'historique.

    Returns
    -------
    None
    """
    while True:
        # On demande au module d'affichage de dessiner le tableau des scores
        moyennes_comp = controller.calculer_moyennes_competition(competition)
        afficher_resultats_competition(competition, moyennes_comp)

        print("1. Consulter la liste des matchs")
        print("0. Retour")

        choix_m = demander_saisie("\nVotre choix : ")

        if choix_m == "1":
            matchs = competition.liste_match

            # Vérification de sécurité avant d'afficher la liste
            if not matchs:
                print("⚠️  Aucun match enregistré dans cette catégorie.")
                continue

            print(f"\nMatchs de la phase : {competition.nom}")

            # On laisse l'objet Match gérer lui-même son affichage textuel
            for i, m in enumerate(matchs, 1):
                print(f"{i:2d}. {m}")

            num_match = demander_saisie("\nNuméro pour voir le score détaillé (0 pour retour) : ")
            if num_match.isdigit() and 1 <= int(num_match) <= len(matchs):
                # On ouvre la feuille de match complète avec toutes les statistiques
                afficher_details_match(matchs[int(num_match) - 1])
                demander_saisie("\nAppuyez sur Entrée pour continuer...")

        elif choix_m == "0":
            break
        else:
            print("❌ Saisie invalide.")


def menu_statistiques(controller: AppController) -> None:
    """
    Gère l'accès aux tableaux de bord analytiques et aux comparaisons directes.

    Ce menu oriente l'utilisateur vers des modules d'exploration des
    données agrégées, incluant l'extraction de records globaux ou la
    génération de l'historique des confrontations (Head-to-Head).

    Parameters
    ----------
    controller : AppController
        L'instance fournissant les méthodes de calcul statistique lourd.

    Returns
    -------
    None
    """
    while True:
        print("\n" + "=" * 55)
        print(f"{'📊 STATISTIQUES ET ANALYSES':^55}")
        print("=" * 55)
        print("1. Tableau de bord global (Records et Géographie)")
        print("2. Face-à-Face entre 2 particpants")
        print("0. Retour au menu principal")

        choix = demander_saisie("\nVotre choix : ")

        if choix == "1":
            comp = controller.obtenir_resultats()
            tous = controller.obtenir_tous_les_participants()
            if comp and tous:
                stats = calculer_statistiques_globales(comp, tous)

                # Calcul et transmission des moyennes sur le tournoi entier
                moyennes_glob = controller.calculer_moyennes_competition(comp)
                afficher_statistiques_globales(stats, moyennes_glob)

                demander_saisie("\nAppuyez sur Entrée pour continuer...")

        elif choix == "2":
            _sous_menu_face_a_face(controller)

        elif choix == "0":
            break
        else:
            print("❌ Saisie invalide.")


def _sous_menu_face_a_face(controller: AppController) -> None:
    """
    Pilote l'outil de comparaison directe (Head-to-Head) entre deux entités.

    Demande à l'utilisateur de sélectionner deux participants distincts
    (Joueur vs Joueur ou Équipe vs Équipe) via le moteur de recherche,
    puis sollicite le contrôleur pour extraire et analyser l'intersection
    de leurs historiques de matchs.

    Parameters
    ----------
    controller : AppController
        Le gestionnaire fournissant l'algorithme d'isolation des rencontres
        croisées (calculer_face_a_face).

    Returns
    -------
    None
    """
    print("\n--- ANALYSE FACE-À-FACE ---")

    # RECHERCHE DU PREMIER PARTICIPANT
    nom_p1 = demander_saisie("Entrez le nom du premier participant (ou 0 pour annuler) : ")
    if nom_p1 == "0":
        return

    trouves_1 = controller.rechercher_participants_par_nom(nom_p1)
    if not trouves_1:
        print("❌ Aucun participant trouvé.")
        return

    p1 = trouves_1[0]
    if len(trouves_1) > 1:
        print("\nPlusieurs résultats trouvés pour le participant 1 :")
        for i, p in enumerate(trouves_1, 1):
            print(f"{i}. {p.nom}")
        c = demander_saisie("Lequel ? (numéro) : ")
        if c.isdigit() and 1 <= int(c) <= len(trouves_1):
            p1 = trouves_1[int(c) - 1]

    # RECHERCHE DU DEUXIÈME PARTICIPANT
    nom_p2 = demander_saisie("Entrez le nom de son adversaire (ou 0 pour annuler) : ")
    if nom_p2 == "0":
        return

    trouves_2 = controller.rechercher_participants_par_nom(nom_p2)
    if not trouves_2:
        print("❌ Aucun adversaire trouvé.")
        return

    p2 = trouves_2[0]
    if len(trouves_2) > 1:
        print("\nPlusieurs résultats trouvés pour l'adversaire :")
        for i, p in enumerate(trouves_2, 1):
            print(f"{i}. {p.nom}")
        c = demander_saisie("Lequel ? (numéro) : ")
        if c.isdigit() and 1 <= int(c) <= len(trouves_2):
            p2 = trouves_2[int(c) - 1]

    # Sécurité : vérifier qu'on ne compare pas un joueur à lui-même
    if p1.id == p2.id:
        print("\n❌ Action impossible : vous devez sélectionner deux participants différents.")
        demander_saisie("Appuyez sur Entrée pour continuer...")
        return

    # EXÉCUTION DU CALCUL ET AFFICHAGE
    stats_h2h = controller.calculer_face_a_face(p1, p2)

    from src.UI.affichage import afficher_face_a_face

    afficher_face_a_face(p1, p2, stats_h2h)

    demander_saisie("\nAppuyez sur Entrée pour continuer...")


def menu_graphiques(competition: Competition, controller: AppController) -> None:
    """
    Gère l'interface de génération des visualisations visuelles (Matplotlib).

    Ce menu est dynamique : il s'adapte automatiquement à la complexité du sport
    qui a été chargé en mémoire. Il analyse les statistiques disponibles et bloque
    les graphiques trop complexes s'il n'y a pas assez de matière à tracer.

    Parameters
    ----------
    competition : Competition
        L'objet contenant l'ensemble des matchs à analyser.
    controller : AppController
        Le gestionnaire permettant d'utiliser le moteur de recherche de profils.

    Returns
    -------
    None
    """
    # Importation locale pour ne pas surcharger la mémoire si l'utilisateur
    # n'ouvre jamais le menu des graphiques.
    from src.UI.graphiques import (
        generer_distribution_matchs,
        generer_nuage_points_stats,
        generer_radar_profil,
        generer_top_5_winrate,
    )

    # On cherche dans l'ensemble des matchs pour lister toutes les catégories
    # de statistiques existantes (buts, passes, kills, rebonds, etc.)
    tous_les_matchs = competition.obtenir_tous_les_matchs()
    categories_stats_uniques: set[str] = set()

    for match in tous_les_matchs:
        for performance in match.performances.values():
            # La fonction update() ajoute les clés du dictionnaire au set sans créer de doublons
            categories_stats_uniques.update(performance.stats.keys())

    # On transforme le set en liste triée alphabétiquement pour un affichage élégant
    liste_des_statistiques = sorted(categories_stats_uniques)
    nb_stats_disponibles = len(liste_des_statistiques)

    # Boucle principale de l'interface
    while True:
        print("\n" + "=" * 55)
        print(f"{'📊 CENTRE ANALYSE GRAPHIQUE':^55}")
        print("=" * 55)
        print("1. Distribution globale des matchs (Histogramme)")
        print("2. Top 5 : Meilleurs taux de victoire (Winrate)")

        # Indicateur visuel pour prévenir l'utilisateur si une action est bloquée
        message_blocage = " (Indisponible : il faut au moins 4 stats)" if nb_stats_disponibles < 4 else ""
        print(f"3. Comparer deux statistiques croisées{message_blocage}")
        print(f"4. Générer le profil radar d'un participant{message_blocage}")
        print("0. Retour")

        choix_utilisateur = demander_saisie("\nChoix : ")

        # EXÉCUTION DES GRAPHIQUES SIMPLES
        if choix_utilisateur == "1":
            generer_distribution_matchs(competition)

        elif choix_utilisateur == "2":
            generer_top_5_winrate(competition)

        # SÉCURITÉ : VERROUILLAGE DES GRAPHIQUES COMPLEXES
        elif choix_utilisateur in ["3", "4"] and nb_stats_disponibles < 4:
            print(f"\n❌ Action impossible : ce sport ne possède que {nb_stats_disponibles} statistiques différentes.")
            print("Il en faut un minimum de 4 pour pouvoir générer ce type de graphique.")

        # EXÉCUTION DES GRAPHIQUES COMPLEXES
        elif choix_utilisateur == "3":
            print("\n--- CHOISISSEZ DEUX STATISTIQUES À COMPARER ---")
            for i, nom_stat in enumerate(liste_des_statistiques, 1):
                # On nettoie le nom "informatique" (ex: 'tirs_cadres' devient 'Tirs cadres')
                nom_propre = nom_stat.replace("_", " ").capitalize()
                print(f"{i}. {nom_propre}")

            choix_x = demander_saisie("Numéro pour l'axe horizontal (X) : ")
            choix_y = demander_saisie("Numéro pour l'axe vertical (Y) : ")

            if choix_x.isdigit() and choix_y.isdigit():
                index_x, index_y = int(choix_x) - 1, int(choix_y) - 1

                # Vérification que les numéros tapés existent bien dans la liste
                if 0 <= index_x < nb_stats_disponibles and 0 <= index_y < nb_stats_disponibles:
                    generer_nuage_points_stats(
                        competition, liste_des_statistiques[index_x], liste_des_statistiques[index_y]
                    )
                else:
                    print("❌ Saisie invalide : ce numéro de statistique n'existe pas.")
            else:
                print("❌ Saisie invalide : veuillez entrer des chiffres uniquement.")

        elif choix_utilisateur == "4":
            nom_recherche = demander_saisie("Entrez le nom du participant cible : ")
            # On cherche le participant via le contrôleur pour s'assurer qu'il existe
            resultats_trouves = controller.rechercher_participants_par_nom(nom_recherche)

            if not resultats_trouves:
                print("❌ Aucun participant trouvé avec ce nom.")
                continue

            print("\n--- SELECTIONNEZ LE PARTICIPANT ---")
            for i, participant in enumerate(resultats_trouves, 1):
                print(f"{i}. {participant.nom}")

            choix_participant = demander_saisie("Votre choix (0 pour annuler) : ")
            if choix_participant == "0":
                continue

            if choix_participant.isdigit() and 1 <= int(choix_participant) <= len(resultats_trouves):
                nom_participant_choisi = resultats_trouves[int(choix_participant) - 1].nom
                generer_radar_profil(competition, nom_participant_choisi)
            else:
                print("❌ Saisie invalide.")

        elif choix_utilisateur == "0":
            break

        else:
            print("\n❌ Saisie invalide : veuillez taper un chiffre entre 0 et 4.")


# =============================================================================
# ADMINISTRATION (GESTION DES DONNÉES)
# =============================================================================


def menu_admin(controller: AppController) -> None:
    """
    Affiche et gère le menu principal de l'espace administration.

    Cette fonction sert de point central pour toutes les actions de modification
    des données. Elle oriente l'utilisateur vers des sous-fonctions dédiées
    pour éviter de surcharger le code (principe de responsabilité unique).

    Parameters
    ----------
    controller : AppController
        Le gestionnaire principal permettant d'appliquer les modifications en mémoire.

    Returns
    -------
    None
    """
    while True:
        print("\n" + "=" * 55)
        print(f"{'⚙️  ESPACE ADMINISTRATION':^55}")
        print("=" * 55)
        print("1. Saisir un nouveau résultat officiel")
        print("2. Inscrire un nouveau participant")
        print("3. Gérer un match (Modifier / Supprimer)")
        print("4. Sauvegarder les données (Export CSV)")
        print("0. Retour au menu principal")

        choix = demander_saisie("\nVotre choix : ")

        # Orientation vers les sous-fonctions de traitement
        if choix == "1":
            _admin_saisir_resultat(controller)
        elif choix == "2":
            _admin_inscrire_participant(controller)
        elif choix == "3":
            _admin_gerer_match(controller)
        elif choix == "4":
            _admin_sauvegarder(controller)
        elif choix == "0":
            break
        else:
            print("❌ Saisie invalide : veuillez entrer un numéro entre 0 et 4.")


def _admin_saisir_resultat(controller: AppController) -> None:
    """
    Prend en charge la saisie d'un nouveau match de manière dynamique.

    L'interface demande au contrôleur quel est le modèle de données attendu
    pour le sport en cours (quelles statistiques demander, s'il faut chercher
    des équipes ou des joueurs). Elle construit ensuite le formulaire de saisie
    en temps réel avant de renvoyer les réponses au contrôleur pour enregistrement.

    Parameters
    ----------
    controller : AppController
        Le gestionnaire fournissant le modèle de saisie et validant les données.

    Returns
    -------
    None
    """
    print("\n--- SAISIR UN NOUVEAU RÉSULTAT ---")

    # Récupération du modèle de match défini par le contrôleur
    formulaire_attendu = controller.obtenir_structure_match_attendue()
    if not formulaire_attendu:
        print("❌ Impossible de déduire la structure des statistiques (aucun match existant).")
        demander_saisie("\nAppuyez sur Entrée pour continuer...")
        return

    # Saisie de la date avec délégation de la validation au contrôleur
    date_valide = None
    while not date_valide:
        saisie_date = demander_saisie("Date (YYYY-MM-DD) ou 0 pour annuler : ")
        if saisie_date == "0":
            return

        if controller.valider_et_convertir_date(saisie_date):
            date_valide = saisie_date.strip()
        else:
            print("❌ Format invalide. Veuillez respecter strictement le format YYYY-MM-DD.")

    # Détermination de l'emplacement du match dans l'arborescence du tournoi
    nom_groupe = None
    competition_actuelle = controller.obtenir_resultats()

    if competition_actuelle and competition_actuelle.sous_competitions:
        groupes_disponibles = list(competition_actuelle.sous_competitions.keys())
        print("\n0. Tournoi principal (Aucun groupe)")
        for index, nom in enumerate(groupes_disponibles, 1):
            print(f"{index}. {nom}")

        choix_groupe = demander_saisie("\nDans quel groupe ce match a-t-il été joué ? : ")
        if choix_groupe.isdigit() and 1 <= int(choix_groupe) <= len(groupes_disponibles):
            nom_groupe = groupes_disponibles[int(choix_groupe) - 1]

    # Remplissage des performances pour chaque rôle (ex: Domicile, Extérieur)
    liste_performances = []
    from src.Model.equipe import Equipe

    for role, configuration_role in formulaire_attendu.items():
        print(f"\n--- Saisie pour le rôle : {role.upper()} ---")

        # Adaptation du texte selon la nature du participant attendu
        nom_participant = "équipe" if configuration_role["est_equipe"] else "joueur"
        type_participant = f"l'{nom_participant}" if configuration_role["est_equipe"] else f"le {nom_participant}"
        participant_trouve = None

        # Boucle de recherche et de sélection du participant
        while not participant_trouve:
            nom_recherche = demander_saisie(f"Nom de {type_participant} (ou 0 pour annuler) : ")
            if nom_recherche == "0":
                return

            # Filtrage des résultats selon le type attendu par le contrôleur
            resultats_bruts = controller.rechercher_participants_par_nom(nom_recherche)
            if configuration_role["est_equipe"]:
                resultats_filtres = [p for p in resultats_bruts if isinstance(p, Equipe)]
            else:
                resultats_filtres = [p for p in resultats_bruts if not isinstance(p, Equipe)]

            if not resultats_filtres:
                # On utilise directement le mot pur !
                print(f"❌ Aucun(e) {nom_participant} trouvé(e).")
                continue

            if len(resultats_filtres) == 1:
                participant_trouve = resultats_filtres[0]
                print(f"✅ Sélection du participant : {participant_trouve.nom}")
            else:
                print("Plusieurs résultats :")
                for index, p in enumerate(resultats_filtres, 1):
                    print(f"{index}. {p.nom}")
                choix_participant = demander_saisie("Lequel ? (numéro) : ")
                if choix_participant.isdigit() and 1 <= int(choix_participant) <= len(resultats_filtres):
                    participant_trouve = resultats_filtres[int(choix_participant) - 1]
                else:
                    print("❌ Saisie invalide.")

        # Collecte des statistiques chiffrées ou textuelles
        statistiques_saisies: dict[str, Any] = {}
        for nom_stat, type_attendu in configuration_role["stats"].items():
            while True:
                valeur_saisie = demander_saisie(f"Valeur pour '{nom_stat}' : ")

                # Vérification du typage pour éviter les plantages futurs lors des calculs
                if type_attendu == "nombre":
                    try:
                        statistiques_saisies[nom_stat] = (
                            float(valeur_saisie) if "." in valeur_saisie else int(valeur_saisie)
                        )
                        break
                    except ValueError:
                        print("❌ Erreur : Vous devez entrer un nombre valide.")
                else:
                    statistiques_saisies[nom_stat] = valeur_saisie
                    break

        # Détermination stricte du vainqueur
        while True:
            reponse_victoire = demander_saisie("Est-ce le vainqueur du match ? (o/n) : ").lower()
            if reponse_victoire in ["o", "n"]:
                est_gagnant = reponse_victoire == "o"
                break
            print("❌ Réponse invalide. Tapez 'o' pour oui ou 'n' pour non.")

        # Compilation des données du participant pour ce match
        liste_performances.append(
            {"participant": participant_trouve, "role": role, "est_gagnant": est_gagnant, "stats": statistiques_saisies}
        )

    # Validation globale et transmission des données au cerveau de l'application
    if liste_performances and len(liste_performances) == len(formulaire_attendu):
        nouvel_id = controller.enregistrer_nouveau_match(date_valide, liste_performances, nom_groupe)
        print(f"\n✅ Match '{nouvel_id}' enregistré ! Les classements ont été recalculés.")
    else:
        print("\n❌ Saisie incomplète. L'enregistrement a été annulé.")

    demander_saisie("\nAppuyez sur Entrée pour continuer...")


def _admin_inscrire_participant(controller: AppController) -> None:
    """
    Interface d'ajout d'une nouvelle entité dans la base de données.

    Parameters
    ----------
    controller : AppController
        Le gestionnaire s'occupant de l'instanciation et de l'indexation.

    Returns
    -------
    None
    """
    print("\n--- INSCRIRE UN PARTICIPANT ---")
    type_participant = demander_saisie("Type (1 = Joueur, 2 = Équipe, 0 = Annuler) : ")

    if type_participant in ["1", "2"]:
        nom_saisi = demander_saisie("Nom complet du participant : ")
        provenance_saisie = demander_saisie("Provenance (Pays/Région) ou Entrée pour ignorer : ")

        # On délègue la création réelle de l'objet informatique au contrôleur
        nouvel_objet = controller.inscrire_participant(
            type_participant=type_participant,
            nom=nom_saisi,
            provenance=provenance_saisie if provenance_saisie else None,
        )

        if nouvel_objet:
            label = "L'équipe" if type_participant == "2" else "Le joueur"
            print(f"✅ Succès : {label} '{nouvel_objet.nom}' a été ajouté(e) en mémoire.")
    elif type_participant != "0":
        print("❌ Saisie invalide : veuillez choisir 1 ou 2.")

    if type_participant != "0":
        demander_saisie("\nAppuyez sur Entrée pour continuer...")


def _admin_gerer_match(controller: AppController) -> None:
    """
    Gère la recherche, la modification et la suppression d'un match existant.

    Au lieu de demander un identifiant technique complexe, l'interface propose
    de rechercher un participant, affiche son historique récent, et permet
    de sélectionner le match visuellemment avant d'appliquer les changements.

    Parameters
    ----------
    controller : AppController
        Le gestionnaire appliquant les modifications et recalculant le classement.

    Returns
    -------
    None
    """
    print("\n--- GÉRER UN MATCH ---")
    nom_recherche = demander_saisie("Entrez le nom d'un participant ayant joué le match : ")

    # Recherche du participant pour accéder à son historique
    resultats = controller.rechercher_participants_par_nom(nom_recherche)

    if not resultats:
        print("❌ Aucun participant trouvé à ce nom.")
        demander_saisie("\nAppuyez sur Entrée pour continuer...")
        return

    # On utilise le premier résultat trouvé pour afficher son historique
    participant_cible = resultats[0]
    _, historique = controller.calculer_bilan_historique(participant_cible)

    if not historique:
        print(f"❌ Aucun match enregistré pour {participant_cible.nom}.")
        demander_saisie("\nAppuyez sur Entrée pour continuer...")
        return

    print(f"\n--- Derniers matchs de {participant_cible.nom} ---")
    matchs_recents = historique[:20]
    for index, match_data in enumerate(matchs_recents, 1):
        print(f"{index:2d}. {match_data['match']}")

    choix_match = demander_saisie("\nNuméro du match à gérer (0 pour annuler) : ")

    if choix_match == "0" or not choix_match.isdigit() or not (1 <= int(choix_match) <= len(matchs_recents)):
        return

    # Récupération de l'objet Match caché derrière la sélection visuelle
    match_selectionne = matchs_recents[int(choix_match) - 1]["match"]
    id_match = str(match_selectionne.id_match)

    print(f"\nMatch sélectionné : {match_selectionne}")
    print("1. Supprimer définitivement ce match")
    print("2. Modifier la date du match")
    print("3. Modifier les statistiques (scores, vainqueur...)")
    print("0. Retour")

    action_choisie = demander_saisie("\nQue voulez-vous faire ? : ")

    if action_choisie == "1":
        confirmation = demander_saisie("⚠️ Êtes-vous sûr de vouloir supprimer ce match ? (o/n) : ")
        if confirmation.lower() == "o" and controller.supprimer_match(id_match):
            print("✅ Le match a été supprimé. Les classements ont été mis à jour.")
        else:
            print("❌ Suppression annulée ou échouée.")

    elif action_choisie == "2":
        nouvelle_date = demander_saisie("Nouvelle date (YYYY-MM-DD) ou 0 pour annuler : ")
        if nouvelle_date != "0":
            # Le contrôleur vérifie lui-même la validité de la date avant de l'appliquer
            if controller.modifier_match(id_match, nouvelle_date=nouvelle_date):
                print("✅ La date du match a été mise à jour avec succès.")
            else:
                print("❌ Format invalide. Veuillez respecter strictement YYYY-MM-DD.")

    elif action_choisie == "3":
        print("\n--- Participants du match ---")
        roles_disponibles = list(match_selectionne.performances.keys())
        for index, role in enumerate(roles_disponibles, 1):
            nom_participant = match_selectionne.performances[role].participant.nom
            print(f"{index}. {role} ({nom_participant})")

        choix_role = demander_saisie("\nNuméro du rôle à modifier (0 pour annuler) : ")

        if choix_role.isdigit() and 1 <= int(choix_role) <= len(roles_disponibles):
            role_cible = roles_disponibles[int(choix_role) - 1]
            performance_actuelle = match_selectionne.performances[role_cible]

            print(f"\n--- Modification de {performance_actuelle.participant.nom} ---")
            print("(Appuyez simplement sur Entrée pour conserver la valeur actuelle)")

            # Création du dictionnaire contenant uniquement les valeurs à modifier
            valeur_modifications: dict[str, Any] = {"stats": {}}

            for nom_stat, valeur_actuelle in performance_actuelle.stats.items():
                nouvelle_valeur = demander_saisie(f"Nouvelle valeur pour '{nom_stat}' (actuel: {valeur_actuelle}) : ")
                if nouvelle_valeur.strip() != "":
                    try:
                        valeur_modifications["stats"][nom_stat] = (
                            float(nouvelle_valeur) if "." in nouvelle_valeur else int(nouvelle_valeur)
                        )
                    except ValueError:
                        valeur_modifications["stats"][nom_stat] = nouvelle_valeur

            statut_victoire = "o" if performance_actuelle.est_gagnant else "n"
            nouveau_statut = demander_saisie(f"Est-ce le vainqueur ? (o/n, actuel: {statut_victoire}) : ")
            if nouveau_statut.lower() in ["o", "n"]:
                valeur_modifications["est_gagnant"] = nouveau_statut.lower() == "o"

            # Envoi du panier de modifications au contrôleur pour fusion et recalcul
            if controller.modifier_match(id_match, mises_a_jour_perfs={role_cible: valeur_modifications}):
                print("✅ Les statistiques ont été mises à jour avec succès.")
            else:
                print("❌ Erreur lors de la modification.")
        else:
            print("Annulé.")

    if action_choisie in ["1", "2", "3"]:
        demander_saisie("\nAppuyez sur Entrée pour continuer...")


def _admin_sauvegarder(controller: AppController) -> None:
    """
    Déclenche l'exportation des données de la mémoire vers un fichier physique.

    Parameters
    ----------
    controller : AppController
        Le gestionnaire gérant la communication avec les fichiers.

    Returns
    -------
    None
    """
    print("\n--- EXPORT CSV DES DONNÉES ---")
    nom_saisi = demander_saisie("Nom du fichier (ex: export_2024.csv) ou Entrée pour utiliser 'sauvegarde.csv' : ")

    # Sécurisation de l'extension du fichier
    if not nom_saisi:
        nom_saisi = "sauvegarde.csv"
    elif not nom_saisi.endswith(".csv"):
        nom_saisi += ".csv"

    # Appel au système d'infrastructure pour l'écriture dans les fichiers
    succes, nombre_matchs, message_retour = controller.sauvegarder_matchs(nom_saisi)

    if succes:
        print(f"✅ Succès : {nombre_matchs} matchs ont été sécurisés dans le fichier '{message_retour}'.")
    else:
        print(f"❌ Erreur lors de la sauvegarde : {message_retour}")

    demander_saisie("\nAppuyez sur Entrée pour continuer...")
