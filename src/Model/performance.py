from typing import Any


class Performance:
    """
    Objet faisant le lien entre un participant (Athlète ou Équipe) et un Match.
    Il contient le résultat et les statistiques spécifiques au sport.
    """

    def __init__(
        self,
        id_participant: str,
        role: str,
        est_gagnant: bool = False,
        stats: dict[str, Any] | None = None
    ) -> None:
        self.id_participant = id_participant
        self.role = role
        self.est_gagnant = est_gagnant
        self.stats = stats if stats is not None else {}

    def ajouter_stat(self, cle: str, valeur: Any) -> None:
        """Ajoute ou met à jour une statistique spécifique."""
        self.stats[cle] = valeur

    def to_dict(self) -> dict:
        """
        Convertit la performance en dictionnaire pour Pandas.
        """
        base_dict = {
            "id_participant": self.id_participant,
            "role": self.role,
            "est_gagnant": self.est_gagnant
        }
        base_dict.update(self.stats)
        return base_dict

    def __str__(self) -> str:
        resultat = "Victoire" if self.est_gagnant else "Défaite"
        nb_stats = len(self.stats)
        return f"Performance ({self.role}) - {resultat} - {nb_stats} stat(s) - ID Participant: {self.id_participant}"
