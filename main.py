import sys

from src.Core.app_controller import AppController
from src.UI.affichage import afficher_en_tete
from src.UI.menus import (
    afficher_menu_principal,
    executer_action_menu,
    lister_configurations_disponibles,
    selectionner_role,
    selectionner_sport,
)


def main() -> None:
    """
    Point d'entrée principal de l'application.
    Gère la boucle d'exécution globale et l'initialisation du programme.
    """
    afficher_en_tete()

    # Définition des droits d'accès (Admin ou Spectateur)
    role_utilisateur = selectionner_role()

    # Initialisation du contrôleur (qui gèrera toutes les données)
    controller = AppController()
    configs = lister_configurations_disponibles()

    # Boucle principale de l'application
    while True:
        # Sélection de la base de données (le fichier JSON du sport)
        config_choisie = selectionner_sport(configs)

        # Si l'utilisateur choisit l'option de sortie (0)
        if not config_choisie:
            print("\nFermeture du gestionnaire sportif. À bientôt !")
            sys.exit(0)

        try:
            # Demande au contrôleur de charger les CSV et de calculer les classements
            print("\nChargement et traitement des données en cours...")
            controller.executer_chargement_complet(config_choisie)

            # Boucle du menu pour le sport actuellement chargé
            rester_sur_ce_sport = True
            while rester_sur_ce_sport:
                # Affichage des choix possibles
                choix_menu = afficher_menu_principal(role_utilisateur, controller)

                # On délègue l'exécution à notre fichier menus.py.
                # Si l'utilisateur choisit '8' (Changer de sport), la fonction renvoie False
                # ce qui casse la boucle "while" et nous ramène au choix du sport.
                rester_sur_ce_sport = executer_action_menu(choix_menu, controller, role_utilisateur)

        except OSError as erreur:
            # Rattrapage d'erreur propre si un fichier CSV ou JSON est manquant/corrompu
            print(f"\n[Erreur Système] Impossible de lire les fichiers de données : {erreur}")
            print("Veuillez vérifier que vos fichiers sont bien présents dans le dossier.")


# Condition standard en Python pour exécuter le programme
if __name__ == "__main__":
    main()
