import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class Personne(ABC):
    """
    Objet représentant les participants à une compétition : athlètes et coachs.

    Parameters :
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
        date_naissance: datetime | None = None,
        lieu_naissance: str | None = None,
    ) -> None:
        if id_personne is None or id_personne == "":
            self.id_personne = str(uuid.uuid4())
        else:
            self.id_personne = id_personne

        if prenom:
            self.nom = f"{prenom} {nom}"
        else:
            self.nom = nom

        self.provenance = provenance
        self.pseudo = pseudo
        self.genre = genre
        self.date_naissance = date_naissance
        self.lieu_naissance = lieu_naissance
        self.role = role

    @abstractmethod
    def __str__(self) -> str:
        ...
