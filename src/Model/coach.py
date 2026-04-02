from personne import Personne
from time import datetime


class Coach(Personne):

    def __init__(
        self,
        id_personne: int,
        nom: str,
        provenance: str, 
        pseudo: str, 
        genre: str, 
        role: str,
        date_naissance: datetime,
    ) -> None:
        super.__init__(
            id_personne,
            nom,
            provenance,
            pseudo, genre,
            role,
            date_naissance)

    def __str__(self) -> str:
        return f"Coach : {self.nom} ({self.pays}) - ID: {self.id_personne}"