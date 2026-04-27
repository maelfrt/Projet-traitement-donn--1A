from typing import Any

from src.Model.athlete import Athlete
from src.Model.equipe import Equipe


def calculer_statistiques_globales(competition, liste_entites: list) -> dict:
    """Chef d'orchestre des statistiques (Version Haute Performance)."""
    tous_les_matchs = competition.obtenir_tous_les_matchs()

    stats: dict[str, Any] = {
        "total_athletes": sum(1 for e in liste_entites if isinstance(e, Athlete)),
        "total_equipes": sum(1 for e in liste_entites if isinstance(e, Equipe)),
        "total_matchs": len(tous_les_matchs),
    }

    # 1. Calcul de l'âge (rapide car la liste des inscrits est petite)
    stats.update(_calculer_records_age(liste_entites))

    # 2. Calcul mutualisé des matchs en un seul passage (O(N))
    stats.update(_calculer_statistiques_matchs(tous_les_matchs, liste_entites))

    return stats


def _calculer_records_age(liste_entites: list) -> dict:
    """Trouve le plus jeune et le plus vieux très rapidement."""
    athletes_valides = [a for a in liste_entites if isinstance(a, Athlete) and a.age() is not None]
    if not athletes_valides:
        return {}

    plus_jeune = min(athletes_valides, key=lambda x: x.age() or 999)
    plus_age = max(athletes_valides, key=lambda x: x.age() or 0)

    return {
        "plus_jeune": {"nom": plus_jeune.nom, "age": plus_jeune.age()},
        "plus_age": {"nom": plus_age.nom, "age": plus_age.age()},
    }


def _calculer_statistiques_matchs(tous_les_matchs: list, liste_entites: list) -> dict:
    """
    Calcule les winrates ET la démographie en un seul passage sur les matchs.
    """
    bilan_joueurs: dict[str, Any] = {}
    bilan_prov: dict[str, Any] = {}
    repartition_prov: dict[str, Any] = {}

    valeurs_nulles = {"nan", "none", "", "aucun", "inconnu"}

    # --- Répartition des provenances des inscrits ---
    for entite in liste_entites:
        prov = getattr(entite, "provenance", None)
        if prov:
            prov_clean = str(prov).strip().lower()
            if prov_clean not in valeurs_nulles:
                # Initialisation manuelle si la clé n'existe pas
                if prov not in repartition_prov:
                    repartition_prov[prov] = 0
                repartition_prov[prov] += 1

    for match in tous_les_matchs:
        for perf in match.performances.values():
            participant = perf.participant
            pid = str(participant.id)

            # 1. Mise à jour Winrate Joueur
            if pid not in bilan_joueurs:
                # Initialisation manuelle
                bilan_joueurs[pid] = {"joues": 0, "victoires": 0, "nom": participant.nom}

            bilan_joueurs[pid]["joues"] += 1
            if perf.est_gagnant:
                bilan_joueurs[pid]["victoires"] += 1

            # 2. Mise à jour Winrate Provenance
            prov = getattr(participant, "provenance", None)

            # Gestion du cas des équipes sans provenance propre
            if not prov and isinstance(participant, Equipe) and participant.liste_athlete:
                prov = getattr(participant.liste_athlete[0], "provenance", None)

            if prov:
                prov_clean = str(prov).strip().lower()
                if prov_clean not in valeurs_nulles:
                    # Initialisation manuelle
                    if prov not in bilan_prov:
                        bilan_prov[prov] = {"joues": 0, "victoires": 0}

                    bilan_prov[prov]["joues"] += 1
                    if perf.est_gagnant:
                        bilan_prov[prov]["victoires"] += 1

    # ---  Extraction des records ---
    resultats: dict[str, Any] = {}

    # Records Joueurs
    if bilan_joueurs:
        plus_actif = max(bilan_joueurs.values(), key=lambda x: x["joues"])
        resultats["plus_actif"] = {"nom": plus_actif["nom"], "joues": plus_actif["joues"]}

        valides_wr = [p for p in bilan_joueurs.values() if p["joues"] >= 3]
        if valides_wr:
            meilleur = max(valides_wr, key=lambda x: x["victoires"] / x["joues"])
            resultats["meilleur_winrate"] = {
                "nom": meilleur["nom"],
                "winrate": (meilleur["victoires"] / meilleur["joues"]) * 100,
                "joues": meilleur["joues"],
            }

    # Records Provenances
    if repartition_prov:
        resultats["top_provenances"] = sorted(repartition_prov.items(), key=lambda x: x[1], reverse=True)[:3]

    valides_prov = {k: v for k, v in bilan_prov.items() if v["joues"] >= 3}
    if valides_prov:
        meilleur_p = max(valides_prov.items(), key=lambda x: x[1]["victoires"] / x[1]["joues"])
        resultats["meilleur_winrate_provenance"] = {
            "pays": meilleur_p[0],
            "winrate": (meilleur_p[1]["victoires"] / meilleur_p[1]["joues"]) * 100,
            "joues": meilleur_p[1]["joues"],
            "seuil": 3,
        }

    return resultats
