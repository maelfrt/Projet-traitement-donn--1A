from typing import Any

from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe


def calculer_statistiques_globales(competition: Competition, liste_entites: list) -> dict:
    """Analyse la compétition et les participants pour générer des records globaux."""
    stats: dict[str, Any] = {}

    stats["total_athletes"] = sum(1 for e in liste_entites if isinstance(e, Athlete))
    stats["total_equipes"] = sum(1 for e in liste_entites if isinstance(e, Equipe))

    # Extraction de tous les matchs
    def extraire_matchs(comp: Competition) -> list:
        matchs = list(comp.liste_match)
        for sous_comp in comp.sous_competitions.values():
            matchs.extend(extraire_matchs(sous_comp))
        return matchs

    tous_les_matchs = extraire_matchs(competition)
    stats["total_matchs"] = len(tous_les_matchs)

    # Records d'Âge (Uniquement sur les objets Athlete)
    athletes_valides = [a for a in liste_entites if isinstance(a, Athlete) and a.age() is not None]
    if athletes_valides:
        plus_jeune = min(athletes_valides, key=lambda x: x.age() or 999)
        plus_age = max(athletes_valides, key=lambda x: x.age() or 0)

        stats["plus_jeune"] = {"nom": plus_jeune.nom, "age": plus_jeune.age()}
        stats["plus_age"] = {"nom": plus_age.nom, "age": plus_age.age()}

    # Records de Performance (Winrate et Activité)
    bilan = {}
    for match in tous_les_matchs:
        for perf in match.performances.values():
            part_id = str(perf.participant.id)
            if part_id not in bilan:
                bilan[part_id] = {"nom": perf.participant.nom, "joues": 0, "victoires": 0}

            bilan[part_id]["joues"] += 1
            if perf.est_gagnant:
                bilan[part_id]["victoires"] += 1

    if bilan:
        # Le plus actif (celui qui a joué le plus de matchs)
        plus_actif = max(bilan.values(), key=lambda x: x["joues"])
        stats["plus_actif"] = {"nom": plus_actif["nom"], "joues": plus_actif["joues"]}

        # Le meilleur Winrate (au moins 3 matchs joués)
        valides_winrate = [p for p in bilan.values() if p["joues"] >= 3]
        if valides_winrate:
            meilleur_wr = max(valides_winrate, key=lambda x: (x["victoires"] / x["joues"], x["joues"]))
            stats["meilleur_winrate"] = {
                "nom": meilleur_wr["nom"],
                "winrate": (meilleur_wr["victoires"] / meilleur_wr["joues"]) * 100,
                "joues": meilleur_wr["joues"],
            }
    # Analyse Démographique et Géographique (Provenance)
    repartition_provenance: dict[str, Any] = {}
    bilan_provenance = {}

    # Compter les représentants par provenance
    for entite in liste_entites:
        prov = getattr(entite, "provenance", None)
        if prov and str(prov).strip().lower() not in ["nan", "none", "", "aucun", "inconnu"]:
            repartition_provenance[prov] = repartition_provenance.get(prov, 0) + 1

    if repartition_provenance:
        # On trie pour avoir le Top 3
        top_provenances = sorted(repartition_provenance.items(), key=lambda x: x[1], reverse=True)[:3]
        stats["top_provenances"] = top_provenances

    # Calculer le Winrate par provenance
    for match in tous_les_matchs:
        for perf in match.performances.values():
            participant = perf.participant
            prov = getattr(participant, "provenance", None)

            provenance_invalide = not prov or str(prov).lower() in ["nan", "none", "", "aucun", "inconnu"]

            possede_joueurs = hasattr(participant, "liste_athlete") and participant.liste_athlete

            if provenance_invalide and possede_joueurs:
                prov = getattr(participant.liste_athlete[0], "provenance", None)

            if prov and str(prov).strip().lower() not in ["nan", "none", "", "aucun", "inconnu"]:
                if prov not in bilan_provenance:
                    bilan_provenance[prov] = {"joues": 0, "victoires": 0}

                bilan_provenance[prov]["joues"] += 1
                if perf.est_gagnant:
                    bilan_provenance[prov]["victoires"] += 1

    if bilan_provenance:
        MIN_MATCHS = 3
        valides_prov = {k: v for k, v in bilan_provenance.items() if v["joues"] >= MIN_MATCHS}

        if valides_prov:
            meilleure_prov = max(valides_prov.items(), key=lambda x: x[1]["victoires"] / x[1]["joues"])
            stats["meilleur_winrate_provenance"] = {
                "pays": meilleure_prov[0],
                "winrate": (meilleure_prov[1]["victoires"] / meilleure_prov[1]["joues"]) * 100,
                "joues": meilleure_prov[1]["joues"],
                "seuil": MIN_MATCHS,
            }

    return stats
