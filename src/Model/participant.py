from abc import ABC, abstractmethod
from typing import Any


class Participant(ABC):
    """
    Classe de base pour tout concurrent (Athlète ou Équipe).
    """
    def __init__(self, nom: str, id_participant: str | None = None, **kwargs: Any) -> None:
        self.id: str = str(id_participant) if id_participant else "ID_A_DEFINIR"
        self.nom: str = nom
        self.donnees_complementaires: dict[str, Any] = kwargs

    @abstractmethod
    def __str__(self) -> str:
        pass
