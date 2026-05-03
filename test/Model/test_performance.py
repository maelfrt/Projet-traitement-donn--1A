from src.Model.athlete import Athlete
from src.Model.performance import Performance


class TestPerformance:
    # Initialisation et gestion des attributs

    def test_initialisation_valeurs_par_defaut(self, athlete_standard: Athlete) -> None:
        """Verifie que les dictionnaires et listes sont bien instancies par defaut."""
        perf = Performance(participant=athlete_standard, role="Remplaçant")

        assert perf.participant == athlete_standard
        assert perf.role == "Remplaçant"
        assert perf.est_gagnant is False
        assert perf.est_nul is False
        assert perf.stats == {}
        assert perf.joueurs_match == []

    def test_initialisation_parametres_complets(self, athlete_standard: Athlete) -> None:
        """Verifie l affectation des parametres optionnels lors de la creation."""
        stats = {"points": 35}
        perf = Performance(participant=athlete_standard, role="Meneur", est_gagnant=True, est_nul=False, stats=stats)

        assert perf.est_gagnant is True
        assert perf.stats["points"] == 35

    def test_ajouter_stat(self, performance_gagnante: Performance) -> None:
        """Verifie l ajout dynamique de nouvelles statistiques en cours de route."""
        # La fixture performance_gagnante a deja des points egaux a 25
        performance_gagnante.ajouter_stat("rebonds", 10)

        assert "rebonds" in performance_gagnante.stats
        assert performance_gagnante.stats["rebonds"] == 10
        assert performance_gagnante.stats["points"] == 25

    def test_joueurs_match_ajout(self, performance_gagnante: Performance, athlete_standard: Athlete) -> None:
        """Verifie que l on peut lier des joueurs specifiques a cette performance collective."""
        performance_gagnante.joueurs_match.append(athlete_standard)

        assert len(performance_gagnante.joueurs_match) == 1
        assert performance_gagnante.joueurs_match[0] == athlete_standard

    # Affichage textuel

    def test_to_dict_formatage(self, performance_gagnante: Performance) -> None:
        """Verifie la fusion des attributs de base et des statistiques dans un dictionnaire plat."""
        dico = performance_gagnante.to_dict()

        # Verifications des attributs racines
        assert dico["id_participant"] == "P001"
        assert dico["nom_participant"] == "Jean Dupont"
        assert dico["role"] == "Domicile"
        assert dico["est_gagnant"] is True
        assert dico["est_nul"] is False

        # Verification de l aplatissement des statistiques
        assert "points" in dico
        assert dico["points"] == 25

    def test_str_affichage_dynamique(self, athlete_standard: Athlete) -> None:
        """Verifie l adaptation du texte selon le resultat du match victoire match nul ou defaite."""
        # Verification du cas de victoire
        perf_victoire = Performance(participant=athlete_standard, role="Dom", est_gagnant=True)
        assert "Victoire" in str(perf_victoire)

        # Verification du cas de match nul
        perf_nul = Performance(participant=athlete_standard, role="Dom", est_nul=True)
        assert "Match nul" in str(perf_nul)

        # Verification du cas de defaite
        perf_defaite = Performance(participant=athlete_standard, role="Dom", est_gagnant=False, est_nul=False)
        assert "Défaite" in str(perf_defaite)
