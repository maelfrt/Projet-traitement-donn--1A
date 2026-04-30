from typing import Any

from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe


def calculer_statistiques_globales(competition: Competition, liste_participants: list[Any]) -> dict[str, Any]:
    """
    Moteur d'agrégation principal pour l'analyse des données de la compétition.

    Compile les métriques démographiques, géographiques et de performance en
    déléguant les calculs spécifiques à des sous-fonctions spécialisées.
    Cette approche garantit un code modulaire et facilement testable.

    Parameters
    ----------
    competition : Competition
        L'objet racine contenant l'arborescence des matchs à analyser.
    liste_participants : list[Any]
        La liste complète des participants (athlètes et équipes) chargés en mémoire.

    Returns
    -------
    dict[str, Any]
        Un dictionnaire global contenant tous les indicateurs clés et les records.
    """
    tous_les_matchs = competition.obtenir_tous_les_matchs()

    # Initialisation de la structure avec les comptages de base via des générateurs.
    # L'utilisation de sum() avec une expression génératrice évite de créer
    # des listes intermédiaires inutiles en mémoire.
    stats: dict[str, Any] = {
        "total_athletes": sum(1 for e in liste_participants if isinstance(e, Athlete)),
        "total_equipes": sum(1 for e in liste_participants if isinstance(e, Equipe)),
        "total_matchs": len(tous_les_matchs),
    }

    # Enrichissement du dictionnaire avec l'analyse de la répartition des âges
    stats.update(_analyser_demographie_age(liste_participants))

    # Enrichissement avec les bilans de victoires et les statistiques géographiques
    stats.update(_analyser_performances_et_provenances(tous_les_matchs, liste_participants))

    return stats


def _analyser_demographie_age(liste_participants: list[Any]) -> dict[str, Any]:
    """
    Isole les athlètes valides pour identifier les extrema d'âge.

    Parameters
    ----------
    liste_participants : list[Any]
        La liste de tous les participants inscrits au tournoi.

    Returns
    -------
    dict[str, Any]
        Un dictionnaire contenant les informations du plus jeune et du plus âgé.
    """
    # Filtrage préalable pour écarter les équipes et les athlètes dont la
    # date de naissance n'a pas pu être convertie (absence de méthode age() valide).
    athletes_valides = [a for a in liste_participants if isinstance(a, Athlete) and a.age() is not None]

    if not athletes_valides:
        return {}

    # Extraction des extrêmes à l'aide des fonctions natives Python.
    # Le cast en int() combiné à l'opérateur "or" garantit la stabilité
    # du comparateur pour Mypy au cas où un résidu None passerait le filtre.
    plus_jeune = min(athletes_valides, key=lambda x: int(x.age() or 999))
    plus_age = max(athletes_valides, key=lambda x: int(x.age() or 0))

    return {
        "plus_jeune": {"nom": plus_jeune.nom, "age": plus_jeune.age()},
        "plus_age": {"nom": plus_age.nom, "age": plus_age.age()},
    }


def _analyser_performances_et_provenances(tous_les_matchs: list[Any], liste_participants: list[Any]) -> dict[str, Any]:
    """
    Agrège les résultats des matchs et la géographie en un seul passage algorithmique.

    Cette fonction optimise le calcul en balayant la liste des rencontres
    une seule fois (complexité O(N)). Elle utilise des dictionnaires
    pour compter les victoires par individu et par nation.

    Parameters
    ----------
    tous_les_matchs : list[Any]
        L'ensemble des objets Match joués durant la compétition.
    liste_participants : list[Any]
        Les entités participant au tournoi pour l'extraction des pays d'origine.

    Returns
    -------
    dict[str, Any]
        Un dictionnaire contenant les records de performance et les données
        de domination géographique.
    """
    bilan_joueurs: dict[str, dict[str, Any]] = {}
    bilan_prov: dict[str, dict[str, int]] = {}
    repartition_prov: dict[str, int] = {}

    # Création d'un ensemble (set) de mots-clés désignant une information manquante.
    # La recherche dans un set est instantanée par rapport à une liste.
    valeurs_nulles = {"nan", "none", "", "aucun", "inconnu"}

    # Construction de la distribution géographique initiale basée sur les inscrits
    for participant in liste_participants:
        prov = getattr(participant, "provenance", None)
        if prov:
            prov_clean = str(prov).strip().lower()
            if prov_clean not in valeurs_nulles:
                # Incrémentation sécurisée : si la clé n'existe pas, get() renvoie 0
                repartition_prov[prov] = repartition_prov.get(prov, 0) + 1

    # Agrégation des performances par itération unique sur les matchs joués
    for match in tous_les_matchs:
        for perf in match.performances.values():
            participant = perf.participant
            pid = str(participant.id)

            # Mise à jour des compteurs individuels de victoire et de participation
            if pid not in bilan_joueurs:
                bilan_joueurs[pid] = {"joues": 0, "victoires": 0, "nom": participant.nom}

            bilan_joueurs[pid]["joues"] += 1
            if perf.est_gagnant:
                bilan_joueurs[pid]["victoires"] += 1

            # Collecte des données de provenance pour évaluer la domination régionale
            prov = getattr(participant, "provenance", None)

            # Stratégie de repli : si une équipe n'a pas de nationalité propre
            # (comme en E-sport), on tente de récupérer celle de son premier joueur.
            if not prov and isinstance(participant, Equipe) and participant.liste_athlete:
                prov = getattr(participant.liste_athlete[0], "provenance", None)

            if prov:
                prov_clean = str(prov).strip().lower()
                if prov_clean not in valeurs_nulles:
                    if prov not in bilan_prov:
                        bilan_prov[prov] = {"joues": 0, "victoires": 0}

                    bilan_prov[prov]["joues"] += 1
                    if perf.est_gagnant:
                        bilan_prov[prov]["victoires"] += 1

    # Extraction des métriques cibles et des records à partir des accumulateurs
    resultats: dict[str, Any] = {}

    if bilan_joueurs:
        # Détection de l'entité ayant disputé le plus de rencontres
        plus_actif = max(bilan_joueurs.values(), key=lambda x: int(x["joues"]))
        resultats["plus_actif"] = {"nom": plus_actif["nom"], "joues": plus_actif["joues"]}

        # Échantillonnage : on impose un minimum de 3 matchs pour garantir
        # la pertinence mathématique du taux de victoire (winrate).
        valides_wr = [p for p in bilan_joueurs.values() if p["joues"] >= 3]
        if valides_wr:
            meilleur = max(valides_wr, key=lambda x: float(x["victoires"]) / float(x["joues"]))
            resultats["meilleur_winrate"] = {
                "nom": meilleur["nom"],
                "winrate": (meilleur["victoires"] / meilleur["joues"]) * 100,
                "joues": meilleur["joues"],
            }

    if repartition_prov:
        # Tri décroissant des effectifs pour isoler les 3 régions les plus représentées
        resultats["top_provenances"] = sorted(repartition_prov.items(), key=lambda x: int(x[1]), reverse=True)[:3]

    # Application du même échantillonnage statistique pour les nations
    valides_prov = {k: v for k, v in bilan_prov.items() if v["joues"] >= 3}
    if valides_prov:
        meilleur_p = max(valides_prov.items(), key=lambda x: float(x[1]["victoires"]) / float(x[1]["joues"]))
        resultats["meilleur_winrate_provenance"] = {
            "pays": meilleur_p[0],
            "winrate": (meilleur_p[1]["victoires"] / meilleur_p[1]["joues"]) * 100,
            "joues": meilleur_p[1]["joues"],
            "seuil": 3,
        }

    return resultats
