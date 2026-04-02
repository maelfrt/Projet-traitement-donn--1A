from time import datetime
from abc import ABC, abstractmethod


class Personne(ABC):
    """
    Objet représentant les participants à une compatitions : athlètes et coachs

    Parameters :
    id_personne : int
        identifiant unique de la personne
    nom : str
        nom et prénom de la personne
    provenance : str
        drapeau sous lequel il concourt
    pseudo :  str | None
        pseudo de la personne
    genre : str | None
        genre sous lequel concourt la personne
    date_naissance : datetime
        date de naissance de la personne
    role : str | None
        poste de la personne
    """
    def __init__(
        self,
        id_personne: int,
        nom: str,
        provenance: str,
        pseudo: str,
        genre: str,
        role: str,
        date_naissance: datetime.date,
    ) -> None:
        self.id_personne = id_personne
        self.nom = nom
        self.provenance: str | None = provenance
        self.pseudo: str | None = pseudo
        self.genre: str | None = genre
        self.date_naissance = date_naissance
        self.role: str | None = role

    @abstractmethod
    def __str__() -> str:
        ...
    
