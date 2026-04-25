from typing import Any

from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe


def calculer_statistiques_globales(competition: Competition, liste_entites: list) -> dict:
    """Fonction principale, agissant comme un chef d'orchestre très lisible."""
    tous_les_matchs = competition.obtenir_tous_les_matchs()

    stats: dict[str, Any] = {
        "total_athletes": sum(1 for e in liste_entites if isinstance(e, Athlete)),
        "total_equipes": sum(1 for e in liste_entites if isinstance(e, Equipe)),
        "total_matchs": len(tous_les_matchs),
    }

    # On fusionne les résultats des petits modules spécialisés
    stats.update(_calculer_records_age(liste_entites))
    stats.update(_calculer_records_winrate(tous_les_matchs))
    stats.update(_calculer_demographie(liste_entites, tous_les_matchs))

    return stats


# ==========================================
# SOUS-FONCTIONS SPÉCIALISÉES
# ==========================================


def _calculer_records_age(liste_entites: list) -> dict:
    """Ne s'occupe QUE de trouver le plus jeune et le plus vieux."""
    athletes_valides = [a for a in liste_entites if isinstance(a, Athlete) and a.age() is not None]
    if not athletes_valides:
        return {}

    plus_jeune = min(athletes_valides, key=lambda x: x.age() or 999)
    plus_age = max(athletes_valides, key=lambda x: x.age() or 0)

    return {
        "plus_jeune": {"nom": plus_jeune.nom, "age": plus_jeune.age()},
        "plus_age": {"nom": plus_age.nom, "age": plus_age.age()},
    }


def _calculer_records_winrate(tous_les_matchs: list) -> dict:
    """Ne s'occupe QUE de l'activité et des taux de victoires."""
    bilan: dict[str, dict[str, Any]] = {}

    for match in tous_les_matchs:
        for perf in match.performances.values():
            pid = str(perf.participant.id)
            if pid not in bilan:
                bilan[pid] = {"nom": perf.participant.nom, "joues": 0, "victoires": 0}

            bilan[pid]["joues"] += 1
            if perf.est_gagnant:
                bilan[pid]["victoires"] += 1

    if not bilan:
        return {}

    resultats = {}
    plus_actif = max(bilan.values(), key=lambda x: int(x["joues"]))
    resultats["plus_actif"] = {"nom": plus_actif["nom"], "joues": plus_actif["joues"]}

    valides_wr = [p for p in bilan.values() if int(p["joues"]) >= 3]
    if valides_wr:
        meilleur = max(valides_wr, key=lambda x: (x["victoires"] / x["joues"], x["joues"]))
        resultats["meilleur_winrate"] = {
            "nom": meilleur["nom"],
            "winrate": (meilleur["victoires"] / meilleur["joues"]) * 100,
            "joues": meilleur["joues"],
        }
    return resultats


def _calculer_demographie(liste_entites: list, tous_les_matchs: list) -> dict:
    """Ne s'occupe QUE des pays/provenances."""
    repartition: dict[str, int] = {}
    bilan_prov: dict[str, dict[str, Any]] = {}

    for entite in liste_entites:
        prov = getattr(entite, "provenance", None)
        if prov and str(prov).strip().lower() not in ["nan", "none", "", "aucun", "inconnu"]:
            repartition[prov] = repartition.get(prov, 0) + 1

    for match in tous_les_matchs:
        for perf in match.performances.values():
            participant = perf.participant
            prov = getattr(participant, "provenance", None)

            if (
                (not prov or str(prov).lower() in ["nan", "none", ""])
                and isinstance(participant, Equipe)
                and participant.liste_athlete
            ):
                prov = getattr(participant.liste_athlete[0], "provenance", None)

            if prov and str(prov).strip().lower() not in ["nan", "none", "", "aucun", "inconnu"]:
                if prov not in bilan_prov:
                    bilan_prov[prov] = {"joues": 0, "victoires": 0}
                bilan_prov[prov]["joues"] += 1
                if perf.est_gagnant:
                    bilan_prov[prov]["victoires"] += 1

    resultats: dict[str, Any] = {}
    if repartition:
        resultats["top_provenances"] = sorted(repartition.items(), key=lambda x: x[1], reverse=True)[:3]

    valides_prov = {k: v for k, v in bilan_prov.items() if v["joues"] >= 3}
    if valides_prov:
        meilleur = max(valides_prov.items(), key=lambda x: x[1]["victoires"] / x[1]["joues"])
        resultats["meilleur_winrate_provenance"] = {
            "pays": meilleur[0],
            "winrate": (meilleur[1]["victoires"] / meilleur[1]["joues"]) * 100,
            "joues": meilleur[1]["joues"],
            "seuil": 3,
        }
    return resultats
