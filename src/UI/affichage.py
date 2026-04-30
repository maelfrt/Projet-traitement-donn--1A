from typing import Any

from src.Infrastructure.data_loader import DataLoader
from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match


def afficher_en_tete() -> None:
    """
    Affiche la bannière d'accueil.
    """
    print("\n" + "═" * 60)
    titre = "APPLICATION DE TRAITEMENT DES DONNÉES SPORTIVES"
    print(f"{titre:^60}")
    print("═" * 60)


def afficher_profil(partcipant: Any, palmares: list[str], moyennes: dict[str, float] | None = None) -> None:
    """
    Affiche la fiche biographique d'un participant.

    Parameters
    ----------
    partcipant : Any
        L'objet Participant (Athlete ou Equipe) à afficher.
    palmares : list[str]
        Liste des titres officiels gagnés.
    moyennes : dict[str, float], optional
        Dictionnaire des statistiques moyennes par match du participant.
    """
    print("\n" + "=" * 50)
    titre = f"FICHE PROFIL : {str(partcipant.nom).upper()}"
    print(f"{titre:^50}")
    print("=" * 50)

    type_str = "Équipe" if isinstance(partcipant, Equipe) else "Joueur"
    print(f"{'Type'.ljust(15)} : {type_str}")

    # Les attributs de base qu'on veut toujours afficher s'ils existent
    attributs_visibles = {
        "provenance": "Provenance",
        "equipe_actuelle": "Équipe",
        "role": "Rôle / Poste",
        "pseudo": "Pseudo",
        "genre": "Genre",
        "lieu_naissance": "Lieu Naiss.",
        "specialite": "Spécialité",
        "main_dominante": "Latéralité",
    }

    for attr, label in attributs_visibles.items():
        val = getattr(partcipant, attr, None)
        # On utilise la fonction de validation qui existe déjà dans le DataLoader
        if DataLoader._est_valeur_valide(val):
            print(f"{label.ljust(15)} : {val}")

    # Spécifique Athlète (Âge, IMC, etc.)
    if isinstance(partcipant, Athlete):
        age = partcipant.age()
        if DataLoader._est_valeur_valide(age):
            print(f"{'Âge'.ljust(15)} : {age} ans")

        gabarit = []
        taille = getattr(partcipant, "taille", None)
        poids = getattr(partcipant, "poids", None)

        if DataLoader._est_valeur_valide(taille):
            try:
                # Si c'est un nombre classique (ex: 185 ou 185.0), on le formate proprement
                taille_float = float(str(taille))
                gabarit.append(f"{taille_float:.0f} cm")
            except ValueError:
                # Si c'est un format texte comme '6-6' (système impérial), on l'affiche tel quel
                # On remplace le tiret par un apostrophe pour que ça ressemble à 6'6
                taille_propre = str(taille).replace("-", "'")
                gabarit.append(f'{taille_propre}"')
        if DataLoader._est_valeur_valide(poids):
            try:
                poids_float = float(str(poids))
                # Si le poids dépasse 150, on déduit qu'il est en système impérial
                if poids_float > 150:
                    gabarit.append(f"{poids_float:.0f} lbs")
                else:
                    gabarit.append(f"{poids_float:.0f} kg")
            except ValueError:
                # Si la donnée contient du texte imprévu, on l'affiche telle quelle
                gabarit.append(f"{poids}")

        if gabarit:
            print(f"{'Gabarit'.ljust(15)} : {' / '.join(gabarit)}")

        imc = partcipant.calculer_imc() if hasattr(partcipant, "calculer_imc") else None
        if imc:
            print(f"{'IMC'.ljust(15)} : {imc}")

    # Infos complémentaires (Les colonnes "bonus" du CSV)
    if hasattr(partcipant, "donnees_complementaires") and partcipant.donnees_complementaires:
        extras = {
            k: v
            for k, v in partcipant.donnees_complementaires.items()
            if k not in attributs_visibles and DataLoader._est_valeur_valide(v)
        }
        if extras:
            print("\n-- Infos Complémentaires --")
            for cle, val in extras.items():
                label = cle.replace("_", " ").capitalize()
                print(f"{label.ljust(15)} : {val}")

    # Effectif (Si c'est une équipe)
    if isinstance(partcipant, Equipe) and getattr(partcipant, "liste_athlete", None):
        print("\n-- Effectif --")
        for joueur in partcipant.liste_athlete:
            role_str = f" ({joueur.role})" if DataLoader._est_valeur_valide(getattr(joueur, "role", None)) else ""
            print(f"  • {joueur.nom}{role_str}")

    # Affichage des moyennes
    if moyennes:
        print("\n-- Moyennes de Performance (par match) --")
        for stat, valeur in moyennes.items():
            nom_propre = stat.replace("_", " ").capitalize()
            print(f"  • {nom_propre.ljust(20)} : {valeur}")

    # Palmarès & Titres (Fournis par l'AppController, on a juste à les afficher)
    print("\n-- Palmarès & Titres --")
    if not palmares:
        print("  Aucun titre pour le moment.")
    else:
        for titre in sorted(set(palmares)):
            print(f"  {titre}")
    print()


def afficher_bilan_historique(nom: str, stats: dict[str, Any], historique: list[dict[str, Any]]) -> None:
    """
    Affiche les performances passées et le taux de victoire.

    Paramètres
    ----------
    nom : str
        Nom du participant.
    stats : dict
        Dictionnaire des totaux calculés par l'AppController.
    historique : list
        Liste des derniers matchs formatés par l'AppController.
    """
    print(f"{'-' * 50}")
    titre = "BILAN & HISTORIQUE DES MATCHS"
    print(f"{titre:^50}")
    print(f"{'-' * 50}\n")

    total = stats.get("total", 0)

    if total == 0:
        print("Aucun match enregistré pour ce participant.")
        return

    victoires = stats.get("victoires", 0)
    nuls = stats.get("nuls", 0)
    defaites = stats.get("defaites", total - victoires - nuls)
    winrate = stats.get("winrate", 0.0)

    # Affichage du bilan chiffré
    print(f"{'Matchs joués'.ljust(12)} : {total}")
    print(f"{'Victoires'.ljust(12)} : {victoires}")
    if nuls > 0:
        print(f"{'Nuls'.ljust(12)} : {nuls}")
    print(f"{'Défaites'.ljust(12)} : {defaites}")
    print(f"{'Winrate'.ljust(12)} : {winrate:.1f} %\n")

    print("Historique récent :")
    for i, match_data in enumerate(historique[:15], 1):
        if match_data.get("gagne"):
            statut = "🏆 V"
        elif match_data.get("nul"):
            statut = "🤝 N"
        else:
            statut = "❌ D"

        date_raw = match_data.get("date", "")
        if DataLoader._est_valeur_valide(date_raw) and date_raw != "Date inconnue":
            date_propre = f"{date_raw.replace('-', '/')} - "
        else:
            date_propre = ""

        adv = match_data.get("adversaire", "Inconnu")

        print(f"{i:2d}. {statut} | {date_propre}vs {adv}")
    print()


def afficher_resultats_competition(competition: Competition, moyennes: dict[str, float] | None = None) -> None:
    """
    Affiche le tableau de classement pour le niveau de compétition fourni.

    La fonction se concentre sur une seule responsabilité : formater et
    afficher les données du classement de l'objet passé en paramètre,
    sans chercher à explorer l'arborescence des sous-groupes.

    Parameters
    ----------
    competition : Competition
        L'instance de la compétition (ou sous-compétition) dont on veut
        afficher le tableau des scores.
    moyennes : dict[str, float], optional
        Moyennes globales constatées durant cette phase précise.

    Returns
    -------
    None
    """
    print(f"\n🏆 STATISTIQUES ET CLASSEMENT : {competition.nom.upper()}")

    if moyennes:
        print("\n📊 Moyennes par participant sur cette phase :")
        lignes = [f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in moyennes.items()]
        print(" | ".join(lignes))
        print()

    if competition.classement_final:
        print(f"{'=' * 55}")
        print(f"{'Rang':<6} | {'Nom':<25} | Score/Stats")
        print(f"{'-' * 55}")

        for i, rang in enumerate(competition.classement_final, 1):
            # Extraction des données du classement
            nom = rang.get("nom", "Inconnu")
            nom_affiche = nom[:22] + "..." if len(nom) > 25 else nom

            # Adaptation selon le mode de calcul (Championnat vs Élimination)
            score = rang.get("victoires") if "victoires" in rang else rang.get("tour_atteint", "N/A")
            label = "victoires" if "victoires" in rang else ""

            print(f"{i:2d}.    | {nom_affiche:<25} | {score} {label}")
    else:
        print("Note : Classement en cours de calcul ou non disponible.")


def afficher_details_match(match: Match) -> None:
    """
    Affiche les informations du match avec toutes les statistiques.

    Paramètres
    ----------
    match : Match
        L'objet contenant les informations de la rencontre.
    """
    print("\n" + "=" * 50)

    # Génération de l'affiche (Les adversaires)
    noms_participants = [perf.participant.nom for perf in match.performances.values()]
    titre_affiche = " vs ".join(noms_participants) if noms_participants else "Participants inconnus"

    print(f"{'RAPPORT DE MATCH :':^50}")
    print("-" * 50)
    print(f"{titre_affiche}")

    # On récupère le véritable objet date et on le formate en YYYY/MM/DD
    date_obj = getattr(match, "date_objet", None)
    date_str = date_obj.strftime("%Y/%m/%d") if date_obj else "N/A"
    lieu_str = getattr(match, "lieu", "N/A")
    print(f"Date : {date_str} | Lieu : {lieu_str}")

    print("-" * 50)

    infos_extras = []

    attributs_natifs = {
        "type_match": "Phase/Tour",
        "niveau_tournoi": "Niveau",
        "surface": "Surface",
        "format_sets": "Format",
        "patch": "Patch",
    }

    for attr, label in attributs_natifs.items():
        valeur = getattr(match, attr, None)
        if valeur is not None and str(valeur).strip().lower() not in ["nan", "none", ""]:
            infos_extras.append(f"{label} : {valeur}")

    # Extraction des données spécifiques du JSON (Le dictionnaire infos_supplementaires)
    if getattr(match, "infos_supplementaires", None):
        for cle, valeur in match.infos_supplementaires.items():
            if valeur is not None and str(valeur).strip().lower() not in ["nan", "none", ""]:
                cle_formatee = str(cle).replace("_", " ").capitalize()
                infos_extras.append(f"{cle_formatee} : {valeur}")

    # Affichage final
    if infos_extras:
        for info in infos_extras:
            print(f"  - {info}")

    print("=" * 50)

    # Affichage des performances individuelles ou collectives
    for role, perf in match.performances.items():
        if perf.est_gagnant:
            embleme = "🏆 [GAGNANT]"
        elif getattr(perf, "est_nul", False):
            embleme = "🤝 [NUL]"
        else:
            embleme = "🥈 [PERDANT]"
        print(f"\n   {embleme} {role} : {perf.participant.nom}")

        if not perf.stats:
            print("   (Pas de statistiques enregistrées)")
        else:
            for cle, valeur in perf.stats.items():
                nom_stat = cle.replace("_", " ").capitalize()
                val_str = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
                print(f"     • {nom_stat:20} : {val_str}")


def afficher_face_a_face(p1: Any, p2: Any, stats_h2h: dict) -> None:
    """
    Affiche le bilan des confrontations directes entre deux entités.

    Paramètres
    ----------
    p1 : Any
        participant numéro 1.
    p2 : Any
        participant numéro 2.
    stats_h2h : dict
        Nombre de victoire du face à face.
    """
    print("\n" + "=" * 55)
    print(f"{'⚔️  FACE-À-FACE  ⚔️':^55}")
    print("=" * 55)

    # Affichage du score géant (ex: FEDERER  25 -- 15  NADAL)
    print(f"\n{p1.nom:^25} VS {p2.nom:^25}")
    print(f"{stats_h2h['victoires_p1']:^25} -- {stats_h2h['victoires_p2']:^25}")
    print("-" * 55)
    print(f"Total des confrontations directes : {stats_h2h['total']}")

    if stats_h2h["nuls"] > 0:
        print(f"Matchs nuls : {stats_h2h['nuls']}")

    if stats_h2h["total"] == 0:
        print("\nCes deux participants ne se sont jamais affrontés.")
        return

    print("\nHISTORIQUE DES RENCONTRES :")
    for i, match_info in enumerate(stats_h2h["historique"][:10], 1):
        date = match_info["date"]
        vainqueur = match_info["vainqueur"]

        if vainqueur == p1.nom:
            resultat = f"🏆 Victoire de {p1.nom}"
        elif vainqueur == p2.nom:
            resultat = f"🏆 Victoire de {p2.nom}"
        else:
            resultat = "🤝 Match nul"

        print(f" {i:2d}. [{date}] {resultat}")

    if stats_h2h["total"] > 10:
        print(" ... (seuls les 10 derniers matchs sont affichés)")
    print()


def afficher_statistiques_globales(stats: dict[str, Any], moyennes_globales: dict[str, float] | None = None) -> None:
    """
    Affiche le tableau de bord complet (Records, Âge, Géo).
    C'est ici que l'on valorise les données de provenance.

    Paramètres
    ----------
    stats : dict
        Dictionnaire de données compilées par le moteur de statistiques.
    moyennes_globales : dict[str, float], optional
        Moyennes de toutes les rencontres du sport actuellement chargé.
    """
    print("\n" + "=" * 55)
    print(f"{'STATISTIQUES ET RECORDS':^55}")
    print("=" * 55)

    # Chiffres de participation
    # On utilise ljust(28) pour aligner parfaitement les ":"
    print(f"{'Total des matchs enregistrés'.ljust(28)} : {stats.get('total_matchs', 0)}")
    print(f"{'Total des équipes inscrites'.ljust(28)} : {stats.get('total_equipes', 0)}")
    print(f"{'Total des joueurs inscrits'.ljust(28)} : {stats.get('total_athletes', 0)}")

    # Records sportifs
    print("\n--- 🏆 RECORDS DE PERFORMANCE ---")
    if "meilleur_winrate" in stats:
        w = stats["meilleur_winrate"]
        print(f"{'Meilleur Winrate'.ljust(18)} : {w['nom']} avec {w['winrate']:.1f}% ({w['joues']} matchs)")
    if "plus_actif" in stats:
        a = stats["plus_actif"]
        print(f"{'Le plus actif'.ljust(18)} : {a['nom']} avec {a['joues']} matchs disputés.")

    # Moyenne globale du tournoi
    if moyennes_globales:
        print("\n--- 📈 MOYENNES GLOBALES DU TOURNOI (par participant/match) ---")
        for stat, valeur in moyennes_globales.items():
            nom_propre = stat.replace("_", " ").capitalize()
            print(f"{nom_propre.ljust(28)} : {valeur}")

    # Données démographiques
    if "plus_jeune" in stats or "plus_age" in stats:
        print("\n--- 👤 RECORDS DÉMOGRAPHIQUES ---")
        if "plus_jeune" in stats:
            j = stats["plus_jeune"]
            print(f"{'Joueur le plus jeune'.ljust(21)} : {j['nom']} ({j['age']} ans)")
        if "plus_age" in stats:
            v = stats["plus_age"]
            print(f"{'Joueur le plus âgé'.ljust(21)} : {v['nom']} ({v['age']} ans)")

    # Analyse Géographique (Provenance)
    if "top_provenances" in stats or "meilleur_winrate_provenance" in stats:
        print("\n--- 🌍 GÉOGRAPHIE & PROVENANCES ---")

        if "top_provenances" in stats:
            print("Nations/Régions les plus représentées :")
            for i, (nation, nb) in enumerate(stats["top_provenances"], 1):
                print(f" {i}. {nation} : {nb} représentant(s)")

        if "meilleur_winrate_provenance" in stats:
            p = stats["meilleur_winrate_provenance"]
            print(f"\nNation la plus dominante : {p['pays']}")
            print(f" -> {p['winrate']:.0f}% de victoires (sur {p['joues']} matchs cumulés)")


def afficher_a_propos() -> None:
    """
    Affiche le manuel d'aide et les crédits de l'application.

    Cette interface présente de manière claire les fonctionnalités,
    les raccourcis, la flexibilité du système (architecture universelle)
    et l'équipe de développement à l'origine du projet.
    """
    print("\n" + "=" * 65)
    print(f"{'ℹ️  AIDE, INFORMATIONS ET CRÉDITS':^65}")
    print("=" * 65)

    print("\n L'APPLICATION EN BREF")
    print("  • Objectif : Suivre et analyser n'importe quel tournoi sportif.")
    print("  • Suivi    : Les classements s'actualisent automatiquement à chaque match.")
    print("  • Analyse  : Consultez profils, statistiques moyennes et historiques.")

    print("\n UNE ARCHITECTURE UNIVERSELLE")
    print("  • Flexibilité : Le système a été conçu pour s'adapter à chaque sport.")
    print("  • Évolutivité : Grâce à de simples fichiers de configuration JSON, le")
    print("                  programme interprète n'importe quel nouveau fichier")
    print("                  de données sans aucune modification du code source.")
    print("  • Multi-sport : Passez du Tennis, au Football ou à l'E-sport en un clic !")

    print("\n OÙ SONT MES DONNÉES ?")
    print("  • Configurations : Le dossier 'configs' contient les règles des sports.")
    print("  • Résultats      : Le dossier 'donnees' stocke les informations des matchs.")
    print("  • Sauvegardes    : Accessibles via le menu [ADMIN] pour sauvegarder les modifications.")

    print("\n RACCOURCIS UTILES")
    print("  • [Entrée] : Valider une saisie ou passer à l'écran suivant.")
    print("  • [0]      : Revenir en arrière (très utile en cas d'erreur de menu).")
    print("  • [q]      : Fermer l'application proprement à n'importe quel moment.")

    print("\n ÉQUIPE DE DÉVELOPPEMENT")
    print("  • Kilian Crumbach")
    print("  • Ryan Alves")
    print("  • Mael Fretté")
    print("  • Raphaëlle Belaygues")

    print("\n" + "=" * 65)
