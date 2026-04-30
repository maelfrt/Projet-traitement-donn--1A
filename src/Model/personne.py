from abc import abstractmethod
from datetime import UTC, datetime
from typing import Any

from .participant import Participant


class Personne(Participant):
    """
    Objet représentant les participants humains à une compétition (athlètes et coachs).
    Hérite de Participant pour la gestion de l'ID et du Nom.

    Parameters
    ----------
    id_personne : int
        identifiant unique de la personne
    nom : str
        nom et prénom de la personne
    provenance : str | None
        drapeau ou pays sous lequel il concourt
    pseudo :  str | None
        pseudo de la personne
    genre : str | None
        genre sous lequel concourt la personne
    date_naissance : datetime | None
        date de naissance de la personne
    role : str | None
        poste de la personne
    """

    def __init__(
        self,
        nom: str,
        prenom: str | None = None,
        id_personne: str | None = None,
        provenance: str | None = None,
        pseudo: str | None = None,
        genre: str | None = None,
        role: str | None = None,
        date_naissance: datetime | str | None = None,
        lieu_naissance: str | None = None,
        **kwargs: Any,
    ) -> None:
        nom_complet = f"{prenom} {nom}" if prenom else nom

        super().__init__(nom=nom_complet, id_participant=id_personne, **kwargs)

        self.prenom = prenom
        self.provenance = provenance
        self.pseudo = pseudo
        self.genre = genre
        self.role = role

        self.date_naissance = None
        if isinstance(date_naissance, datetime):
            self.date_naissance = date_naissance
        elif isinstance(date_naissance, str):
            try:
                date_pure = str(date_naissance).strip().split(" ")[0]
                self.date_naissance = datetime.strptime(date_pure, "%Y-%m-%d").replace(tzinfo=UTC)
            except (ValueError, IndexError):
                pass

        self.lieu_naissance = lieu_naissance

    @abstractmethod
    def __str__(self) -> str:
        """Méthode abstraite à implémenter dans Athlete et Coach."""
