from datetime import UTC, datetime
from unittest.mock import patch

from src.Model.athlete import Athlete


class TestAthlete:
    # Initialisation et héritage de la classe abstraite Personne

    def test_initialisation_dates_et_attributs_etendus(self, athlete_standard: Athlete) -> None:
        """Vérifie le décodage des dates hérité de Personne et la capture des kwargs."""
        assert athlete_standard.date_naissance is not None
        assert athlete_standard.date_naissance.year == 1990
        assert athlete_standard.date_naissance.month == 5

        date_native = datetime(1990, 5, 15, tzinfo=UTC)
        athlete_native = Athlete(nom="Dupont", date_naissance=date_native, donnee_bonus="test")
        assert athlete_native.date_naissance == date_native
        assert athlete_native.donnees_complementaires["donnee_bonus"] == "test"

        athlete_invalide = Athlete(nom="Dupont", date_naissance="Format Inconnu")
        assert athlete_invalide.date_naissance is None

    # Logique spécifique à l athlète

    @patch("src.Model.athlete.datetime")
    def test_age_calcul_dynamique(self, mock_datetime, athlete_standard: Athlete) -> None:
        """Vérifie le calcul de l âge selon que l anniversaire est passé ou non dans l année en cours."""
        # Fixation temporelle au 1er Juillet 2024 pour garantir des tests déterministes
        mock_datetime.now.return_value = datetime(2024, 7, 1, tzinfo=UTC)
        mock_datetime.strptime = datetime.strptime

        # L athlète standard est né en mai 1990
        assert athlete_standard.age() == 34

        # Test d un anniversaire à venir dans l année fixée
        athlete_futur = Athlete(nom="B", date_naissance="1990-08-15")
        assert athlete_futur.age() == 33

        # Test d absence de données
        athlete_sans_date = Athlete(nom="C")
        assert athlete_sans_date.age() is None

    def test_calculer_imc_conversion_et_securite(self, athlete_standard: Athlete) -> None:
        """Vérifie l algorithme de calcul de l IMC et ses sécurités."""
        # L athlète standard fait 185 cm pour 80 kg
        assert athlete_standard.calculer_imc() == 23.4

        # Test avec une taille déjà exprimée en mètres
        athlete_m = Athlete(nom="B", taille=1.85, poids=80.0)
        assert athlete_m.calculer_imc() == 23.4

        # Tests de robustesse et de rejet
        assert Athlete(nom="C", taille=0, poids=80.0).calculer_imc() is None
        assert Athlete(nom="D", taille="Texte", poids=80.0).calculer_imc() is None  # type: ignore
        assert Athlete(nom="E").calculer_imc() is None

    # Exportation et présentation

    def test_to_dict_complet(self, athlete_standard: Athlete) -> None:
        """Vérifie la sérialisation de l athlète incluant l exécution des méthodes de calcul."""
        dico = athlete_standard.to_dict()

        assert dico["nom_complet"] == "Jean Dupont"
        assert dico["id_participant"] == "P001"
        assert dico["imc"] == 23.4

    def test_str_affichage_dynamique(self, athlete_standard: Athlete) -> None:
        """Vérifie l adaptation de la présentation textuelle selon les données disponibles."""
        athlete_standard.provenance = "FRA"
        texte_complet = str(athlete_standard)

        assert "Jean Dupont" in texte_complet
        assert "(FRA)" in texte_complet
        assert "ID: P001" in texte_complet

        athlete_simple = Athlete(nom="Zidane", id_personne="P2")
        texte_simple = str(athlete_simple)

        assert "Zidane" in texte_simple
        assert "()" not in texte_simple
