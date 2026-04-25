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

    noms_participants = [perf.participant.nom for perf in match.performances.values()]
    if len(noms_participants) == 2:
        titre = f"{noms_participants[0]} vs {noms_participants[1]}"
    elif len(noms_participants) > 2:
        titre = f"Match multi-participants ({len(noms_participants)} inscrits)"
    else:
        titre = "Détails de la rencontre"

    print(f"   RAPPORT DE MATCH : {titre}")

    date_propre = (
        str(match.date).split()[0].replace("-", "/") if match.date and str(match.date).lower() != "none" else "N/A"
    )
    print(f"   Date : {date_propre} | Lieu : {match.lieu or 'N/A'}")

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

    if hasattr(match, "infos_supplementaires"):
        for cle, valeur in match.infos_supplementaires.items():
            if valeur is not None and str(valeur).strip().lower() not in ["nan", "none", ""]:
                cle_formatee = cle.replace("_", " ").capitalize()
                infos_extras.append(f"{cle_formatee} : {valeur}")

    if infos_extras:
        print("-" * 30)
        for info in infos_extras:
            print(f"   - {info}")

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

    # ==============================
    # PALMARÈS & TITRES
    # ==============================
    if competition:

        def _recuperer_trophees(entite_cible, comp: Competition) -> list[str]:
            trophees_trouves = []

            # Si le tournoi a un classement calculé
            if comp.classement_final and len(comp.classement_final) > 0:
                premier = comp.classement_final[0]
                nom_premier = str(premier.get("nom", "")).strip()

                # Le participant a-t-il gagné ? (Lui-même, ou son équipe)
                nom_gagnant = nom_premier.lower()

                noms_valides = [str(entite_cible.nom).lower().strip()]

                equipe = getattr(entite_cible, "equipe_actuelle", None)
                if equipe:
                    noms_valides.append(str(equipe).lower().strip())

                a_gagne = nom_gagnant in noms_valides

                # S'il est premier, on personnalise l'affichage selon le nom du bloc
                if a_gagne:
                    nom_actuel = comp.nom.upper()
                    nom_global = competition.nom.upper()

                    # Si c'est le tournoi principal
                    if nom_actuel == "TABLEAU PRINCIPAL" or nom_actuel == nom_global:
                        trophees_trouves.append(f"🏆 Vainqueur : {nom_global}")

                    # Si c'est une phase de poule ou un groupe
                    elif str(comp.type_format).lower() == "championnat":
                        victoires = premier.get("victoires", 0)
                        trophees_trouves.append(f"🥇 1er de groupe/section : {nom_actuel} ({victoires}V)")

                    # Pour les autres sous-tournois à élimination
                    else:
                        trophees_trouves.append(f"🥇 1er de phase : {nom_actuel}")

            # Recherche récursive dans les sous-tournois (Poules, Stages...)
            for sous_comp in comp.sous_competitions.values():
                trophees_trouves.extend(_recuperer_trophees(entite_cible, sous_comp))

            return trophees_trouves

        # Exécution de la recherche
        liste_trophees = _recuperer_trophees(entite, competition)

        if liste_trophees:
            print("\n-- Palmarès & Titres --")
            for trophee in liste_trophees:
                print(f" {trophee}")

    # BILAN DES MATCHS
    print("\n" + "-" * 55)
    print("   BILAN & HISTORIQUE DES MATCHS")
    print("-" * 55)

    if not competition:
        print("Aucune compétition chargée.")
    else:
        tous_les_matchs = competition.obtenir_tous_les_matchs()
        historique = []
        victoires = 0

        for match in tous_les_matchs:
            for role, perf in match.performances.items():
                match_valide = str(perf.participant.id) == str(entite.id)

                if not match_valide and isinstance(entite, Athlete):
                    if hasattr(perf, "joueurs_match") and perf.joueurs_match:
                        for joueur in perf.joueurs_match:
                            if str(joueur.id) == str(entite.id):
                                match_valide = True
                                break
                    elif hasattr(perf.participant, "liste_athlete"):
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

            historique.sort(key=lambda item: str(item[0].date), reverse=True)

            print("Historique récent :")
            matchs_visibles = historique[:15]

            for i, (match, role, perf) in enumerate(matchs_visibles, 1):
                statut = "🏆 V" if perf.est_gagnant else "❌ D"

                if match.date and str(match.date).strip().lower() not in ["nan", "none", ""]:
                    date_propre = f"{str(match.date).split()[0].replace('-', '/')} - "
                else:
                    date_propre = ""

                nom_adversaire = "Adversaire inconnu"
                for p in match.performances.values():
                    if str(p.participant.id) != str(entite.id):
                        nom_adversaire = p.participant.nom
                        break

                print(f"{i:2d}. {statut} | {date_propre}vs {nom_adversaire}")


def afficher_statistiques_globales(stats: dict) -> None:
    """Affiche le tableau de bord des records globaux du tournoi."""
    print("\n" + "=" * 55)
    print("   📊 TABLEAU DE BORD : STATISTIQUES ET RECORDS")
    print("=" * 55)

    print(f"Total des matchs enregistrés : {stats.get('total_matchs', 0)}")

    if stats.get("total_equipes", 0) > 0:
        print(f"Total des équipes inscrites  : {stats['total_equipes']}")
    if stats.get("total_athletes", 0) > 0:
        print(f"Total des joueurs inscrits   : {stats['total_athletes']}")

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


def afficher_a_propos() -> None:
    """Affiche la page de présentation, les aides et l'architecture des fichiers."""
    import pydoc

    texte_a_propos = """
        ============================================================
                        À propos / Fonctionnalités
        ============================================================
        Description : Système avancé de gestion de compétitions
        ------------------------------------------------------------

        PRÉSENTATION
        Cette application a été conçue et développée en Python dans
        le cadre d'un projet de groupe. L'objectif était de créer un
        système complet et robuste de gestion de compétitions sportivee
        en appliquant les meilleures pratiques de programmation.

        ARCHITECTURE ET ADAPTABILITÉ
        Le système repose sur une architecture générique, pensée
        pour gérer de multiples jeux de données sans avoir à
        réécrire le cœur de l'application pour chaque nouveau sport.

        Cette flexibilité repose sur les fichiers de configuration JSON
        (dans le dossier "config"). Ces fichiers agissent comme des
        traducteurs : ils expliquent au programme comment "mapper" les
        colonnes d'un fichier CSV inconnu vers nos objets Python standards.

        CE QUE VOUS POUVEZ FAIRE
        - Naviguer    : Changez de sport à tout moment depuis le menu.
        - Rechercher  : Trouvez instantanément le profil complet
                        d'un athlète ou d'une équipe.
        - Consulter   : Lisez les classements d'une compétition,
                        que ça soit un championnat ou un tournoi à
                        élimination.
        - Administrer : Ajoutez de nouveaux matchs, inscrivez des
                        joueurs ou corrigez des erreurs passées.

        CONSEILS D'UTILISATION
        - Navigation : Tapez simplement le numéro correspondant
                        à votre choix et appuyez sur Entrée.
        - Annulation : Dans presque tous les menus, tapez "0"
                        pour faire un retour en arrière.
                        Vous pouvez aussi appuyer sur "q" (ou "Q")
                        pour quitter l'application à tout moment.
        - Recherche  : Vous n'avez pas besoin de taper le nom
                        complet d'un joueur, une partie suffit !

        ARCHITECTURE ET FICHIERS DE DONNÉES
        Vos données sont stockées localement sur votre disque dur
        dans le dossier "donnees".

        Chaque sport possède son propre sous-dossier (ex: /football)
        contenant les fichiers de données (au format CSV) :
        - match.csv  : L'historique officiel de toutes les rencontres.
        - player.csv : La base de données des athlètes.
        - team.csv   : La base de données des équipes engagées.

        NOTE POUR L'ADMIN :
        Vos ajouts et modifications en mémoire ne seront inscrits
        définitivement dans ces fichiers CSV que si vous utilisez
        l'option "Sauvegarder" avant de quitter l'application !

        ============================================================
        """
    pydoc.pager(texte_a_propos)
