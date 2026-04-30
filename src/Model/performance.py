from typing import Any

from .participant import Participant


class Performance:
    """
    Objet faisant le lien entre un participant et un match spécifique.
    Il stocke le résultat (victoire/défaite) et toutes les statistiques
    produites durant la rencontre.

    Parameters
    ----------
    participant : Participant
        L'objet Participant (Athlète ou Équipe) concerné.
    role : str
        Le rôle occupé lors du match (ex: "Domicile", "Vainqueur", "Equipe Bleue").
    est_gagnant : bool
        Indique si ce participant a remporté le match. Par défaut False.
    stats : dict[str, Any] | None
        Dictionnaire des statistiques chiffrées (buts, points, etc.).
    """

    def __init__(
        self,
        participant: Participant,
        role: str,
        est_gagnant: bool = False,
        est_nul: bool = False,
        stats: dict[str, Any] | None = None,
    ) -> None:
        self.participant = participant
        self.role = role
        self.est_gagnant = est_gagnant
        self.est_nul = est_nul

        # On s'assure que stats est toujours un dictionnaire pour éviter les erreurs de type
        self.stats = stats if stats is not None else {}

        # Cette liste est utilisée pour les sports d'équipe (ex: Football, LoL).
        # Elle permet de lister les athlètes précis qui ont participé à cette performance collective.
        self.joueurs_match: list[Participant] = []

    def ajouter_stat(self, cle: str, valeur: Any) -> None:
        """
        Permet d'ajouter ou de mettre à jour manuellement une statistique.
        """
        self.stats[cle] = valeur

    def to_dict(self) -> dict[str, Any]:
        """
        Convertit la performance en un dictionnaire.
        C'est cette méthode qui est appelée par le Match pour construire
        le tableau de données final (Dataframe ou CSV).

        Renvoie
        -------
        dict[str, Any]
            Dictionnaire contenant l'ID, le nom, le résultat et toutes les stats.
        """
        # On prépare les informations d'identité de base
        resultat = {
            "id_participant": self.participant.id,
            "nom_participant": self.participant.nom,
            "role": self.role,
            "est_gagnant": self.est_gagnant,
            "est_nul": self.est_nul,
        }

        # On fusionne avec le dictionnaire des statistiques chiffrées
        resultat.update(self.stats)

        return resultat

    def __str__(self) -> str:
        if self.est_gagnant:
            verdict = "Victoire"
        elif getattr(self, "est_nul", False):
            verdict = "Match nul"
        else:
            verdict = "Défaite"
        return f"Performance de {self.participant.nom} ({self.role}) - {verdict}"
