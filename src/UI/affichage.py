from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match


def afficher_en_tete() -> None:
    """Affiche le titre institutionnel de l'application."""
    print("-" * 60)
    print("APPLICATION DE TRAITEMENT DES DONNÉES SPORTIVES")
    print("-" * 60)


def afficher_resultats_competition(competition: Competition, niveau: int = 0) -> None:
    """Affiche l'arborescence des résultats et classements de manière récursive."""
    marge = "    " * niveau
    separateur = ">>> " if niveau == 0 else "  > "

    print(f"\n{marge}{separateur}COMPÉTITION : {competition.nom.upper()}")

    if competition.classement_final:
        print(f"{marge}{'=' * 40}")
        for i, rang in enumerate(competition.classement_final, 1):
            if "victoires" in rang:
                label_score = "victoires"
            else:
                label_score = ""
            valeur_score = rang.get("victoires") if "victoires" in rang else rang.get("tour_atteint")

            print(f"{marge}{i:2d}. {rang['nom']:<25} | {valeur_score} {label_score}")
    else:
        print(f"{marge}Information : Aucun classement calculé à ce niveau.")

    for sous_comp in competition.sous_competitions.values():
        afficher_resultats_competition(sous_comp, niveau + 1)


def afficher_details_match(match: Match) -> None:
    """Affiche le rapport détaillé d'un match avec les stats de chaque participant."""
    print("\n" + "=" * 60)
    print(f"   RAPPORT DE MATCH : {match.id_match}")
    print(f"   Date : {match.date} | Lieu : {match.lieu or 'N/A'}")
    print("=" * 60)

    if not match.performances:
        print("Aucune donnée de performance disponible pour ce match.")
    else:
        for role, perf in match.performances.items():
            prefixe = "🏆 [GAGNANT]" if perf.est_gagnant else "🥈 [PERDANT]"
            print(f"\n{prefixe} {role} : {perf.participant.nom}")
            print("-" * 30)

            if not perf.stats:
                print("   (Aucune statistique détaillée)")
            else:
                for cle, valeur in perf.stats.items():
                    cle_nom = cle.replace("_", " ").capitalize()
                    valeur_str = f"{valeur:.1f}" if isinstance(valeur, float) else str(valeur)
                    print(f"   - {cle_nom:25} : {valeur_str}")

    print("\n" + "=" * 60)
    input("Appuyez sur Entrée pour revenir à la liste...")


def _recuperer_tous_les_matchs(competition: Competition) -> list:
    """Parcourt l'arborescence complète pour récupérer une liste plate de tous les matchs."""
    matchs = list(competition.liste_match)
    for sous_comp in competition.sous_competitions.values():
        matchs.extend(_recuperer_tous_les_matchs(sous_comp))
    return matchs


def afficher_profil(entite, competition: Competition | None) -> None:
    """Affiche un tableau de bord exhaustif et dynamique d'une Équipe ou d'un Joueur."""

    def est_valide(valeur) -> bool:
        if valeur is None:
            return False
        return not (isinstance(valeur, str) and valeur.strip().lower() in ["nan", "none", "", "aucun", "inconnu"])

    def obtenir_valeur(obj, cle):
        val = getattr(obj, cle, None)
        if val is not None:
            return val
        if hasattr(obj, "donnees_complementaires"):
            return obj.donnees_complementaires.get(cle, None)
        return None

    print("\n" + "=" * 55)
    print(f"   FICHE PROFIL : {entite.nom.upper()}")
    print("=" * 55)

    type_str = "Équipe" if isinstance(entite, Equipe) else "Joueur"
    print(f"Type       : {type_str}")

    attributs_a_tester = {
        "provenance": "Provenance",
        "equipe_actuelle": "Équipe",
        "role": "Rôle / Poste",
        "pseudo": "Pseudo",
        "genre": "Genre",
        "lieu_naissance": "Lieu Naiss.",
        "specialite": "Spécialité",
        "main_dominante": "Latéralité",
    }

    for attr, label in attributs_a_tester.items():
        val = obtenir_valeur(entite, attr)
        if est_valide(val):
            print(f"{label:11} : {val}")

    # Cas particuliers (Âge et Gabarit)
    if isinstance(entite, Athlete):
        age_val = entite.age()
        if est_valide(age_val):
            print(f"Âge         : {age_val} ans")

        taille_val = entite.taille
        poids_val = entite.poids

        if est_valide(taille_val) or est_valide(poids_val):
            elements_gabarit = []
            if taille_val is not None and est_valide(taille_val):
                elements_gabarit.append(f"{float(taille_val):.0f} cm")
            if poids_val is not None and est_valide(poids_val):
                elements_gabarit.append(f"{poids_val} kg")

            print(f"Gabarit     : {' / '.join(elements_gabarit)}")

            imc = entite.calculer_imc()
            if imc:
                print(f"IMC         : {imc}")

    # AFFICHAGE DES DONNÉES "KWARGS" (Tout le reste du mapping JSON)
    if hasattr(entite, "donnees_complementaires") and entite.donnees_complementaires:
        extras = []
        for cle, valeur in entite.donnees_complementaires.items():
            if cle not in attributs_a_tester and est_valide(valeur):
                cle_f = cle.replace("_", " ").capitalize()
                extras.append(f"{cle_f:11} : {valeur}")

        if extras:
            print("\n-- Infos Complémentaires --")
            for info in extras:
                print(info)

    # EFFECTIF (Pour les Équipes)
    if isinstance(entite, Equipe) and entite.liste_athlete:
        print("\n-- Effectif --")
        for joueur in entite.liste_athlete:
            role_str = f" ({joueur.role})" if est_valide(joueur.role) else ""
            print(f" - {joueur.nom}{role_str}")

    # BILAN DES MATCHS
    print("\n" + "-" * 55)
    print("   BILAN & HISTORIQUE DES MATCHS")
    print("-" * 55)

    if not competition:
        print("Aucune compétition chargée.")
    else:
        tous_les_matchs = _recuperer_tous_les_matchs(competition)
        historique = []
        victoires = 0

        for match in tous_les_matchs:
            for role, perf in match.performances.items():
                match_valide = str(perf.participant.id) == str(entite.id)

                if not match_valide and isinstance(entite, Athlete) and hasattr(perf.participant, "liste_athlete"):
                    for joueur_equipe in perf.participant.liste_athlete:
                        if str(joueur_equipe.id) == str(entite.id):
                            match_valide = True
                            break

                if match_valide:
                    historique.append((match, role, perf))
                    if perf.est_gagnant:
                        victoires += 1

        total_matchs = len(historique)
        if total_matchs == 0:
            print("Aucun match enregistré pour ce participant.")
        else:
            winrate = (victoires / total_matchs) * 100
            print(f"Matchs joués : {total_matchs:2d}")
            print(f"Victoires    : {victoires:2d}")
            print(f"Défaites     : {total_matchs - victoires:2d}")
            print(f"Winrate      : {winrate:.1f} %\n")

            print("Historique récent (Ligne par match) :")
            for match, role, perf in historique:
                statut = "🏆 V" if perf.est_gagnant else "❌ D"
                date_propre = str(match.date).split()[0].replace("-", "/")

                resume_parts = []
                for cle, valeur in perf.stats.items():
                    if est_valide(valeur):
                        cle_formatee = cle.replace("_", " ").capitalize()
                        if isinstance(valeur, float):
                            valeur = f"{valeur:.1f}"
                        resume_parts.append(f"{cle_formatee}: {valeur}")
                    if len(resume_parts) >= 2:
                        break

                resume_stat = " - ".join(resume_parts)
                detail = f" | {resume_stat}" if resume_stat else ""

                print(f" {statut} | {date_propre} - Match {match.id_match}{detail}")

    print("\n" + "=" * 55)
    input("Appuyez sur Entrée pour continuer...")


def afficher_statistiques_globales(stats: dict) -> None:
    """Affiche le tableau de bord des records globaux du tournoi."""
    print("\n" + "=" * 55)
    print("   📊 TABLEAU DE BORD : STATISTIQUES ET RECORDS")
    print("=" * 55)

    print(f"Total des matchs enregistrés : {stats.get('total_matchs', 0)}")

    print("\n--- 🏆 RECORDS DE PERFORMANCE ---")
    if "meilleur_winrate" in stats:
        wr = stats["meilleur_winrate"]
        print(f"Meilleur Winrate  : {wr['nom']} avec {wr['winrate']:.1f}% ({wr['joues']} matchs)")
    else:
        print("Meilleur Winrate  : Pas assez de matchs joués (min. 3) pour calculer un ratio pertinent.")

    if "plus_actif" in stats:
        pa = stats["plus_actif"]
        print(f"Le plus actif     : {pa['nom']} avec {pa['joues']} matchs disputés.")

    print("\n--- 👤 RECORDS DÉMOGRAPHIQUES ---")
    if "plus_jeune" in stats and "plus_age" in stats:
        print(f"Joueur le plus jeune : {stats['plus_jeune']['nom']} ({stats['plus_jeune']['age']} ans)")
        print(f"Joueur le plus âgé   : {stats['plus_age']['nom']} ({stats['plus_age']['age']} ans)")
    else:
        print("Données d'âge insuffisantes ou non applicables pour ce sport.")

    print("\n--- 🌍 GÉOGRAPHIE & PROVENANCES ---")
    if "top_provenances" in stats:
        print("Nations/Régions les plus représentées :")
        for i, (pays, compte) in enumerate(stats["top_provenances"], 1):
            print(f"  {i}. {pays:<5} : {compte} représentant(s)")
    else:
        print("Aucune donnée de provenance valide pour ce tournoi.")

    if "meilleur_winrate_provenance" in stats:
        mwp = stats["meilleur_winrate_provenance"]
        print(f"\nNation la plus dominante : {mwp['pays']}")
        print(f"  -> {mwp['winrate']:.0f}% de victoires (sur {mwp['joues']} matchs cumulés)")
    else:
        print("\nNation la plus dominante : Pas assez de données valides pour calculer cette statistique.")

    print("\n" + "=" * 55)
    input("Appuyez sur Entrée pour retourner au menu...")
