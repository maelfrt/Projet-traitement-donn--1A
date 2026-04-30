from datetime import UTC, datetime
from typing import Any

from .personne import Personne


class Athlete(Personne):
    """
    Objet représentant un athlète et ses caractéristiques physiques.
    Hérite de la classe Personne pour les informations d'identité de base.

    Parameters
    ----------
    nom : str
        Le nom de famille de l'athlète.
    prenom : str | None
        Le prénom de l'athlète.
    id_personne : str | None
        L'identifiant unique utilisé pour le suivi technique.
    provenance : str | None
        Le pays ou la région d'origine.
    pseudo : str | None
        Nom d'usage ou pseudonyme (courant en E-sport).
    genre : str | None
        Le genre de l'athlète.
    role : str | None
        La position ou le rôle dans le sport (ex: Gardien, Pivot).
    date_naissance : datetime | str | None
        La date de naissance (format objet datetime ou texte YYYY-MM-DD).
    lieu_naissance : str | None
        Lieu de naissance de l'athlète.
    equipe_actuelle : str | None
        Le club ou l'équipe d'appartenance actuelle.
    taille : float | None
        La taille de l'athlète en centimètres.
    poids : float | None
        Le poids de l'athlète en kilogrammes.
    **kwargs : Any
        Permet de recevoir d'autres données spécifiques sans bloquer le code.
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
        date_naissance: datetime | str | None = None,
        lieu_naissance: str | None = None,
        equipe_actuelle: str | None = None,
        taille: float | None = None,
        poids: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            nom=nom,
            prenom=prenom,
            id_personne=id_personne,
            provenance=provenance,
            pseudo=pseudo,
            genre=genre,
            role=role,
            date_naissance=date_naissance,
            lieu_naissance=lieu_naissance,
            **kwargs,
        )
        self.taille = taille
        self.poids = poids
        self.equipe_actuelle = equipe_actuelle

    def age(self) -> int | None:
        """
        Calcule l'âge actuel de l'athlète de manière précise.

        Renvoie
        -------
        int | None
            L'âge calculé en années, ou None si la date est inconnue.
        """
        if not self.date_naissance:
            return None

        try:
            naissance = self.date_naissance.date()
            aujourdhui = datetime.now(UTC).date()

            # Calcul de la différence d'années
            age_calcule = aujourdhui.year - naissance.year

            # On vérifie si l'anniversaire est déjà passé cette année
            anniversaire_passe = (aujourdhui.month, aujourdhui.day) >= (naissance.month, naissance.day)

            return age_calcule if anniversaire_passe else age_calcule - 1

        except (ValueError, TypeError, AttributeError):
            return None

    def calculer_imc(self) -> float | None:
        """
        Calcule l'Indice de Masse Corporelle (IMC) à partir du poids et de la taille.

        Renvoie
        -------
        float | None
            L'IMC arrondi (1 décimale), ou None si les mesures sont absentes.
        """
        if self.taille is None or self.poids is None:
            return None

        try:
            poids_val = float(self.poids)
            taille_val = float(self.taille)

            if taille_val <= 0 or poids_val <= 0:
                return None

            # Si la taille est en cm (ex: 180), on la convertit en mètres (1.80)
            taille_m = taille_val / 100.0 if taille_val > 3.0 else taille_val

            # Formule : poids / taille au carré
            imc = poids_val / (taille_m**2)

            return round(imc, 1)

        except (ValueError, TypeError):
            return None

    def to_dict(self) -> dict[str, Any]:
        """
        Transforme l'athlète en dictionnaire pour l'affichage ou l'export.

        Renvoie
        -------
        dict[str, Any]
            Dictionnaire contenant les caractéristiques clés de l'athlète.
        """
        return {
            "id_participant": self.id,
            "nom_complet": self.nom,
            "provenance": self.provenance,
            "pseudo": self.pseudo,
            "genre": self.genre,
            "role": self.role,
            "date_naissance": self.date_naissance,
            "taille": self.taille,
            "poids": self.poids,
            "imc": self.calculer_imc(),
            "equipe_actuelle": self.equipe_actuelle,
        }

    def __str__(self) -> str:
        prov = f" ({self.provenance})" if self.provenance else ""
        return f"Athlète : {self.nom}{prov} - ID: {self.id}"
