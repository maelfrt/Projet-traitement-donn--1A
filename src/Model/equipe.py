from typing import Any

from .athlete import Athlete
from .coach import Coach
from .participant import Participant


class Equipe(Participant):
    """
    Objet représentant un collectif (club, nation) participant à la compétition.
    Hérite de la classe Participant pour la gestion de l'identité et du nom.

    Parameters
    ----------
    nom : str
        Le nom officiel de l'équipe (ex: "Équipe de France", "Lakers").
    id_equipe : str | None
        L'identifiant unique de l'équipe pour le système.
    provenance : str | None
        La région, ville ou pays d'origine de l'équipe.
    **kwargs : Any
        Données supplémentaires provenant de la configuration (ex: ville, stade).
    """

    def __init__(
        self,
        nom: str,
        id_equipe: str | None = None,
        provenance: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Initialisation via la classe mère Participant
        super().__init__(nom=nom, id_participant=id_equipe, **kwargs)

        self.provenance = provenance

        self.liste_athlete: list[Athlete] = []
        self.coachs: list[Coach] = []

    def ajouter_membre(self, membre: Athlete) -> None:
        """
        Inscrit un nouvel athlète dans l'effectif de l'équipe.
        """
        if membre not in self.liste_athlete:
            self.liste_athlete.append(membre)

    def ajouter_coach(self, coach: Coach) -> None:
        """
        Associe un nouvel entraîneur à l'encadrement de l'équipe.
        """
        if coach not in self.coachs:
            self.coachs.append(coach)

    def effectif_total(self) -> int:
        """
        Calcule le nombre total de personnes rattachées à l'équipe.

        Renvoie
        -------
        int
            Somme des athlètes et des entraîneurs.
        """
        return len(self.liste_athlete) + len(self.coachs)

    def to_dict(self) -> dict[str, Any]:
        """
        Convertit l'équipe en dictionnaire pour permettre son affichage ou
        son traitement statistique via Pandas.

        Renvoie
        -------
        dict[str, Any]
            Dictionnaire récapitulant les informations clés de l'équipe.
        """
        return {
            "id_participant": self.id,
            "nom": self.nom,
            "provenance": self.provenance,
            "nb_athletes": len(self.liste_athlete),
            "nb_coachs": len(self.coachs),
            # On génère une chaîne simple listant les noms pour faciliter la lecture
            "noms_athletes": ", ".join([a.nom for a in self.liste_athlete]),
        }

    def __str__(self) -> str:
        prov = f" ({self.provenance})" if self.provenance else ""
        return f"Équipe : {self.nom}{prov} - {len(self.liste_athlete)} athlète(s) - ID: {self.id}"
