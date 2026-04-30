from typing import Any

from .match import Match


class Competition:
    """
    Objet racine représentant un tournoi, une ligue ou une saison complète.
    Une compétition peut contenir des matchs directs ou être divisée en
    sous-groupes (phases, poules, sections).

    Parameters
    ----------
    id_competition : int | str
        L'identifiant unique de la compétition.
    nom : str
        Le nom complet du tournoi (ex: "Champions League").
    type_format : str | None
        Le mode d'organisation (ex: "Championnat", "Élimination").
    poids_rounds : dict[str, int] | None
        Dictionnaire optionnel pour pondérer l'importance des tours.
    """

    def __init__(
        self,
        id_competition: int | str,
        nom: str,
        type_format: str | None = None,
        poids_rounds: dict[str, int] | None = None,
    ) -> None:
        self.id_competition = id_competition
        self.nom = nom
        self.type_format = type_format

        # On s'assure que poids_rounds est toujours un dictionnaire, même vide,
        # pour éviter des erreurs de type None lors des calculs de classement.
        self.poids_rounds: dict[str, int] = poids_rounds if poids_rounds else {}

        # Initialisation explicite des listes et dictionnaires
        self.liste_match: list[Match] = []
        self.sous_competitions: dict[str, Competition] = {}

        # Le classement sera rempli par le moteur d'analyse après les calculs
        self.classement_final: list[dict[str, Any]] = []

    def ajouter_match(self, match: Match) -> None:
        """
        Ajoute une rencontre à la liste des matchs de ce niveau.
        """
        self.liste_match.append(match)

    def obtenir_ou_creer_sous_comp(self, nom_sous_comp: str) -> "Competition":
        """
        Gère l'organisation du tournoi en créant des sous-groupes.
        Si le groupe existe déjà, il est simplement renvoyé.

        Renvoie
        -------
        Competition
            L'instance de la sous-compétition (ex: "Poule A").
        """
        if nom_sous_comp not in self.sous_competitions:
            # On crée une nouvelle instance "enfant".
            # On lui transmet le format et les poids du parent pour rester cohérent.
            nouvelle_id = f"{self.id_competition}_{len(self.sous_competitions)}"
            self.sous_competitions[nom_sous_comp] = Competition(
                id_competition=nouvelle_id,
                nom=nom_sous_comp,
                type_format=self.type_format,
                poids_rounds=self.poids_rounds,
            )

        return self.sous_competitions[nom_sous_comp]

    def obtenir_tous_les_matchs(self) -> list[Match]:
        """
        Parcourt la compétition pour extraire absolument tous les matchs,
        qu'ils soient à la racine ou dans une sous-compétition.

        Renvoie
        -------
        list[Match]
            Une liste unique contenant l'intégralité des rencontres.
        """
        # On commence par récupérer les matchs de ce niveau
        tous_les_matchs = list(self.liste_match)

        # On va explorer les sous-groupes pour collecter leurs matchs.
        for sous_comp in self.sous_competitions.values():
            tous_les_matchs.extend(sous_comp.liste_match)

        return tous_les_matchs

    def __str__(self) -> str:
        nb_m = len(self.obtenir_tous_les_matchs())
        nb_sc = len(self.sous_competitions)

        detail = f"{nb_m} matchs"
        if nb_sc > 0:
            detail += f" répartis dans {nb_sc} sous-groupes"

        return f"Compétition : {self.nom} ({detail})"
