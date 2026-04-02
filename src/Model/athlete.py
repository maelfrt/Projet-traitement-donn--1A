<<<<<<< HEAD
from typing import Union
from src.Common.utils import parse_boolean


class Player:
    def __init__(self, id: int, full_name: str, is_the_goat: Union[str, bool]):
        self.id = id
        self.full_name = full_name
        self.is_the_goat = parse_boolean(is_the_goat)

    def __repr__(self):
        display_string = self.full_name
        if self.is_the_goat:
            display_string += " (GOAT)"
        return display_string
=======
from personne import Personne
from time import datetime


class Athlete(Personne):

    def __init__(
        self,
        id_personne: int,
        nom: str,
        provenance: str, 
        pseudo: str, 
        genre: str, 
        role: str,
        date_naissance: datetime,
        taille, poids: float
    ) -> None:
        super.__init__(
            id_personne,
            nom,
            provenance,
            pseudo, genre,
            role,
            date_naissance)
        self.taille = taille
        self.poids = poids

    def __str__(self) -> str:
        return f"Athlète : {self.nom} ({self.pays}) - ID: {self.id_personne}"
>>>>>>> 1089b7bd745a09ef037d1b52c63f25eae229d4f1
