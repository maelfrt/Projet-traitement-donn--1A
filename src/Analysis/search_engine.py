class SearchEngine:
    """
    Responsable uniquement de la recherche d'informations.
    """
    def __init__(self, data_loader):
        self.loader = data_loader

    def chercher_athlete_par_nom(self, nom_partiel: str) -> list:
        """Retourne une liste d'objets Athlete correspondant au nom."""
        df = self.loader.base_athletes
        if df.empty or 'objet' not in df.columns:
            return []

        # On met en minuscules pour une recherche insensible à la casse
        recherche = nom_partiel.lower()

        filtre = df['objet'].apply(lambda obj: recherche in str(obj.nom).lower())

        return df.loc[filtre, 'objet'].tolist()

    def chercher_equipe_par_nom(self, nom_partiel: str) -> list:
        """Retourne une liste d'objets Equipe correspondant au nom."""
        df = self.loader.base_equipes
        if df.empty or 'objet' not in df.columns:
            return []

        recherche = nom_partiel.lower()
        filtre = df['objet'].apply(lambda obj: recherche in str(obj.nom).lower())

        return df.loc[filtre, 'objet'].tolist()
