from src.Analysis.statistiques import (
    _analyser_demographie_age,
    _analyser_performances_et_provenances,
    calculer_statistiques_globales,
)
from src.Model.competition import Competition
from src.Model.equipe import Equipe


class TestStatistiques:
    def test_analyser_demographie_age_complet(self, liste_participants_statistiques: list) -> None:
        # On utilise la fixture qui contient des ages varies
        resultat = _analyser_demographie_age(liste_participants_statistiques)

        assert "plus_jeune" in resultat
        assert resultat["plus_jeune"]["nom"] == "Jeune Challenger"
        assert resultat["plus_age"]["nom"] == "Vieux Champion"

    def test_analyser_demographie_liste_vide(self) -> None:
        # On garde une creation manuelle ici car on veut forcer un cas vide specifique
        resultat = _analyser_demographie_age([Equipe(nom="Seulement une equipe")])
        assert resultat == {}

    def test_analyser_performances_et_provenances_complet(
        self, competition_statistiques: Competition, liste_participants_statistiques: list
    ) -> None:
        matchs = competition_statistiques.obtenir_tous_les_matchs()
        resultat = _analyser_performances_et_provenances(matchs, liste_participants_statistiques)

        # Vérification des records (Vieux Champion a joue 3 matchs et a gagne les 3)
        assert resultat["plus_actif"]["nom"] in ["Vieux Champion", "Jeune Challenger"]
        assert resultat["plus_actif"]["joues"] == 3
        assert resultat["meilleur_winrate"]["nom"] == "Vieux Champion"
        assert resultat["meilleur_winrate"]["winrate"] == 100.0

        # Vérification des statistiques géographiques (2 Francais contre 1 Espagnol)
        assert resultat["top_provenances"][0][0] == "France"
        assert resultat["meilleur_winrate_provenance"]["pays"] == "France"
        assert resultat["meilleur_winrate_provenance"]["winrate"] == 100.0

    def test_calculer_statistiques_globales_complet(
        self, competition_statistiques: Competition, liste_participants_statistiques: list
    ) -> None:
        stats = calculer_statistiques_globales(competition_statistiques, liste_participants_statistiques)

        # Vérification que l'agrégation finale regroupe bien tout
        assert stats["total_athletes"] == 3
        assert stats["total_equipes"] == 1
        assert stats["total_matchs"] == 3
        assert "plus_jeune" in stats
        assert stats["plus_jeune"]["nom"] == "Jeune Challenger"

    def test_calculer_statistiques_globales_vide(self) -> None:
        # Cas limite lorsqu'il n'y a aucune donnée
        comp_vide = Competition(id_competition="C_VIDE", nom="Tournoi Fantome")
        stats = calculer_statistiques_globales(comp_vide, [])

        assert stats["total_athletes"] == 0
        assert stats["total_equipes"] == 0
        assert stats["total_matchs"] == 0
        assert "plus_actif" not in stats
