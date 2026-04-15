from .match import Match


class Competition:
    """
    Objet représentant un tournoi ou une ligue,
    agrégeant les différents matchs d'un sport.
    """

    def __init__(
        self,
        id_competition: int,
        nom: str,
        liste_match: list[Match] | None = None
    ) -> None:
        self.id_competition = id_competition
        self.nom = nom
        self.liste_match = liste_match if liste_match is not None else []

    def ajouter_match(self, match: Match) -> None:
        """Ajoute un match à la compétition s'il n'y est pas déjà."""
        if match not in self.liste_match:
            self.liste_match.append(match)

    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour Pandas."""
        return {
            "id_competition": self.id_competition,
            "nom": self.nom,
            "nb_matchs": len(self.liste_match)
        }

    def __str__(self) -> str:
        return f"Compétition : {self.nom} - {len(self.liste_match)} match (ID: {self.id_competition})"
