from datetime import datetime
from typing import Any

from .personne import Personne


class Coach(Personne):
    """
    Objet représentant un coach, héritant de Personne.

    Attributs supplémentaires :
    specialite : str | None
        le domaine d'expertise du coach (ex: "Tactique", "Mental")
    """

    def __init__(
        self,
        nom: str,
        id_personne: str | None = None,
        prenom: str | None = None,
        provenance: str | None = None,
        pseudo: str | None = None,
        genre: str | None = None,
        role: str | None = None,
        date_naissance: datetime | None = None,
        specialite: str | None = None,
        **kwargs: Any,  # Capture les arguments supplémentaires (comme equipe_actuelle)
    ) -> None:
        super().__init__(
            nom=nom,
            prenom=prenom,
            id_personne=id_personne,
            provenance=provenance,
            pseudo=pseudo,
            genre=genre,
            role=role,
            date_naissance=date_naissance,
            **kwargs,
        )
        self.specialite = specialite

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'objet en dictionnaire pour Pandas."""
        return {
            "id_personne": self.id,
            "nom": self.nom,
            "provenance": self.provenance,
            "pseudo": self.pseudo,
            "genre": self.genre,
            "role": self.role,
            "date_naissance": self.date_naissance,
            "specialite": self.specialite,
        }

    def __str__(self) -> str:
        info_provenance = f" ({self.provenance})" if self.provenance else ""
        info_specialite = f" - Spécialité : {self.specialite}" if self.specialite else ""
        return f"Coach : {self.nom}{info_provenance}{info_specialite} - ID: {self.id}"
