from typing import Any

from .athlete import Athlete
from .coach import Coach
from .participant import Participant


class Equipe(Participant):
    """
    Objet représentant les équipes participantes à la compétition.
    Hérite de Participant pour la gestion de l'ID et du Nom.
    """
    def __init__(
        self,
        nom: str,
        id_equipe: str | None = None,
        provenance: str | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(nom=nom, id_participant=id_equipe, **kwargs)
        self.provenance = provenance
        self.liste_athlete: list[Athlete] = []
        self.coachs: list[Coach] = []

    def ajouter_membre(self, membre: Athlete) -> None:
        """Ajoute un athlète à l'équipe s'il n'y est pas déjà."""
        if membre not in self.liste_athlete:
            self.liste_athlete.append(membre)

    def ajouter_coach(self, coach: Coach) -> None:
        """Ajoute un coach à l'équipe s'il n'y est pas déjà."""
        if coach not in self.coachs:
            self.coachs.append(coach)

    def effectif_total(self) -> int:
        """Retourne le nombre total de personnes dans l'équipe (athlètes + coachs)."""
        return len(self.liste_athlete) + len(self.coachs)

    def to_dict(self) -> dict:
        """
        Convertit l'équipe en dictionnaire pour Pandas.
        On met à jour les clés pour correspondre au nouveau Participant.
        """
        return {
            "id_participant": self.id,
            "nom": self.nom,
            "provenance": self.provenance,
            "nb_athletes": len(self.liste_athlete),
            "nb_coachs": len(self.coachs),
            "noms_athletes": ", ".join([a.nom for a in self.liste_athlete])
        }

    def __str__(self) -> str:
        prov = f" ({self.provenance})" if self.provenance else ""
        return f"Équipe : {self.nom}{prov} - {len(self.liste_athlete)} athlète(s) - ID: {self.id}"
