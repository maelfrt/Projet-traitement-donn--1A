from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.Infrastructure.gestionnaire_csv import GestionnaireCSV


class TestGestionnaireCSV:
    # Chargement des fichiers

    def test_charger_fichier_succes(self, tmp_path: Path) -> None:
        """Vérifie la lecture d'un CSV et le typage automatique en texte."""
        dossier = tmp_path / "data"
        dossier.mkdir()
        fichier = dossier / "test.csv"
        fichier.write_text("id,valeur\n1,100\n2,200", encoding="utf-8")

        gestionnaire = GestionnaireCSV(str(dossier))
        df = gestionnaire.charger_fichier("test.csv")

        # On s'assure que le DataFrame est bien chargé et les données intactes
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["id"] == "1"

    def test_charger_fichier_inexistant(self) -> None:
        """Vérifie que l'absence de fichier lève bien une exception FileNotFoundError."""
        gestionnaire = GestionnaireCSV("dossier_inconnu")

        with pytest.raises(FileNotFoundError):
            gestionnaire.charger_fichier("introuvable.csv")

    # Nettoyage et mapping des colonnes

    def test_standardiser_donnees_filtrage(self) -> None:
        """Vérifie le renommage des colonnes et la suppression des données inutiles."""
        df_brut = pd.DataFrame({"NOM_JOUEUR": ["Alice", "Bob"], "AGE": [25, 30], "AUTRE": ["...", "..."]})

        mapping = {"NOM_JOUEUR": "nom", "AGE": "age"}
        gestionnaire = GestionnaireCSV("source")

        df_propre = gestionnaire.standardiser_donnees(df_brut, mapping)

        # Le résultat ne doit contenir que les colonnes définies dans le mapping
        assert list(df_propre.columns) == ["nom", "age"]
        assert df_propre.iloc[0]["nom"] == "Alice"

    def test_standardiser_donnees_partielles(self) -> None:
        """Vérifie que le système ignore les colonnes du mapping absentes du CSV."""
        df_brut = pd.DataFrame({"id": ["1"]})
        mapping = {"id": "id_technique", "cle_absente": "nom"}

        gestionnaire = GestionnaireCSV("source")
        df_propre = gestionnaire.standardiser_donnees(df_brut, mapping)

        # Seule la colonne présente dans le CSV source doit être renommée
        assert "id_technique" in df_propre.columns
        assert "nom" not in df_propre.columns

    # Ecriture sur disque

    @patch("pandas.DataFrame.to_csv")
    def test_sauvegarder_fichier_appel(self, mock_to_csv: MagicMock, tmp_path: Path) -> None:
        """Vérifie que la demande de sauvegarde est transmise à Pandas avec le bon chemin."""
        dossier = tmp_path / "output"
        dossier.mkdir()

        df = pd.DataFrame({"test": [1]})
        gestionnaire = GestionnaireCSV(str(dossier))

        gestionnaire.sauvegarder_fichier(df, "export.csv")

        # Le chemin complet doit être construit correctement par le gestionnaire
        chemin_attendu = str(dossier / "export.csv")
        mock_to_csv.assert_called_once_with(chemin_attendu, index=False)
