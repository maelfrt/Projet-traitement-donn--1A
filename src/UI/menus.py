import sys
import time as time_module
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.Core.app_controller import AppController
from src.Infrastructure.gestionnaire_csv import (
    GestionnaireCSV,
)
from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance
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
                afficher_profil(objet_choisi, controller.competition_actuelle)
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


def menu_administration(controller: AppController, competition: Competition) -> None:
    """Espace réservé aux administrateurs pour manipuler les données."""
    while True:
        print("\n" + "=" * 40)
        print("      ⚙️  ESPACE ADMINISTRATION")
        print("=" * 40)
        print("1. Saisir un nouveau résultat officiel")
        print("2. Inscrire un nouveau participant (Joueur / Équipe)")
        print("3. Gérer un match (Modifier / Supprimer)")
        print("4. Sauvegarder les données (Export CSV)")
        print("0. Retour au menu principal")

        choix = demander_saisie("\nVotre choix : ")

        # =========================================================
        # 1. SAISIR UN NOUVEAU MATCH
        # =========================================================
        if choix == "1":
            print("\n--- Création d'un résultat officiel ---")

            # Trouver un match "modèle" pour copier sa structure
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
                continue

            roles_attendus = list(match_exemple.performances.keys())

            performances_a_creer = {}
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

                # Saisie des statistiques
                stats_modele = match_exemple.performances[role].stats
                stats_saisies = {}

                for nom_stat in stats_modele:
                    nom_propre = nom_stat.replace("_", " ").capitalize()
                    val_stat = demander_saisie(f"Valeur pour '{nom_propre}' : ")
                    try:
                        stats_saisies[nom_stat] = float(val_stat) if "." in val_stat else int(val_stat)
                    except ValueError:
                        stats_saisies[nom_stat] = val_stat

                # Saisie du gagnant
                est_gagnant = False
                if not gagnant_trouve:
                    while True:
                        reponse = (
                            demander_saisie(f"Est-ce que {participant.nom} a GAGNÉ ce match ? (O/N) : ").strip().lower()
                        )
                        if reponse in ["o", "oui", "y", "yes"]:
                            est_gagnant = True
                            gagnant_trouve = True
                            break
                        elif reponse in ["n", "non", "no"]:
                            est_gagnant = False
                            break
                        else:
                            print(" Saisie invalide. Veuillez répondre par 'O' ou 'N'.")

                performances_a_creer[role] = Performance(
                    participant, role=role, est_gagnant=est_gagnant, stats=stats_saisies
                )

            if not saisie_annulee and len(performances_a_creer) == len(roles_attendus):
                id_nouveau = f"M-{int(time_module.time())}"

                date_nouveau = _saisir_date_valide("\nDate du match (YYYY-MM-DD)")

                nouveau_match = Match(id_match=id_nouveau, date=date_nouveau)
                for role, perf in performances_a_creer.items():
                    nouveau_match.ajouter_performance(role, perf)

                # Gestion du sous-tournoi
                tournoi_cible = competition
                if competition.sous_competitions:
                    print("\n--- Sélection de la phase / sous-tournoi ---")
                    liste_sous_comps = list(competition.sous_competitions.keys())
                    for i, nom_sc in enumerate(liste_sous_comps, 1):
                        print(f"{i}. {nom_sc}")
                    print(f"{len(liste_sous_comps) + 1}.  Créer une nouvelle phase/tournoi")
                    print("0. Ajouter au classement global (Racine)")

                    choix_cible = demander_saisie("\nOù voulez-vous enregistrer ce match ? (Numéro) : ")
                    try:
                        idx = int(choix_cible)
                        if 1 <= idx <= len(liste_sous_comps):
                            tournoi_cible = competition.sous_competitions[liste_sous_comps[idx - 1]]
                        elif idx == len(liste_sous_comps) + 1:
                            nom_nouveau = demander_saisie("Nom du nouveau sous-tournoi (ex: Poule D) : ")
                            tournoi_cible = competition.obtenir_ou_creer_sous_comp(nom_nouveau)
                    except ValueError:
                        print("Saisie non reconnue, ajout au classement global par défaut.")

                tournoi_cible.ajouter_match(nouveau_match)
                controller.ranker.generer_classement(competition)

                print(f"\n Match {id_nouveau} enregistré dans '{tournoi_cible.nom}' !")
                print(" Le classement global et les profils ont été mis à jour.")

        # =========================================================
        # 2. INSCRIRE UN PARTICIPANT
        # =========================================================
        elif choix == "2":
            print("\n--- Inscription d'un nouveau participant ---")
            print("1. Joueur / Athlète")
            print("2. Équipe")

            type_choix = demander_saisie("\nType de participant (1 ou 2, ou '0' pour annuler) : ")

            if type_choix == "0":
                continue
            elif type_choix not in ["1", "2"]:
                print("Choix invalide.")
                continue

            nom = ""
            while not nom:
                nom = demander_saisie("Nom complet : ").strip()

            prov = demander_saisie("Provenance (Pays/Ville - Entrée pour ignorer) : ").strip()
            if not prov:
                prov = None

            prefixe = "P" if type_choix == "1" else "E"
            nouveau_id = f"{prefixe}-{int(time_module.time())}"
            nouvel_objet = None

            if type_choix == "1":
                equipe_choisie = None

                equipes_disponibles = (
                    controller.loader.base_equipes["objet"].tolist()
                    if hasattr(controller.loader, "base_equipes") and not controller.loader.base_equipes.empty
                    else []
                )

                if equipes_disponibles:
                    print("\n--- Sélection de l'équipe actuelle ---")
                    for idx, eq in enumerate(equipes_disponibles, 1):
                        print(f"{idx}. {eq.nom}")
                    print(f"{len(equipes_disponibles) + 1}.  Aucune (Agent libre)")

                    choix_eq = demander_saisie(f"\nChoisir l'équipe pour {nom} (Numéro) : ")
                    try:
                        idx_sel = int(choix_eq)
                        if 1 <= idx_sel <= len(equipes_disponibles):
                            equipe_choisie = equipes_disponibles[idx_sel - 1].nom
                    except ValueError:
                        print("Saisie non reconnue, considéré comme agent libre.")
                else:
                    print("\nAucune équipe n'est encore enregistrée dans le système.")

                nouvel_objet = Athlete(nom=nom, id_personne=nouveau_id, provenance=prov, equipe_actuelle=equipe_choisie)
                nouvelle_ligne = pd.DataFrame([{"id_technique": nouveau_id, "objet": nouvel_objet}])
                controller.loader.base_athletes = pd.concat(
                    [controller.loader.base_athletes, nouvelle_ligne], ignore_index=True
                )

                msg_eq = f" rattaché à l'équipe '{equipe_choisie}'" if equipe_choisie else " (Agent libre)"
                print(f"\n Le joueur '{nom}'{msg_eq} a été ajouté !")

            elif type_choix == "2":
                nouvel_objet = Equipe(nom=nom, id_equipe=nouveau_id, provenance=prov)
                nouvelle_ligne = pd.DataFrame([{"id_technique": nouveau_id, "objet": nouvel_objet}])
                controller.loader.base_equipes = pd.concat(
                    [controller.loader.base_equipes, nouvelle_ligne], ignore_index=True
                )
                print(f"\n L'équipe '{nom}' a été ajoutée avec succès !")

            # Mise à jour de l'annuaire interne
            if nouvel_objet:
                cle_annuaire = str(nouveau_id).strip().lower()
                controller.loader._annuaire_participants[cle_annuaire] = nouvel_objet

        # =========================================================
        # 3. GÉRER UN MATCH EXISTANT
        # =========================================================
        elif choix == "3":
            print("\n--- Gestion d'un Match ---")
            id_cible = demander_saisie("Entrez l'ID du match à gérer : ").strip()

            match_trouve = None
            tournoi_parent = None

            for m in competition.liste_match:
                if str(m.id_match) == id_cible:
                    match_trouve = m
                    tournoi_parent = competition
                    break

            if not match_trouve:
                for sous_comp in competition.sous_competitions.values():
                    for m in sous_comp.liste_match:
                        if str(m.id_match) == id_cible:
                            match_trouve = m
                            tournoi_parent = sous_comp
                            break
                    if match_trouve:
                        break

            if not match_trouve:
                print(f"Aucun match trouvé avec l'ID '{id_cible}'.")
                continue

            print(f"\n ✔️ Match trouvé dans la phase : '{tournoi_parent.nom}'")
            print(f"   {match_trouve}")

            print("\nQue voulez-vous faire avec ce match ?")
            print("1. Modifier les informations (Date, Participants, Stats, Score)")
            print("2. Supprimer définitivement le match")
            print("0. Annuler")

            action = demander_saisie("\nVotre choix : ")

            if action == "1":
                print("\n--- Mode Édition (Appuyez sur Entrée pour conserver la valeur actuelle) ---")

                date_actuelle = str(match_trouve.date).split()[0] if match_trouve.date else "Aucune"
                match_trouve.date = _saisir_date_valide("\nNouvelle date (YYYY-MM-DD)", date_actuelle)

                type_entite_attendu = None

                for role, perf in match_trouve.performances.items():
                    print(f"\n--- Édition du rôle : [{role}] ---")

                    if not type_entite_attendu:
                        type_entite_attendu = type(perf.participant)

                    nouveau_participant = rechercher_participant(controller, type_entite_attendu, perf.participant.nom)

                    if nouveau_participant == "GARDER_ACTUEL":
                        nouveau_participant = perf.participant
                    elif not nouveau_participant:
                        print("Édition annulée pour ce rôle.")
                        nouveau_participant = perf.participant
                    else:
                        print(f"✔️ Nouveau participant validé : {nouveau_participant.nom}")

                    nouvelles_stats = {}
                    for nom_stat, ancienne_valeur in perf.stats.items():
                        val_stat = demander_saisie(f"Valeur '{nom_stat}' [Actuel: {ancienne_valeur}] : ").strip()
                        if not val_stat:
                            nouvelles_stats[nom_stat] = ancienne_valeur
                        else:
                            try:
                                nouvelles_stats[nom_stat] = float(val_stat) if "." in val_stat else int(val_stat)
                            except ValueError:
                                nouvelles_stats[nom_stat] = val_stat

                    actuel_gagnant = "Oui" if perf.est_gagnant else "Non"
                    rep = demander_saisie(f"A GAGNÉ ? (O/N) [Actuel: {actuel_gagnant}] : ").strip().lower()
                    if not rep:
                        est_gagnant = perf.est_gagnant
                    elif rep in ["o", "oui", "y"]:
                        est_gagnant = True
                    elif rep in ["n", "non"]:
                        est_gagnant = False
                    else:
                        est_gagnant = perf.est_gagnant

                    match_trouve.performances[role] = Performance(
                        nouveau_participant, role=role, est_gagnant=est_gagnant, stats=nouvelles_stats
                    )

                controller.ranker.generer_classement(competition)
                print(f"\n Le match {id_cible} a été mis à jour !")
                print(" Le classement global et les statistiques ont été recalculés.")

            elif action == "2":
                print("\n ATTENTION : Vous êtes sur le point de supprimer ce match :")
                print(f"   {match_trouve}")
                confirmation = demander_saisie("Êtes-vous sûr ? (O/N) : ").strip().lower()

                if confirmation in ["o", "oui", "y"]:
                    tournoi_parent.liste_match.remove(match_trouve)
                    controller.ranker.generer_classement(competition)
                    print(f"\n Le match {id_cible} a été supprimé avec succès.")
                    print(" Le classement global et les statistiques ont été recalculés.")
                else:
                    print("\nSuppression annulée.")

            elif action == "0":
                continue
            else:
                print("Choix invalide.")

        # =========================================================
        # 4. SAUVEGARDER DANS LES FICHIERS CSV
        # =========================================================
        elif choix == "4":
            print("\n--- Sauvegarde des données ---")

            liste_totale_matchs = competition.liste_match.copy()

            for sous_comp in competition.sous_competitions.values():
                liste_totale_matchs.extend(sous_comp.liste_match)

            if not liste_totale_matchs:
                print(" Aucun match à sauvegarder.")
                continue

            donnees = []
            for m in liste_totale_matchs:
                try:
                    donnees.append(m.to_dict())
                except KeyError as e:
                    print(f"Données manquantes dans le match {m.id_match} : {e}")

            df_export = pd.DataFrame(donnees)
            print(f"{len(donnees)} matchs sont prêts à être sauvegardés.")

            chemin_defaut = "donnees/matchs_sauvegarde.csv"
            chemin_fichier = demander_saisie(f"Chemin (Entrée pour '{chemin_defaut}') : ").strip() or chemin_defaut

            try:
                from pathlib import Path

                dossier_brut = controller.loader.dossier_source if hasattr(controller.loader, "dossier_source") else "."

                dossier_path = Path(str(dossier_brut))

                gestionnaire = GestionnaireCSV(dossier_source=dossier_path)

                nom_final = str(chemin_fichier)
                gestionnaire.sauvegarder_fichier(df=df_export, nom_fichier=nom_final)
                print(f"\n✅ SUCCÈS : Base exportée dans '{nom_final}' !")

            except OSError as e:
                print(f"\n Erreur d'écriture (Disque/Droits) : {e}")
            except pd.errors.EmptyDataError as e:
                print(f"\n Erreur Pandas : {e}")

        # =========================================================
        # 0. QUITTER LE MENU
        # =========================================================
        elif choix == "0":
            break
        else:
            print("Choix invalide.")
