class Match:
    """Définition d'un match entre deux équipes.

    Parameters
    ----------
    id_match : str
        clés primaires permetant de différentier les equipes 
    date : str
        date a laquelle le match a lieu
    lieu : str
        lieu ou se tiendra le match
    type_match : str
        état d'avancement du match dans le tournoi (final, demi-finale, quart-final...)
    patch : str
        version des regles utilisé par la competition
    surface : str
        type de materiaux utiliser pour la surface du match(herbe, terrre batue, dur...)
    performance : str
        ensemble des données disponible pour le match
    vaiqueur : str
        correspond au vainqeur du match si il y en a un 
    """
    def __init__(
        self,
        id_match: str,
        date: str,
        lieu: str,    
    ) -> None:
        self.id_match = id_match
        self.lieu = lieu
        self.date = date
        self.type_match: type_match | None = None
        self.patch: patch | None = None
        self.surface: surface | None = None
        self._performance: dict{} = {}
        self._vainqueur: Equipe | Athlete | None = None

    def __str__(self) -> str:
        status = f"Vainqueur : {self._vainqueur.nom}" if self._vainqueur else "En attente"
        return f"Match : {self.nom_epreuve} ({self.date}) - {self.lieu} | {status}"

    def ajouter_performance(
        self,
        performance: Performance,
    ):
        self.performance = performance

    def renvoyer_gagnant(
        self,
    ) -> Equipe | Athlete:
        if self.score is not None:
            if self.score[0] > self.score[1]:
                return equipe_1 
            if self.score[1] > self.score[0]:
                return equipe_2
            else:
                return "match nul (comme le psg)"
        else:
            if vainqueur is not None:
                

