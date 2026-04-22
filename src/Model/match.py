from datetime import datetime
from typing import Any

from .performance import Performance


class Match:
    """
    Définition d'un match regroupant les performances des participants.

    Parameters
    ----------
    id_match : str
        clés primaires permettant de différentier les équipes
    date : str
        date à laquelle le match a lieu
    lieu : str
        lieu ou se tiendra le match
    type_match : str
        état d'avancement du match dans le tournoi (finale, demi-finale, quart-finale...)
    patch : str
        version des règles utilisées par la compétition
    surface : str
        type de matériaux utilisés pour la surface du match(herbe, terre battue, dure...)
    performance : str
        ensemble des données disponibles pour le match
    vaiqueur : str
        correspond au vainqueur du match si il y en a un
    """

    def __init__(
        self,
        date: datetime,
        id_match: str | None = None,
        lieu: str | None = None,
        type_match: str | None = None,
        patch: str | None = None,
        surface: str | None = None,
        niveau_tournoi: str | None = None,
        format_sets: str | None = None,
        **kwargs: Any
    ) -> None:
        self.id_match = str(id_match) if id_match else "ID_A_DEFINIR"

        self.date = date
        self.lieu = lieu
        self.type_match = type_match
        self.patch = patch
        self.surface = surface
        self.niveau_tournoi = niveau_tournoi
        self.format_sets = format_sets
        self.infos_supplementaires: dict[str, Any] = kwargs

        # Dictionnaire stockant les objets Performance par rôle (ex: "Vainqueur", "Equipe 1")
        self.performances: dict[str, Performance] = {}

    def ajouter_performance(self, role: str, performance: Performance) -> None:
        """Ajoute une performance connectée au match."""
        self.performances[role] = performance

    def renvoyer_gagnant(self) -> str:
        """
        Détermine le gagnant en utilisant l'objet Participant stocké dans la performance.
        Retourne le nom réel du vainqueur.
        """
        if not self.performances:
            return "En attente de résultats"

        for role, perf in self.performances.items():
            if perf.est_gagnant:
                # On accède directement au nom de l'objet (Athlete ou Equipe)
                return f"{perf.participant.nom} ({role})"

        return "Match nul"

    def to_dict(self) -> dict[str, Any]:
        """
        Convertit le match en dictionnaire pour Pandas.
        Inclut le nom du gagnant pour éviter les recherches ultérieures.
        """
        return {
            "id_match": self.id_match,
            "date_match": self.date,
            "lieu": self.lieu,
            "type_match": self.type_match,
            "surface": self.surface,
            "nb_participants": len(self.performances),
            "resultat_final": self.renvoyer_gagnant()
        }

    def __str__(self) -> str:
        info_lieu = f" à {self.lieu}" if self.lieu else ""
        return f"Match {self.id_match} ({self.date}){info_lieu} | Vainqueur : {self.renvoyer_gagnant()}"
