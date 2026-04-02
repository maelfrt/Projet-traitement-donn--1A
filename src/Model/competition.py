"Implémentation de la classe Compétition"
from .match import Match


class Competition:
    """Objet agrégeant les différents matchs d'un sport"""
    def __init__(
        self,
        id_competition: int,
        nom: str,
        liste_match: list[Match]
    ) -> None:
        self.