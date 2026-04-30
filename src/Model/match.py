from datetime import UTC, datetime
from typing import Any

from .performance import Performance


class Match:
    """
    Représente une rencontre sportive entre plusieurs participants.
    Cette classe centralise les informations de contexte (date, lieu) et les résultats.

    Parameters
    ----------
    date : datetime | str | None
        La date de la rencontre.
    id_match : str | None
        L'identifiant unique du match.
    lieu : str | None
        L'endroit où se joue le match.
    type_match : str | None
        La phase (ex: "Demi-finale").
    patch : str | None
        La version logicielle (E-sport).
    surface : str | None
        Le type de terrain (Tennis, Foot).
    niveau_tournoi : str | None
        La catégorie du tournoi.
    format_sets : str | None
        Le format de score (ex: "Best of 5").
    **kwargs : Any
        Données complémentaires spécifiques au sport.
    """

    def __init__(
        self,
        date: datetime | str | None = None,
        id_match: str | None = None,
        lieu: str | None = None,
        type_match: str | None = None,
        patch: str | None = None,
        surface: str | None = None,
        niveau_tournoi: str | None = None,
        format_sets: str | None = None,
        **kwargs: Any,
    ) -> None:
        # On s'assure que l'ID est toujours une chaîne de caractères pour éviter les erreurs de type
        self.id_match: str = str(id_match) if id_match else "ID_A_DEFINIR"

        self.date_objet: datetime | None = None

        if isinstance(date, datetime):
            self.date_objet = date
        elif isinstance(date, str):
            try:
                # Nettoyage de la chaîne pour ne garder que la date YYYY-MM-DD
                date_pure = date.strip().split(" ")[0]
                # On crée un objet datetime conscient du fuseau horaire (UTC)
                self.date_objet = datetime.strptime(date_pure, "%Y-%m-%d").replace(tzinfo=UTC)
            except (ValueError, IndexError):
                self.date_objet = None

        self.lieu = lieu
        self.type_match = type_match
        self.patch = patch
        self.surface = surface
        self.niveau_tournoi = niveau_tournoi
        self.format_sets = format_sets
        self.infos_supplementaires = kwargs

        # Stockage des performances (lien entre le match et les athlètes/équipes)
        self.performances: dict[str, Performance] = {}

    def ajouter_performance(self, role: str, performance: Performance) -> None:
        """
        Enregistre le résultat et les statistiques d'un participant pour ce match.
        """
        self.performances[role] = performance

    def renvoyer_gagnant(self) -> str:
        """
        Analyse les performances pour identifier le vainqueur.

        Renvoie
        -------
        str
            Nom du gagnant ou message d'attente.
        """
        if not self.performances:
            return "Résultat non saisi"

        for role, perf in self.performances.items():
            if perf.est_gagnant:
                return f"{perf.participant.nom} ({role})"

        return "Match nul"

    def to_dict(self) -> dict[str, Any]:
        """
        Transforme l'objet Match en dictionnaire.
        C'est essentiel pour que Pandas puisse ensuite l'afficher ou l'exporter en CSV.

        Renvoie
        -------
        dict[str, Any]
            Les données du match et des performances fusionnées.
        """
        # On prépare les infos de base
        donnees: dict[str, Any] = {
            "id_match": self.id_match,
            "date": self.date_objet.strftime("%Y-%m-%d") if self.date_objet else "Date inconnue",
            "lieu": self.lieu,
            "type_match": self.type_match,
            "surface": self.surface,
            "resultat_final": self.renvoyer_gagnant(),
        }

        # On parcourt chaque performance pour ajouter ses colonnes au dictionnaire
        for role, perf in self.performances.items():
            # On normalise le nom du rôle pour en faire une clé de dictionnaire propre
            prefixe = str(role).replace(" ", "_").lower()

            donnees[f"{prefixe}_nom"] = perf.participant.nom
            donnees[f"{prefixe}_id"] = perf.participant.id
            donnees[f"{prefixe}_est_gagnant"] = perf.est_gagnant

            # On ajoute les statistiques détaillées (points, buts, etc.)
            for stat_nom, stat_valeur in perf.stats.items():
                donnees[f"{prefixe}_{stat_nom}"] = stat_valeur

        # Ajout des données bonus si elles existent
        if self.infos_supplementaires:
            donnees.update(self.infos_supplementaires)

        return donnees

    def __str__(self) -> str:
        """
        Définit comment un match s'affiche textuellement dans les listes.
        S'adapte dynamiquement pour afficher une victoire, un nul ou un match non joué.
        """
        # Formatage de la date
        if self.date_objet:
            date_str = self.date_objet.strftime("%Y/%m/%d")
        else:
            date_str = "Date inconnue"

        participants = []
        resultat_str = "❔ Non joué / Résultat inconnu"
        match_est_nul = False

        # Récupération des participants et analyse du résultat
        for role, perf in self.performances.items():
            nom = str(perf.participant.nom)
            participants.append(nom)

            if perf.est_gagnant:
                # Si on trouve un gagnant, on formate directement sa chaîne
                resultat_str = f"🏆 {nom} ({role.capitalize()})"
            elif getattr(perf, "est_nul", False):
                # On note qu'un état nul a été détecté pour cette rencontre
                match_est_nul = True

        # Si aucun vainqueur n'a été trouvé mais que le match est déclaré nul
        if "🏆" not in resultat_str and match_est_nul:
            resultat_str = "🤝 Match nul"

        # Création de l'affiche "Equipe A vs Equipe B"
        if len(participants) >= 2:
            affiche = f"{participants[0]} vs {participants[1]}"
        elif len(participants) == 1:
            affiche = f"{participants[0]} vs Adversaire inconnu"
        else:
            affiche = "Match sans participants"

        # Affichage final assemblé (l'émoji est désormais géré dans resultat_str)
        return f"[{date_str}] {affiche} | {resultat_str}"
