from typing import Any

from src.Model.athlete import Athlete
from src.Model.equipe import Equipe


class SearchEngine:
    """
    Responsable uniquement de la recherche d'informations.
    """

    def __init__(self, data_loader: Any) -> None:
        self.loader = data_loader

    def _recherche_generique(self, nom_partiel: str, type_attendu: type) -> list:
        """Moteur de recherche interne optimisé utilisant l'annuaire (O(N))."""
        if not hasattr(self.loader, "_annuaire_participants"):
            return []

        recherche = nom_partiel.lower()

        resultats_uniques: set[Any] = set()

        for participant in self.loader._annuaire_participants.values():
            nom_participant = getattr(participant, "nom", "")

            if isinstance(participant, type_attendu) and recherche in str(nom_participant).lower():
                resultats_uniques.add(participant)

        return sorted(resultats_uniques, key=lambda p: str(getattr(p, "nom", "")))

    def chercher_athlete_par_nom(self, nom_partiel: str) -> list:
        """Retourne une liste d'objets Athlete correspondant au nom."""
        return self._recherche_generique(nom_partiel, Athlete)

    def chercher_equipe_par_nom(self, nom_partiel: str) -> list:
        """Retourne une liste d'objets Equipe correspondant au nom."""
        return self._recherche_generique(nom_partiel, Equipe)
