"""Implémentation de la classe Equipe"""
from .athlete import Athlete
from .coach import Coach


class Equipe:
    """
    Objet représentant les équipes participantes à la compétition du sport choisi
    """
    def __init__(
        self,
        id_equipe: int,
        nom: str,
        provenance: str | None,
    ) -> None:
        self.id_equipe = id_equipe
        self.nom = nom
        self.provenance = provenance
        self.liste_athlete: list[Athlete] | None = None,
        self.coachs: list[Coach] | None = None,

    def __str__(self) -> str:
        return f"[{self.id_equipe}, {self.nom}, {self.provenance}, {self.liste_athlete}, {self.coachs}]"

    def ajouter_membre(self, membre: Athlete) -> None:
        self.liste_athlete.append(membre)

    def ajouter_coach(self, coach: Coach) -> None:
        self.coachs.append(coach)
