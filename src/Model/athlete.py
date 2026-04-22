from datetime import UTC, datetime
from typing import Any

import pandas as pd

from .personne import Personne


class Athlete(Personne):
    """
    Objet représentant un athlète complet.
    Hérite de Personne (et donc de Participant) pour la gestion de l'identité.
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
        equipe_actuelle: str | None = None,
        taille: float | None = None,
        poids: float | None = None,
        **kwargs: Any
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
            lieu_naissance=lieu_naissance,
            **kwargs
        )
        self.taille = taille  # en cm
        self.poids = poids    # en kg
        self.equipe_actuelle = equipe_actuelle

    def age(self) -> int | None:
        """Calcule l'âge de l'athlète à partir de sa date de naissance."""
        if not self.date_naissance or str(self.date_naissance).lower() in ["nan", "none", ""]:
            return None

        try:
            # Nettoyage et conversion
            date_str = str(self.date_naissance).strip().removesuffix(".0")
            date_obj = pd.to_datetime(date_str)

            aujourdhui = datetime.now(UTC).date()

            naissance = date_obj.date()

            # Calcul de l'âge (ajuste si l'anniversaire n'est pas encore passé cette année)
            return aujourdhui.year - naissance.year - (
                (aujourdhui.month, aujourdhui.day) < (naissance.month, naissance.day)
            )
        except (ValueError, TypeError, AttributeError):
            return None

    def calculer_imc(self) -> float | None:
        """Calcule l'Indice de Masse Corporelle (IMC)."""
        if self.taille and self.poids and self.taille > 0:
            taille_metres = self.taille / 100
            return round(self.poids / (taille_metres ** 2), 2)
        return None

    def to_dict(self) -> dict:
        """
        Convertit l'objet en dictionnaire pour Pandas.
        On utilise self.id (hérité de Participant) pour la cohérence.
        """
        return {
            "id_participant": self.id,
            "nom_complet": self.nom,
            "provenance": self.provenance,
            "pseudo": self.pseudo,
            "genre": self.genre,
            "role": self.role,
            "date_naissance": self.date_naissance,
            "taille": self.taille,
            "poids": self.poids,
            "imc": self.calculer_imc(),
            "equipe_actuelle": self.equipe_actuelle
        }

    def __str__(self) -> str:
        info_provenance = f" ({self.provenance})" if self.provenance else ""
        return f"Athlète : {self.nom}{info_provenance} - ID: {self.id}"
