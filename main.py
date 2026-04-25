import sys

from src.Analysis.statistiques import calculer_statistiques_globales
from src.Core.app_controller import AppController
from src.UI.affichage import afficher_a_propos, afficher_en_tete, afficher_statistiques_globales
from src.UI.menus import (
    afficher_menu_principal,
    lister_configurations_disponibles,
    menu_administration,
    menu_competition,
    menu_graphiques,
    menu_recherche_profil,
    selectionner_role,
    selectionner_sport,
)


def main() -> None:
    """Point d'entrée principal de l'application."""
    afficher_en_tete()

    role_utilisateur = selectionner_role()
    controller = AppController()
    configs = lister_configurations_disponibles()

    while True:
        config_choisie = selectionner_sport(configs)

        if not config_choisie:
            print("\nArrêt du programme. Fin de session.")
            sys.exit()

        try:
            print("\nTraitement des données en cours...")
            controller.executer_chargement_complet(config_choisie)
            competition = controller.obtenir_resultats()

            if not competition:
                print("Erreur : Impossible de charger les résultats.")
                continue

            while True:
                choix_menu = afficher_menu_principal(role_utilisateur)

                if choix_menu == "1":
                    menu_recherche_profil(controller)

                elif choix_menu == "2":
                    menu_competition(competition)

                elif choix_menu == "3":
                    toutes_entites = controller.obtenir_tous_les_participants()

                    print("\nAnalyse des données en cours...")
                    resultats_stats = calculer_statistiques_globales(competition, toutes_entites)
                    afficher_statistiques_globales(resultats_stats)
                    input("\nAppuyez sur Entrée pour retourner au menu principal...")

                elif choix_menu == "4":
                    menu_graphiques(controller, competition)

                elif choix_menu == "5" and role_utilisateur == "admin":
                    menu_administration(controller, competition)

                elif choix_menu == "8":
                    print("\nRetour à la sélection des sports...")
                    break

                elif choix_menu == "9":
                    afficher_a_propos()
                    input("\nAppuyez sur Entrée pour retourner au menu principal...")

                elif choix_menu == "0":
                    print("\nFermeture des modules. Fin du programme.")
                    sys.exit()

                else:
                    print("Choix invalide. Veuillez réessayer.")

        except OSError as e:
            print(f"\nUne erreur critique est survenue : {e}")


if __name__ == "__main__":
    main()
