import json
import sys
from pathlib import Path

from src.Parsers.manager import Manager


def afficher_en_tete() -> None:
    """Affiche le titre de l'application."""
    print("=" * 50)
    print("APPLICATION DE TRAITEMENT DE DONNEES SPORTIVES")
    print("=" * 50)


def choisir_role() -> str:
    """Demande à l'utilisateur de s'identifier."""
    print("\n[ IDENTIFICATION ]")
    print("1. Administrateur")
    print("2. Utilisateur (Consultation)")

    choix = ""
    while choix not in ["1", "2"]:
        choix = input("Choisissez votre profil (1 ou 2) : ")
        if choix not in ["1", "2"]:
            print("Erreur : Veuillez entrer 1 ou 2.")

    if choix == "1":
        return "admin"
    return "user"


def obtenir_sports_disponibles(dossier_configs: str = "configs") -> dict[int, dict[str, str]]:
    """
    Scanne le dossier des configurations pour lister les sports disponibles.
    Retourne un dictionnaire du type : { 1: {"nom": "Tennis (ATP)", "fichier": "config_tennis.json"} }
    """
    chemin_configs = Path(dossier_configs)
    sports_dispo: dict[int, dict[str, str]] = {}

    if not chemin_configs.exists():
        print(f"[ERREUR] Le dossier '{dossier_configs}' est introuvable.")
        return sports_dispo

    index = 1
    for fichier in chemin_configs.glob("*.json"):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                config = json.load(f)
                nom_sport = config.get("sport")

                if nom_sport:
                    sports_dispo[index] = {
                        "nom": nom_sport,
                        "fichier": fichier.name
                    }
                    index += 1
        except Exception:
            # Si un fichier JSON est mal formaté, on l'ignore simplement
            pass

    return sports_dispo


def choisir_sport(sports_dispo: dict[int, dict[str, str]]) -> str:
    """Affiche la liste des sports et demande à l'utilisateur d'en choisir un."""
    if not sports_dispo:
        print("\nAucun sport n'est configuré pour le moment.")
        sys.exit()

    print("\n[ SPORTS DISPONIBLES ]")
    for numero, donnees in sports_dispo.items():
        print(f"{numero}. {donnees['nom']}")

    print("0. Quitter l'application")

    choix_num = -1
    while choix_num not in sports_dispo and choix_num != 0:
        try:
            saisie = input(f"Sélectionnez un sport (0 à {len(sports_dispo)}) : ")
            choix_num = int(saisie)

            if choix_num == 0:
                print("Fermeture de l'application. À bientôt !")
                sys.exit()

            if choix_num not in sports_dispo:
                print("Erreur : Ce numéro ne correspond à aucun sport.")

        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide.")

    return sports_dispo[choix_num]["fichier"]


def main() -> None:
    """Point d'entrée principal de l'application."""
    afficher_en_tete()

    # Identification
    role = choisir_role()
    print(f"-> Connecté en tant que : {role.upper()}")

    # Récupération  des sports
    sports_dispo = obtenir_sports_disponibles()
    fichier_json_choisi = choisir_sport(sports_dispo)

    # Lancement du Manager avec le sport choisi
    print("\n" + "-" * 50)
    mon_manager = Manager()
    competition = mon_manager.charger_sport(fichier_json_choisi)
    print("-" * 50)

    total = len(mon_manager.athletes_globaux)
    print("--- RÉSUMÉ ---")
    print(f"Nombre total d'athlètes en mémoire : {total}")
    mon_manager.afficher_resultats(competition)

    # TODO : Afficher les menus spécifiques selon le rôle (Admin ou User)
    print("\n[ MENU PRINCIPAL ]")
    print(f"La compétition '{competition}' est chargée en mémoire.")
    print("La suite du menu arrive bientôt...")


# Cette condition vérifie que le script est lancé directement (et non importé)
if __name__ == "__main__":
    main()
