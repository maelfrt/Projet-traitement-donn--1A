import json
import sys

from src.Analysis.statistiques import calculer_statistiques_globales
from src.Core.app_controller import AppController
from src.UI.affichage import (
    afficher_a_propos,
    afficher_en_tete,
    afficher_statistiques_globales,
)
from src.UI.graphiques import (
    generer_distribution_matchs,
    generer_nuage_points_stats,
    generer_radar_profil,
    generer_top_5_winrate,
)
from src.UI.menus import (
    afficher_menu_principal,
    lister_configurations_disponibles,
    menu_administration,
    menu_competition,
    menu_recherche_profil,
    rechercher_participant,
    selectionner_role,
    selectionner_sport,
)


def main() -> None:
    """Point d'entrée principal de l'application."""
    afficher_en_tete()

    role_utilisateur = selectionner_role()
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
                choix_menu = afficher_menu_principal(role_utilisateur)

                if choix_menu == "1":
                    menu_recherche_profil(controller)

                elif choix_menu == "2":
                    menu_competition(competition)

                elif choix_menu == "3":
                    liste_athletes = []
                    df_athletes = controller.loader.base_athletes
                    if not df_athletes.empty and "objet" in df_athletes.columns:
                        liste_athletes = df_athletes["objet"].tolist()

                    liste_equipes = []
                    df_equipes = controller.loader.base_equipes
                    if not df_equipes.empty and "objet" in df_equipes.columns:
                        liste_equipes = df_equipes["objet"].tolist()

                    toutes_entites = liste_athletes + liste_equipes

                    print("\nAnalyse des données en cours...")
                    resultats_stats = calculer_statistiques_globales(competition, toutes_entites)
                    afficher_statistiques_globales(resultats_stats)

                elif choix_menu == "4":
                    match_exemple = None
                    if competition.liste_match:
                        match_exemple = competition.liste_match[0]
                    else:
                        for sous_comp in competition.sous_competitions.values():
                            if sous_comp.liste_match:
                                match_exemple = sous_comp.liste_match[0]
                                break

                    stats_disponibles = []
                    if match_exemple and match_exemple.performances:
                        premiere_perf = next(iter(match_exemple.performances.values()))
                        stats_disponibles = list(premiere_perf.stats.keys())

                    print("\n" + "=" * 40)
                    print("      📊 CENTRE D'ANALYSE GRAPHIQUE")
                    print("=" * 40)
                    print("1. Top 5 : Meilleurs taux de victoire (Winrate)")
                    print("2. Distribution des matchs")

                    nb_stat_suffisant = len(stats_disponibles) > 3
                    if nb_stat_suffisant:
                        print("3. Analyse croisée : Corrélation entre 2 stats")
                        print("4. Diagramme Radar d'un participant")
                    else:
                        print("-. Analyse croisée (Indisponible : min. 4 stats)")
                        print("-. Profil du joueur (Indisponible : min. 4 stats)")

                    print("0. Retour")

                    type_graph = input("\nVotre choix : ").strip()

                    if type_graph == "1":
                        print("\n Génération du Top 5 Winrate...")
                        generer_top_5_winrate(competition)

                    elif type_graph == "2":
                        print("\n Analyse de la répartition des matchs...")
                        generer_distribution_matchs(competition)

                    elif type_graph == "3":
                        if not nb_stat_suffisant:
                            print("Option indisponible.")
                            continue

                        print("\n--- Configuration de l'analyse croisée ---")
                        for i, stat in enumerate(stats_disponibles, 1):
                            print(f"{i}. {stat.replace('_', ' ').capitalize()}")
                        ix = input("Numéro X : ").strip()
                        iy = input("\nNuméro Y : ").strip()

                        if ix.isdigit() and iy.isdigit():
                            idx_x, idx_y = int(ix) - 1, int(iy) - 1
                            if 0 <= idx_x < len(stats_disponibles) and 0 <= idx_y < len(stats_disponibles):
                                generer_nuage_points_stats(
                                    competition, stats_disponibles[idx_x], stats_disponibles[idx_y]
                                )
                            else:
                                print("Index invalide.")
                        else:
                            print("Saisie invalide.")

                    elif type_graph == "4":
                        if not nb_stat_suffisant:
                            print("Option indisponible.")
                            continue

                        print("\n--- Recherche du profil ---")
                        participant = rechercher_participant(controller)

                        if participant:
                            print(f"\n Génération du diagramme radar pour : {participant.nom}...")
                            generer_radar_profil(competition, participant.nom)
                        else:
                            print("\nOpération annulée.")

                    elif type_graph == "0":
                        continue

                elif choix_menu == "5" and role_utilisateur == "admin":
                    menu_administration(controller, competition)

                elif choix_menu == "8":
                    print("\nRetour à la sélection des sports...")
                    break

                elif choix_menu == "9":
                    afficher_a_propos()

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
