from datetime import datetime

from .personne import Personne


class Athlete(Personne):
    """
    Objet représentant un athlète, héritant de Personne.

    Attributs supplémentaires :
    taille : float | None (en cm)
    poids : float | None (en kg)
    equipe: str | None
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
        poids: float | None = None
    ) -> None:
        super().__init__(
            nom,
            prenom,
            id_personne,
            provenance,
            pseudo,
            genre,
            role,
            date_naissance,
            lieu_naissance
        )
        self.taille = taille
        self.poids = poids
        self.equipe_actuelle = equipe_actuelle

    def age(self) -> int | None:
        """Calcule l'âge de l'athlète à partir de sa date de naissance."""
        if self.date_naissance:
            return (datetime.now() - self.date_naissance).days // 365
        return None

    def calculer_imc(self) -> float | None:
        """Calcule l'Indice de Masse Corporelle (IMC)."""
        if self.taille and self.poids and self.taille > 0:
            taille_metres = self.taille / 100
            return round(self.poids / (taille_metres ** 2), 2)
        return None

    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour Pandas."""
        return {
            "id_personne": self.id_personne,
            "nom": self.nom,
            "provenance": self.provenance,
            "pseudo": self.pseudo,
            "genre": self.genre,
            "role": self.role,
            "date_naissance": self.date_naissance,
            "taille": self.taille,
            "poids": self.poids,
            "imc": self.calculer_imc()
        }

    def __str__(self) -> str:
        info_provenance = f" ({self.provenance})" if self.provenance else ""
        return f"Athlète : {self.nom}{info_provenance} - ID: {self.id_personne}"
