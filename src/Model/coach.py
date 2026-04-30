from datetime import datetime
from typing import Any

from .personne import Personne


class Coach(Personne):
    """
    Objet représentant un entraîneur ou un membre du staff technique.
    Hérite de Personne pour la gestion de l'identité et des informations de base.

    Parameters
    ----------
    nom : str
        Le nom de famille du coach.
    prenom : str | None
        Le prénom du coach.
    id_personne : str | None
        L'identifiant unique utilisé pour le suivi technique.
    provenance : str | None
        Le pays ou la région d'origine.
    pseudo : str | None
        Nom d'usage ou pseudonyme (courant en E-sport).
    genre : str | None
        Le genre du coach.
    role : str | None
        La position ou le rôle dans le sport.
    date_naissance : datetime | str | None
        La date de naissance (format objet datetime ou texte YYYY-MM-DD).
    specialite : str | None
        Le domaine d'expertise spécifique (ex: "Tactique", "Mental").
    **kwargs : Any
        Permet de recevoir d'autres données spécifiques sans bloquer le code.
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
        date_naissance: datetime | str | None = None,
        specialite: str | None = None,
        **kwargs: Any,
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
        """
        Transforme le coach en dictionnaire pour l'affichage ou l'export.


        Renvoie
        -------
        dict[str, Any]
            Dictionnaire contenant les caractéristiques du coach.
        """
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
