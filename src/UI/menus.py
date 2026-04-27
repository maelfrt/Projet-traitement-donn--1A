import sys
from datetime import UTC, datetime
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


def afficher_menu_principal(role: str) -> str:
    """Affiche les options du menu principal une fois un sport chargé."""
    print("\n" + "=" * 40)
    print("           MENU PRINCIPAL")
    print("=" * 40)
    print("1. Équipe / Joueur (Recherche & Profils)")
    print("2. Compétition (Classements & Matchs)")
    print("3. Statistiques Générales")
    print("4. Visualisations Graphiques")

    if role == "admin":
        print("5. [Admin] Espace Administration")
    print("-" * 40)
    print("8. Changer de sport")
    print("9. À propos")
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
            demander_saisie("\nAppuyez sur Entrée pour continuer...")

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
                    demander_saisie("\nAppuyez sur Entrée pour continuer...")
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

            pseudo = getattr(resultat, "pseudo", None)

            if pseudo and str(pseudo).strip().lower() not in ["nan", "none", ""]:
                # Si le joueur a un pseudo, on l'affiche avec le nom
                affichage_nom = f"{resultat.nom} alias '{pseudo}'"
            else:
                # Sinon, juste le nom classique
                affichage_nom = resultat.nom

            print(f"{index:3d}. [{type_entite}] {affichage_nom}")

        choix_profil = demander_saisie("\nEntrez le numéro pour voir le profil (ou '0' pour annuler) : ")
        try:
            choix_idx = int(choix_profil)
            if 1 <= choix_idx <= total:
                objet_choisi = resultats_globaux[choix_idx - 1]

                matchs_recents = afficher_profil(objet_choisi, controller.competition_actuelle)

                if matchs_recents:
                    choix_m = demander_saisie("\nNuméro du match pour plus de détails (ou Entrée pour retour) : ")
                    if choix_m.isdigit():
                        idx_m = int(choix_m)
                        if 1 <= idx_m <= len(matchs_recents):
                            match_cible = matchs_recents[idx_m - 1][0]
                            afficher_details_match(match_cible)

                demander_saisie("\nAppuyez sur Entrée pour continuer...")

            elif choix_idx != 0:
                print("Numéro invalide. Retour au menu.")
        except ValueError:
            print("Saisie invalide. Retour au menu.")


def _saisir_date_valide(prompt: str, date_actuelle: str | None = None) -> str:
    """Demande une date à l'utilisateur et la valide strictement."""
    texte_complet = f"{prompt} [Actuel: {date_actuelle}] : " if date_actuelle else f"{prompt} : "
    while True:
        saisie = demander_saisie(texte_complet).strip()
        if date_actuelle and not saisie:
            return date_actuelle  # Mode édition : on garde la date si Entrée
        try:
            datetime.strptime(saisie, "%Y-%m-%d").replace(tzinfo=UTC)
            return saisie
        except ValueError:
            print("⚠️ Format invalide. Utilisez AAAA-MM-JJ (ex: 2024-05-12).")


def rechercher_participant(controller, type_attendu=None, nom_actuel=None):
    """Gère la recherche et la sélection d'un participant."""
    texte = f"Participant [Actuel: {nom_actuel}] - Nouveau nom : " if nom_actuel else "Nom du participant : "

    while True:
        saisie = demander_saisie(texte).strip()

        if nom_actuel and not saisie:
            return "GARDER_ACTUEL"
        if saisie.lower() == "q":
            return None

        resultats = controller.searcher.chercher_equipe_par_nom(saisie) + controller.searcher.chercher_athlete_par_nom(
            saisie
        )

        if type_attendu:
            resultats = [r for r in resultats if isinstance(r, type_attendu)]
            if not resultats:
                print(f"⚠️ Vous devez sélectionner un(e) {type_attendu.__name__}.")
                continue

        if not resultats:
            print("⚠️ Aucun résultat trouvé.")
            continue

        if len(resultats) == 1:
            return resultats[0]

        print("Plusieurs correspondances :")
        for idx, res in enumerate(resultats[:5], 1):
            print(f"{idx}. {res.nom}")

        choix = demander_saisie("Numéro : ")
        try:
            return resultats[int(choix) - 1]
        except (ValueError, IndexError):
            print("Numéro invalide.")


def menu_graphiques(controller: AppController, competition: Competition) -> None:
    """Menu interactif dédié aux visualisations Matplotlib."""
    from src.UI.graphiques import (
        generer_distribution_matchs,
        generer_nuage_points_stats,
        generer_radar_profil,
        generer_top_5_winrate,
    )

    match_exemple = None
    if competition.liste_match:
        match_exemple = competition.liste_match[0]
    else:
        for sous_comp in competition.sous_competitions.values():
            if sous_comp.liste_match:
                match_exemple = sous_comp.liste_match[0]
                break

    stats_numeriques = []

    if match_exemple and match_exemple.performances:
        premiere_perf = next(iter(match_exemple.performances.values()))

        for cle, valeur in premiere_perf.stats.items():
            try:
                float(valeur)
                stats_numeriques.append(cle)
            except (ValueError, TypeError):
                pass

    nb_stat_suffisant = len(stats_numeriques) >= 2

    while True:
        print("\n" + "=" * 40)
        print("      📊 CENTRE D'ANALYSE GRAPHIQUE")
        print("=" * 40)
        print("1. Top 5 : Meilleurs taux de victoire (Winrate)")
        print("2. Distribution des matchs")

        if nb_stat_suffisant:
            print("3. Analyse croisée : Corrélation entre 2 stats")
            print("4. Diagramme Radar d'un participant")
        else:
            print("-. Analyse croisée (Indisponible : min. 4 stats)")
            print("-. Profil du joueur (Indisponible : min. 4 stats)")
        print("0. Retour")

        type_graph = demander_saisie("\nVotre choix : ")

        if type_graph == "1":
            print("\n Génération du Top 5 Winrate...")
            generer_top_5_winrate(competition)
        elif type_graph == "2":
            print("\n Analyse de la répartition des matchs...")
            generer_distribution_matchs(competition)
        elif type_graph == "3" and nb_stat_suffisant:
            print("\n--- Configuration de l'analyse croisée ---")
            for i, stat in enumerate(stats_numeriques, 1):
                print(f"{i}. {stat.replace('_', ' ').capitalize()}")
            ix = demander_saisie("Numéro axe X : ")
            iy = demander_saisie("Numéro axe Y : ")

            if ix.isdigit() and iy.isdigit():
                idx_x, idx_y = int(ix) - 1, int(iy) - 1
                if 0 <= idx_x < len(stats_numeriques) and 0 <= idx_y < len(stats_numeriques):
                    generer_nuage_points_stats(competition, stats_numeriques[idx_x], stats_numeriques[idx_y])
                else:
                    print("Index invalide.")
            else:
                print("Saisie invalide.")
        elif type_graph == "4" and nb_stat_suffisant:
            print("\n--- Recherche du profil ---")
            participant = rechercher_participant(controller)
            if participant:
                print(f"\n Génération du diagramme radar pour : {participant.nom}...")
                generer_radar_profil(competition, participant.nom)
        elif type_graph == "0":
            break
        else:
            print("Option invalide ou indisponible.")


def _ui_saisir_nouveau_match(controller: AppController, competition: Competition) -> None:
    """Logique UI pour la saisie d'un nouveau résultat."""
    print("\n--- Création d'un résultat officiel ---")

    # Recherche d'un match "modèle" pour la structure des stats
    match_exemple = None
    if competition.liste_match:
        match_exemple = competition.liste_match[0]
    else:
        for sous_comp in competition.sous_competitions.values():
            if sous_comp.liste_match:
                match_exemple = sous_comp.liste_match[0]
                break

    if not match_exemple or not match_exemple.performances:
        print("\nErreur : Impossible de lire la structure des matchs pour ce sport.")
        return

    roles_attendus = list(match_exemple.performances.keys())
    liste_donnees_perf = []
    gagnant_trouve = False
    saisie_annulee = False
    type_entite_attendu = None

    for role in roles_attendus:
        print(f"\n--- Saisie pour le rôle : [{role}] ---")
        participant = rechercher_participant(controller, type_attendu=type_entite_attendu)

        if not participant:
            saisie_annulee = True
            break

        if not type_entite_attendu:
            type_entite_attendu = type(participant)

        print(f"✔️ Participant sélectionné : {participant.nom}")

        stats_modele = match_exemple.performances[role].stats
        stats_saisies = {}
        for nom_stat in stats_modele:
            nom_propre = nom_stat.replace("_", " ").capitalize()
            val_stat = demander_saisie(f"Valeur pour '{nom_propre}' : ")
            try:
                stats_saisies[nom_stat] = float(val_stat) if "." in val_stat else int(val_stat)
            except ValueError:
                stats_saisies[nom_stat] = val_stat

        est_gagnant = False
        if not gagnant_trouve:
            while True:
                reponse = demander_saisie(f"Est-ce que {participant.nom} a GAGNÉ ce match ? (O/N) : ").lower()
                if reponse in ["o", "oui", "y", "yes"]:
                    est_gagnant = True
                    gagnant_trouve = True
                    break
                elif reponse in ["n", "non", "no"]:
                    est_gagnant = False
                    break
                else:
                    print("Saisie invalide.")

        liste_donnees_perf.append(
            {"participant": participant, "role": role, "est_gagnant": est_gagnant, "stats": stats_saisies}
        )

    if not saisie_annulee and len(liste_donnees_perf) == len(roles_attendus):
        date_nouveau = _saisir_date_valide("\nDate du match (YYYY-MM-DD)")
        nom_tournoi_choisi = None

        if competition.sous_competitions:
            print("\n--- Sélection de la phase / sous-tournoi ---")
            liste_sous_comps = list(competition.sous_competitions.keys())
            for i, nom_sc in enumerate(liste_sous_comps, 1):
                print(f"{i}. {nom_sc}")
            print(f"{len(liste_sous_comps) + 1}. Créer une nouvelle phase/tournoi")
            print("0. Ajouter au classement global (Racine)")

            choix_cible = demander_saisie("\nOù voulez-vous enregistrer ce match ? (Numéro) : ")
            try:
                idx = int(choix_cible)
                if 1 <= idx <= len(liste_sous_comps):
                    nom_tournoi_choisi = liste_sous_comps[idx - 1]
                elif idx == len(liste_sous_comps) + 1:
                    nom_tournoi_choisi = demander_saisie("Nom du nouveau sous-tournoi : ")
            except ValueError:
                pass

        id_cree = controller.enregistrer_nouveau_match(date_nouveau, liste_donnees_perf, nom_tournoi_choisi)
        print(f"\n Match {id_cree} enregistré !")


def _ui_inscrire_participant(controller: AppController) -> None:
    """Logique UI pour l'inscription d'un athlète ou d'une équipe."""
    print("\n--- Inscription d'un nouveau participant ---")
    print("1. Joueur / Athlète\n2. Équipe")
    type_choix = demander_saisie("\nType (1 ou 2, ou '0' pour annuler) : ")

    if type_choix not in ["1", "2"]:
        return

    nom = demander_saisie("Nom complet : ").strip()
    if not nom:
        return

    prov = demander_saisie("Provenance (Entrée pour ignorer) : ").strip() or None
    equipe_choisie = None

    if type_choix == "1":
        # On délègue l'accès aux données via le controller/loader
        equipes = controller.loader.base_equipes["objet"].tolist() if not controller.loader.base_equipes.empty else []
        if equipes:
            print("\n--- Sélection de l'équipe ---")
            for i, eq in enumerate(equipes, 1):
                print(f"{i}. {eq.nom}")
            choix_eq = demander_saisie("\nNuméro d'équipe (ou Entrée pour agent libre) : ")
            if choix_eq.isdigit() and 1 <= int(choix_eq) <= len(equipes):
                equipe_choisie = equipes[int(choix_eq) - 1].nom

    nouvel_obj = controller.inscrire_participant(type_choix, nom, prov, equipe_choisie)
    if nouvel_obj:
        print(f"\n '{nouvel_obj.nom}' ajouté avec l'ID {nouvel_obj.id} !")


def _ui_gerer_match(controller: AppController) -> None:
    """Logique UI pour la modification ou suppression d'un match."""
    id_cible = demander_saisie("\nID du match à gérer : ").strip()
    match_trouve = controller.obtenir_match_par_id(id_cible)

    if not match_trouve:
        print("Match introuvable.")
        return

    print(f"\n✔️ Match : {match_trouve}")
    print("1. Modifier\n2. Supprimer\n0. Annuler")
    action = demander_saisie("\nChoix : ")

    if action == "1":
        print("\n--- Mode Édition ---")
        nouvelle_date = _saisir_date_valide("Nouvelle date", str(match_trouve.date).split()[0])

        if controller.modifier_match(id_cible, nouvelle_date, []):  # Exemple simplifié
            print("✅ Match mis à jour.")

    elif action == "2":
        if demander_saisie("Confirmer suppression (O/N) : ").lower() in ["o", "oui"] and (
            controller.supprimer_match(id_cible)
        ):
            print("✅ Match supprimé.")


def _ui_sauvegarder_donnees(controller: AppController) -> None:
    """Logique UI pour l'exportation CSV."""
    print("\n--- Sauvegarde des données ---")
    nom_f = demander_saisie("Nom du fichier (Entrée pour 'matchs_sauvegarde.csv') : ") or "matchs_sauvegarde.csv"

    succes, nb, msg = controller.sauvegarder_matchs(nom_f)
    if succes:
        print(f"✅ {nb} matchs exportés dans '{msg}' !")
    else:
        print(f"❌ Erreur : {msg}")


def menu_administration(controller: AppController, competition: Competition) -> None:
    """Espace réservé aux administrateurs (Vue simplifiée)."""

    # Mapping des actions pour éviter les gros blocs if/elif
    actions = {
        "1": lambda: _ui_saisir_nouveau_match(controller, competition),
        "2": lambda: _ui_inscrire_participant(controller),
        "3": lambda: _ui_gerer_match(controller),
        "4": lambda: _ui_sauvegarder_donnees(controller),
    }

    while True:
        print("\n" + "=" * 40)
        print("      ⚙️  ESPACE ADMINISTRATION")
        print("=" * 40)
        print("1. Saisir un nouveau résultat officiel")
        print("2. Inscrire un nouveau participant")
        print("3. Gérer un match (Modifier / Supprimer)")
        print("4. Sauvegarder les données (Export CSV)")
        print("0. Retour au menu principal")

        choix = demander_saisie("\nVotre choix : ")

        if choix == "0":
            break

        if choix in actions:
            actions[choix]()
        else:
            print("Choix invalide.")
