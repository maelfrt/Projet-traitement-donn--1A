from src.Model.athlete import Athlete
from src.Model.coach import Coach
from src.Model.equipe import Equipe


class TestEquipe:
    # Initialisation et attributs de base

    def test_initialisation_equipe(self, equipe_standard: Equipe) -> None:
        """Vérifie l'affectation correcte des attributs hérités et spécifiques."""
        assert equipe_standard.nom == "Lakers"
        assert equipe_standard.id == "E01"
        assert equipe_standard.provenance == "USA"
        assert equipe_standard.liste_athlete == []
        assert equipe_standard.coachs == []

    # Gestion des effectifs

    def test_ajouter_membre_sans_doublon(self, equipe_standard: Equipe, athlete_standard: Athlete) -> None:
        """Vérifie le blocage des inscriptions multiples pour un même joueur."""
        equipe_standard.ajouter_membre(athlete_standard)
        equipe_standard.ajouter_membre(athlete_standard)

        assert len(equipe_standard.liste_athlete) == 1
        assert equipe_standard.liste_athlete[0] == athlete_standard

    def test_ajouter_coach_sans_doublon(self, equipe_standard: Equipe, coach_standard: Coach) -> None:
        """Vérifie le blocage des affectations multiples pour le staff technique."""
        equipe_standard.ajouter_coach(coach_standard)
        equipe_standard.ajouter_coach(coach_standard)

        assert len(equipe_standard.coachs) == 1
        assert equipe_standard.coachs[0] == coach_standard

    def test_effectif_total(self, equipe_standard: Equipe, athlete_standard: Athlete, coach_standard: Coach) -> None:
        """Vérifie le calcul global des ressources humaines rattachées à l'équipe."""
        equipe_standard.ajouter_membre(athlete_standard)
        equipe_standard.ajouter_coach(coach_standard)

        assert equipe_standard.effectif_total() == 2

    # Exportation et formatage

    def test_to_dict_formatage(self, equipe_standard: Equipe, athlete_standard: Athlete, coach_standard: Coach) -> None:
        """Vérifie la sérialisation de l'équipe et la concaténation textuelle des joueurs pour Pandas."""
        equipe_standard.ajouter_membre(athlete_standard)
        equipe_standard.ajouter_coach(coach_standard)

        dico = equipe_standard.to_dict()

        assert dico["id_participant"] == "E01"
        assert dico["nom"] == "Lakers"
        assert dico["provenance"] == "USA"
        assert dico["nb_athletes"] == 1
        assert dico["nb_coachs"] == 1

        # Le nom complet construit par la classe parente Personne est testé ici
        assert dico["noms_athletes"] == "Jean Dupont"

    def test_str_affichage_dynamique(self, equipe_standard: Equipe) -> None:
        """Vérifie l'adaptation de la chaîne textuelle selon la présence ou l'absence de provenance."""
        # Test avec une provenance définie
        texte_complet = str(equipe_standard)
        assert "Lakers (USA)" in texte_complet
        assert "0 athlète(s)" in texte_complet
        assert "ID: E01" in texte_complet

        # Test sans provenance
        equipe_sans_prov = Equipe(nom="FC Sans Ville", id_equipe="E02")
        texte_reduit = str(equipe_sans_prov)
        assert "FC Sans Ville" in texte_reduit
        assert "()" not in texte_reduit
        assert "ID: E02" in texte_reduit
