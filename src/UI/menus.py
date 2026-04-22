import sys
from pathlib import Path

from src.Core.app_controller import AppController
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.UI.affichage import (
    afficher_details_match,
    afficher_profil,
    afficher_resultats_competition,
)


def demander_saisie(message: str) -> str:
    """
    Intercepte toutes les requêtes de l'utilisateur.
    Permet de quitter l'application instantanément (Douane).
    """
    choix = input(message).strip()
    if choix.lower() in ["q", "quitter", "exit", "quit"]:
        print("\n🛑 Interruption demandée. Fermeture immédiate de l'application. Au revoir !")
        sys.exit()
    return choix


def selectionner_role() -> str:
    """Gère l'authentification simplifiée de l'utilisateur."""
    print("\n--- AUTHENTIFICATION ---")
    print("1. Administrateur")
    print("2. Spectateur")

    choix = ""
    while choix not in ["1", "2"]:
        choix = demander_saisie("Veuillez sélectionner votre profil (1 ou 2) : ")
        if choix not in ["1", "2"]:
            print("Entrée invalide. Merci de saisir 1 ou 2.")

    role = "admin" if choix == "1" else "spectateur"
    print(f"Session établie en tant que : {role.upper()}")
    return role


def lister_configurations_disponibles(dossier_configs: str = "configs") -> list[Path]:
    """Scanne le répertoire de configuration pour identifier les sports supportés."""
    chemin = Path(dossier_configs)
    if not chemin.exists():
        print(f"Erreur critique : Le dossier '{dossier_configs}' est introuvable.")
        return []
    return sorted(chemin.glob("*.json"))


def selectionner_sport(fichiers: list[Path]) -> str | None:
    """Présente les sports disponibles et capture le choix de l'utilisateur."""
    if not fichiers:
        print("Aucune configuration de sport n'a été détectée.")
        return None

    print("\n--- CATALOGUE DES SPORTS ---")
    for i, fichier in enumerate(fichiers, 1):
        nom_sport = fichier.stem.replace("config_", "").replace("_", " ").capitalize()
        print(f"{i}. {nom_sport}")
    print("0. Quitter l'application")

    while True:
        choix_str = demander_saisie(f"\nSélectionnez un sport (0-{len(fichiers)}) : ")
        try:
            choix = int(choix_str)
            if choix == 0:
                return None
            if 1 <= choix <= len(fichiers):
                return fichiers[choix - 1].name
            print(f"Erreur : Merci de choisir un nombre entre 0 et {len(fichiers)}.")
        except ValueError:
            print("Erreur : Saisie numérique requise.")


def afficher_menu_principal() -> str:
    """Affiche les options du menu principal une fois un sport chargé."""
    print("\n" + "=" * 40)
    print("           MENU PRINCIPAL")
    print("=" * 40)
    print("1. Équipe / Joueur (Recherche & Profils)")
    print("2. Compétition (Classements & Matchs)")
    print("3. Statistiques Générales")
    print("4. Visualisations Graphiques")
    print("9. Changer de sport")
    print("0. Quitter l'application")

    return demander_saisie("\nVotre choix : ")


def menu_competition(competition: Competition) -> None:
    """Menu interactif dédié à l'exploration d'une compétition et de ses matchs."""
    while True:
        print("\n" + "-" * 40)
        print(f"   COMPÉTITION : {competition.nom.upper()}")
        print("-" * 40)
        print("1. Afficher le classement / palmarès")
        print("2. Voir la liste des matchs")

        a_des_sous_tournois = len(competition.sous_competitions) > 0
        if a_des_sous_tournois:
            print("3. Explorer un sous-tournoi")

        print("0. Retour")

        choix = demander_saisie("\nVotre choix : ")

        if choix == "1":
            afficher_resultats_competition(competition)

        elif choix == "2":
            print(f"\n--- Liste des matchs ({competition.nom}) ---")
            matchs_a_afficher = competition.liste_match

            if not matchs_a_afficher:
                if a_des_sous_tournois:
                    print("Information : Les matchs sont rangés dans les sous-tournois.")
                    print("Veuillez utiliser l'option '3' pour choisir un tournoi spécifique.")
                else:
                    print("Aucun match enregistré.")
                continue

            for i, match in enumerate(matchs_a_afficher, 1):
                if match.date and str(match.date).lower() != "none":
                    date_propre = str(match.date).split()[0].replace("-", "/")
                    affichage_date = f"[{date_propre}] "
                else:
                    affichage_date = ""

                statut_vainqueur = match.renvoyer_gagnant()

                noms_participants = [perf.participant.nom for perf in match.performances.values()]
                if len(noms_participants) == 2:
                    titre_match = f"{noms_participants[0]} vs {noms_participants[1]}"
                else:
                    titre_match = f"Match {match.id_match}"
                    if str(match.id_match) == str(match.date):
                        titre_match = "Affrontement"

                print(f"{i:3d}. {affichage_date}{titre_match} | 🏆 {statut_vainqueur}")

            choix_m = demander_saisie(
                "\nEntrez le numéro du match pour voir les stats détaillées (ou '0' pour retour) : "
            )
            try:
                idx = int(choix_m)
                if 1 <= idx <= len(matchs_a_afficher):
                    afficher_details_match(matchs_a_afficher[idx - 1])
                elif idx != 0:
                    print("Numéro invalide. Retour au menu.")
            except ValueError:
                print("Saisie invalide. Retour au menu.")

        elif choix == "3" and a_des_sous_tournois:
            noms_tournois = list(competition.sous_competitions.keys())
            print("\n--- Sous-tournois disponibles ---")
            for i, nom in enumerate(noms_tournois, 1):
                print(f"{i}. {nom}")

            try:
                choix_t = int(demander_saisie("\nChoisissez un numéro (0 pour annuler) : "))
                if 1 <= choix_t <= len(noms_tournois):
                    tournoi_choisi = competition.sous_competitions[noms_tournois[choix_t - 1]]
                    menu_competition(tournoi_choisi)
                elif choix_t != 0:
                    print("Numéro invalide.")
            except ValueError:
                print("Veuillez entrer un nombre.")

        elif choix == "0":
            break

        else:
            print("Choix invalide. Veuillez réessayer.")


def menu_recherche_profil(controller: AppController) -> None:
    """Menu interactif pour rechercher ou lister l'annuaire des équipes et joueurs."""
    while True:
        print("\n" + "=" * 40)
        print("   EXPLORATEUR : ÉQUIPES & JOUEURS")
        print("=" * 40)
        print("1. Rechercher par nom")
        print("2. Afficher l'annuaire des Équipes")
        print("3. Afficher l'annuaire des Joueurs")
        print("0. Retour au menu principal")

        choix_action = demander_saisie("\nVotre choix : ")

        if choix_action == "0":
            break

        resultats_globaux = []

        if choix_action == "1":
            recherche = demander_saisie("\nEntrez un nom : ")
            if len(recherche) < 2:
                print("Veuillez entrer au moins 2 caractères.")
                continue

            athletes = controller.searcher.chercher_athlete_par_nom(recherche)
            equipes = controller.searcher.chercher_equipe_par_nom(recherche)
            resultats_globaux = equipes + athletes

        elif choix_action == "2":
            df_equipes = controller.loader.base_equipes
            if not df_equipes.empty and "objet" in df_equipes.columns:
                resultats_globaux = df_equipes["objet"].tolist()

        elif choix_action == "3":
            df_athletes = controller.loader.base_athletes
            if not df_athletes.empty and "objet" in df_athletes.columns:
                resultats_globaux = df_athletes["objet"].tolist()

        else:
            print("Choix invalide.")
            continue

        total = len(resultats_globaux)
        if total == 0:
            print("\nInformation : Aucun résultat trouvé ou base de données vide pour cette catégorie.")
            continue

        print(f"\n--- Liste générée ({total} résultats) ---")
        for index, resultat in enumerate(resultats_globaux, 1):
            type_entite = "ÉQUIPE" if isinstance(resultat, Equipe) else "JOUEUR"
            print(f"{index:3d}. [{type_entite}] {resultat.nom}")

        choix_profil = demander_saisie("\nEntrez le numéro pour voir le profil (ou '0' pour annuler) : ")
        try:
            choix_idx = int(choix_profil)
            if 1 <= choix_idx <= total:
                objet_choisi = resultats_globaux[choix_idx - 1]
                afficher_profil(objet_choisi, controller.competition_actuelle)
            elif choix_idx != 0:
                print("Numéro invalide. Retour au menu.")
        except ValueError:
            print("Saisie invalide. Retour au menu.")
