from typing import Any

from .participant import Participant


class Performance:
    """
    Objet faisant le lien entre un participant (Athlète ou Équipe) et un Match.
    Contient l'objet Participant complet, le résultat et les statistiques.
    """

    def __init__(
        self,
        participant: Participant,
        role: str,
        est_gagnant: bool = False,
        stats: dict[str, Any] | None = None
    ) -> None:
        self.participant: Participant = participant
        self.role: str = role
        self.est_gagnant: bool = est_gagnant
        self.stats: dict[str, Any] = stats if stats is not None else {}

    def ajouter_stat(self, cle: str, valeur: Any) -> None:
        """Ajoute ou met à jour une statistique spécifique."""
        self.stats[cle] = valeur

    def to_dict(self) -> dict[str, Any]:
        """
        Convertit la performance en dictionnaire pour Pandas.
        Pratique pour aplatir les données dans un DataFrame de résultats.
        """
        base_dict = {
            "id_participant": self.participant.id,
            "nom_participant": self.participant.nom,
            "role": self.role,
            "est_gagnant": self.est_gagnant
        }
        base_dict.update(self.stats)
        return base_dict

    def __str__(self) -> str:
        resultat = "Victoire" if self.est_gagnant else "Défaite"
        return f"Performance de {self.participant.nom} ({self.role}) - {resultat} - Stats: {list(self.stats.keys())}"
