from pathlib import Path
from unittest.mock import patch

from src.UI.menus import demander_saisie, selectionner_role, selectionner_sport


class TestMenus:
    @patch("src.UI.menus.input", side_effect=["1"])
    def test_demander_saisie_standard(self, mock_input) -> None:
        """Verifie que la saisie utilisateur est bien recuperee"""
        resultat = demander_saisie("Question ?")
        assert resultat == "1"

    @patch("src.UI.menus.input", side_effect=["1"])
    def test_selectionner_role_admin(self, mock_input) -> None:
        """Verifie que le choix 1 renvoie bien le role admin"""
        role = selectionner_role()
        assert role == "admin"

    @patch("src.UI.menus.input", side_effect=["2"])
    def test_selectionner_role_spectateur(self, mock_input) -> None:
        """Verifie que le choix 2 renvoie bien le role spectateur"""
        role = selectionner_role()
        assert role == "spectateur"

    @patch("src.UI.menus.input", side_effect=["0"])
    def test_selectionner_sport_quitter(self, mock_input) -> None:
        """Verifie que le choix 0 permet de sortir de la selection"""
        fichiers = [Path("config_foot.json")]
        resultat = selectionner_sport(fichiers)
        assert resultat is None

    @patch("src.UI.menus.input", side_effect=["1"])
    def test_selectionner_sport_valide(self, mock_input) -> None:
        """Verifie que selectionner un numero de la liste renvoie le bon fichier"""
        fichiers = [Path("config_basket.json")]
        resultat = selectionner_sport(fichiers)
        assert resultat == "config_basket.json"

    @patch("src.UI.menus.input", side_effect=["5", "1"])
    def test_selectionner_sport_erreur_puis_valide(self, mock_input) -> None:
        """Verifie que le menu boucle si l utilisateur tape un mauvais numero au debut"""
        fichiers = [Path("config_tennis.json")]
        # L'utilisateur se trompe (5), puis choisit le bon (1)
        resultat = selectionner_sport(fichiers)
        assert resultat == "config_tennis.json"
