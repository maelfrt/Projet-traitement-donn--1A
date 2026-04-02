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