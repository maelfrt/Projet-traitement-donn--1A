from typing import Any

from src.Model.athlete import Athlete
from src.Model.equipe import Equipe


class SearchEngine:
    """
    Moteur de recherche interne de l'application.

    Cette classe est dédiée à l'exploration de l'annuaire des participants
    chargés en mémoire. Elle utilise des opérations sur les ensembles (sets)
    pour garantir des résultats uniques et performants.
    """

    def __init__(self, data_loader: Any) -> None:
        """
        Initialise le moteur de recherche en le connectant à la source de données.

        Parameters
        ----------
        data_loader : Any
            L'instance du DataLoader contenant le dictionnaire de cache mémoire
            où sont stockés tous les participants.
        """
        self.loader = data_loader

    def _recherche_generique(self, recherche: str, classe_attendue: type) -> list:
        """
        Explore la mémoire pour trouver les entités correspondant à un mot-clé.

        La méthode utilise une approche souple : la casse (majuscules/minuscules)
        est ignorée et la recherche est inclusive (le mot-clé peut se trouver
        n'importe où dans le nom). L'utilisation d'un ensemble (set) permet
        d'éliminer automatiquement les éventuels doublons.

        Parameters
        ----------
        recherche : str
            Le mot-clé ou le fragment de nom saisi par l'utilisateur.
        classe_attendue : type
            Le type d'objet ciblé par la recherche (Athlete ou Equipe)
            pour filtrer intelligemment les résultats.

        Returns
        -------
        list
            Une liste d'instances correspondantes, triée par ordre alphabétique.
        """
        # Sécurité empêchant un plantage si l'utilisateur lance une recherche
        # alors qu'aucun sport n'a encore été chargé en mémoire.
        if not hasattr(self.loader, "_annuaire_participants"):
            return []

        recherche_minuscule = recherche.strip().lower()

        # Le set garantit l'unicité des résultats
        resultats_uniques = set()

        for participant in self.loader._annuaire_participants.values():
            # L'utilisation de getattr protège le programme en cas d'objet mal formé
            # qui ne possèderait pas l'attribut 'nom'
            nom_participant = str(getattr(participant, "nom", ""))

            # Le filtrage croisé vérifie à la fois l'identité
            # de l'objet (son type) et la présence du mot-clé
            if isinstance(participant, classe_attendue) and recherche_minuscule in nom_participant.lower():
                resultats_uniques.add(participant)

        # La fonction sorted convertit naturellement le set en une liste ordonnée
        return sorted(resultats_uniques, key=lambda p: str(getattr(p, "nom", "")))

    def chercher_athlete_par_nom(self, recherche: str) -> list:
        """
        Restreint la recherche textuelle aux individus (athlètes).

        Parameters
        ----------
        recherche : str
            Le texte à rechercher dans le nom du joueur.

        Returns
        -------
        list
            Liste triée des objets Athlete correspondants.
        """
        return self._recherche_generique(recherche, Athlete)

    def chercher_equipe_par_nom(self, recherche: str) -> list:
        """
        Restreint la recherche textuelle aux structures collectives (équipes).

        Parameters
        ----------
        recherche : str
            Le texte à rechercher dans le nom de l'équipe.

        Returns
        -------
        list
            Liste triée des objets Equipe correspondants.
        """
        return self._recherche_generique(recherche, Equipe)
