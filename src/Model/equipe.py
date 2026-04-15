from .athlete import Athlete
from .coach import Coach


class Equipe:
    """
    Objet représentant les équipes participantes à la compétition.
    """
    def __init__(
        self,
        id_equipe: int,
        nom: str,
        provenance: str | None = None,
        liste_athlete: list[Athlete] | None = None,
        coachs: list[Coach] | None = None,
    ) -> None:
        self.id_equipe = id_equipe
        self.nom = nom
        self.provenance = provenance
        self.liste_athlete = liste_athlete if liste_athlete is not None else []
        self.coachs = coachs if coachs is not None else []

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
        """
        return {
            "id_equipe": self.id_equipe,
            "nom": self.nom,
            "provenance": self.provenance,
            "nb_athletes": len(self.liste_athlete),
            "nb_coachs": len(self.coachs),
            "noms_athletes": ", ".join([a.nom for a in self.liste_athlete])
        }

    def __str__(self) -> str:
        prov = f" ({self.provenance})" if self.provenance else ""
        return f"Équipe : {self.nom}{prov} - {len(self.liste_athlete)} athlète(s) - ID: {self.id_equipe}"
