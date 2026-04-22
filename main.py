import json
import sys

from src.Analysis.statistiques import calculer_statistiques_globales
from src.Core.app_controller import AppController
from src.UI.affichage import (
    afficher_en_tete,
    afficher_statistiques_globales,
)
from src.UI.graphiques import (
    generer_camembert_provenance,
    generer_graphique_winrates,
)
from src.UI.menus import (
    afficher_menu_principal,
    lister_configurations_disponibles,
    menu_competition,
    menu_recherche_profil,
    selectionner_role,
    selectionner_sport,
)


def main() -> None:
    """Point d'entrée principal de l'application."""
    afficher_en_tete()

    selectionner_role()
    controller = AppController()
    configs = lister_configurations_disponibles()

    # Boucle de Niveau 0 : Choix du sport
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

            # Boucle de Niveau 1 : Le Menu interactif du sport
            while True:
                choix_menu = afficher_menu_principal()

                if choix_menu == "1":
                    menu_recherche_profil(controller)

                elif choix_menu == "2":
                    menu_competition(competition)

                elif choix_menu == "3":
                    liste_athletes = []
                    df_athletes = controller.loader.base_athletes

                    if not df_athletes.empty and 'objet' in df_athletes.columns:
                        liste_athletes = df_athletes['objet'].tolist()

                    print("\nAnalyse des données en cours...")
                    resultats_stats = calculer_statistiques_globales(competition, liste_athletes)
                    afficher_statistiques_globales(resultats_stats)

                elif choix_menu == "4":
                    print("\nPréparation des visualisations...")
                    liste_athletes = controller.loader.base_athletes['objet'].tolist()
                    resultats_stats = calculer_statistiques_globales(competition, liste_athletes)

                    generer_camembert_provenance(resultats_stats)
                    generer_graphique_winrates(resultats_stats)

                elif choix_menu == "9":
                    print("\nRetour à la sélection des sports...")
                    break

                elif choix_menu == "0":
                    print("\nFermeture des modules. Fin du programme.")
                    sys.exit()

                else:
                    print("Choix invalide. Veuillez réessayer.")

        except FileNotFoundError as e:
            print(f"\nErreur critique : Un fichier de données est manquant. {e}")
        except json.JSONDecodeError:
            print("\nErreur critique : Le fichier de configuration JSON est mal formé.")
        except KeyError as e:
            print(f"\nErreur technique : Une colonne attendue est manquante dans le CSV ou le JSON. Clé : {e}")
        except RuntimeError as e:
            print(f"\nUne erreur est survenue lors de l'exécution du traitement : {e}")


if __name__ == "__main__":
    main()
