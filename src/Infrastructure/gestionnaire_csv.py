from pathlib import Path

import pandas as pd


class GestionnaireCSV:
    """
    Classe responsable de l'accès aux données (DAO).
    Elle lit les fichiers CSV et standardise leurs colonnes grâce à un mapping,
    sans jamais avoir besoin de connaître le sport traité.
    """

    def __init__(self, dossier_source: str) -> None:
        self.dossier_source = Path(dossier_source)

    def charger_fichier(self, nom_fichier: str) -> pd.DataFrame:
        """Charge un fichier CSV brut depuis le dossier source."""
        chemin_complet = self.dossier_source / nom_fichier

        if not chemin_complet.exists():
            raise FileNotFoundError(f"Le fichier {chemin_complet} est introuvable.")

        return pd.read_csv(chemin_complet, dtype=str)

    def standardiser_donnees(self, df: pd.DataFrame, colonnes_type: dict[str, str]) -> pd.DataFrame:
        """
        Cette fonction renomme les colonnes du CSV brut
        pour qu'elles correspondent exactement aux attributs des classes.

        Exemple de mapping reçu : {"Nom du Joueur": "nom", "ID_J": "id_personne"}
        """
        df_propre = df.rename(columns=colonnes_type)

        colonnes_a_garder = list(colonnes_type.values())

        colonnes_existantes = [col for col in colonnes_a_garder if col in df_propre.columns]

        return df_propre[colonnes_existantes]

    def sauvegarder_fichier(self, df: pd.DataFrame, nom_fichier: str) -> None:
        """Sauvegarde un DataFrame mis à jour dans un fichier CSV pour l'admin."""
        chemin_complet = self.dossier_source / nom_fichier
        df.to_csv(str(chemin_complet), index=False)
        print(f"Fichier sauvegardé : {nom_fichier}")
