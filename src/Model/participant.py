from abc import ABC, abstractmethod
from typing import Any


class Participant(ABC):
    """
    Classe de base abstraite pour tout concurrent de la compétition.
    Elle définit les attributs communs aux athlètes et aux équipes.

    Parameters
    ----------
    nom : str
        Le nom du participant (individu ou équipe).
    id_participant : str | None
        L'identifiant unique permettant de retrouver le participant dans le système.
    **kwargs : Any
        Dictionnaire flexible pour stocker des informations spécifiques
        selon le sport, sans modifier la structure de base.
    """

    def __init__(self, nom: str, id_participant: str | None = None, **kwargs: Any) -> None:
        self.id: str = str(id_participant) if id_participant else "ID_A_DEFINIR"
        self.nom: str = nom

        self.donnees_complementaires: dict[str, Any] = kwargs

    @abstractmethod
    def __str__(self) -> str:
        """
        Force les classes filles (Athlete, Equipe) à définir leur propre
        manière de s'afficher textuellement.
        """
