from __future__ import annotations

from .match import Match


class Competition:
    """
    Objet représentant un tournoi ou une ligue.
    Peut contenir soit une liste de Matchs, soit des sous-compétitions.
    """

    def __init__(
        self,
        id_competition: int,
        nom: str,
        type_format: str = "championnat",
        poids_rounds: dict[str, int] | None = None,
    ) -> None:
        self.id_competition = id_competition
        self.nom = nom
        self.type_format = type_format
        self.poids_rounds: dict[str, int] = poids_rounds if poids_rounds else {}

        self.liste_match: list[Match] = []
        self.sous_competitions: dict[str, Competition] = {}
        self.classement_final: list[dict] = []

    def set_classement(self, classement: list) -> None:
        """Enregistre le classement calculé."""
        self.classement_final = classement

    def ajouter_match(self, match: Match) -> None:
        """Ajoute un match à la liste."""
        self.liste_match.append(match)

    def obtenir_ou_creer_sous_comp(self, nom_sous_comp: str) -> Competition:
        """Gère l'imbrication des tournois (ex: Roland Garros dans ATP)."""
        if nom_sous_comp not in self.sous_competitions:
            # On crée une sous-comp avec un ID dérivé
            nouvelle_id = hash(nom_sous_comp) % 10000
            self.sous_competitions[nom_sous_comp] = Competition(
                id_competition=nouvelle_id,
                nom=nom_sous_comp,
                type_format=self.type_format,
                poids_rounds=self.poids_rounds,
            )
        return self.sous_competitions[nom_sous_comp]

    def obtenir_tous_les_matchs(self) -> list[Match]:
        """
        Parcourt l'arborescence pour renvoyer une liste de tous les matchs
        du tournoi principal et de ses sous-tournois.
        """
        matchs = list(self.liste_match)
        for sous_comp in self.sous_competitions.values():
            matchs.extend(sous_comp.obtenir_tous_les_matchs())
        return matchs

    def __str__(self) -> str:
        nb_m = len(self.liste_match)
        nb_s = len(self.sous_competitions)
        detail = f"{nb_m} matchs" if nb_m > 0 else f"{nb_s} sous-tournois"
        return f"Compétition : {self.nom} ({detail})"
