from typing import Any

from src.Model.competition import Competition


class RankingEngine:
    """
    Moteur algorithmique responsable de la génération des classements.

    Cette classe analyse les résultats des matchs d'une compétition et
    détermine la position finale de chaque participant en appliquant
    les règles spécifiques au format du tournoi (championnat régulier
    ou arbre à élimination directe).
    """

    def generer_classement(self, competition: Competition) -> None:
        """
        Génère et met à jour le classement final d'un tournoi complet.

        La méthode s'applique d'abord au tableau principal, puis descend
        automatiquement dans les sous-groupes existants pour s'assurer
        que chaque phase possède son propre classement à jour.

        Parameters
        ----------
        competition : Competition
            L'objet compétition dont les classements doivent être calculés.
        """
        self._classer_une_competition(competition)

        for sous_comp in competition.sous_competitions.values():
            self._classer_une_competition(sous_comp)

    def _classer_une_competition(self, comp: Competition) -> None:
        """
        Aiguille le calcul du classement vers l'algorithme approprié.

        Vérifie la présence de matchs et le format déclaré de la
        compétition pour appliquer la logique sportive adéquate.

        Parameters
        ----------
        comp : Competition
            Le niveau de compétition (racine ou poule) à évaluer.
        """
        if not getattr(comp, "liste_match", []):
            comp.classement_final = []
            return

        format_cible = str(getattr(comp, "type_format", "championnat")).strip().lower()

        if format_cible == "championnat":
            comp.classement_final = self._calculer_championnat(comp)
        elif format_cible == "elimination":
            comp.classement_final = self._calculer_elimination(comp)
        else:
            comp.classement_final = []

    def _calculer_championnat(self, comp: Competition) -> list[dict[str, Any]]:
        """
        Calcule le classement basé sur l'accumulation de victoires.

        Parameters
        ----------
        comp : Competition
            La compétition au format ligue à évaluer.

        Returns
        -------
        list[dict[str, Any]]
            Une liste de dictionnaires représentant le classement trié,
            du vainqueur au dernier.
        """
        bilan_participants: dict[str, dict[str, Any]] = {}

        for match in comp.liste_match:
            for performance in match.performances.values():
                id_joueur = str(performance.participant.id)
                nom_joueur = str(performance.participant.nom)

                if id_joueur not in bilan_participants:
                    bilan_participants[id_joueur] = {"nom": nom_joueur, "victoires": 0, "matchs_joues": 0}

                bilan_participants[id_joueur]["matchs_joues"] = int(bilan_participants[id_joueur]["matchs_joues"]) + 1

                if performance.est_gagnant:
                    bilan_participants[id_joueur]["victoires"] = int(bilan_participants[id_joueur]["victoires"]) + 1

        liste_bilan = list(bilan_participants.values())

        # Tri décroissant direct en se basant sur le compteur de victoires
        liste_triee = sorted(liste_bilan, key=lambda x: int(x["victoires"]), reverse=True)

        return liste_triee

    def _calculer_elimination(self, comp: Competition) -> list[dict[str, Any]]:
        """
        Calcule le classement pour un tournoi à élimination directe.

        L'algorithme identifie le tour le plus avancé atteint par chaque
        participant. Il utilise un système de poids défini dans la
        configuration JSON pour hiérarchiser les tours.

        Parameters
        ----------
        comp : Competition
            La compétition au format tournoi à évaluer.

        Returns
        -------
        list[dict[str, Any]]
            Une liste triée des participants, du vainqueur final aux
            éliminés des premiers tours.
        """
        bilan_participants: dict[str, dict[str, Any]] = {}
        hierarchie_json = comp.poids_rounds or {}

        for match in comp.liste_match:
            nom_du_tour = str(match.type_match)
            # Poids arbitraire élevé appliqué si le tour n'est pas répertorié dans la configuration
            poids_de_base = hierarchie_json.get(nom_du_tour, 99)

            for performance in match.performances.values():
                id_joueur = str(performance.participant.id)
                nom_joueur = str(performance.participant.nom)

                poids_definitif = self._departager_finalistes(
                    nom_du_tour=nom_du_tour, est_gagnant=performance.est_gagnant, poids_de_base=int(poids_de_base)
                )

                if id_joueur not in bilan_participants:
                    bilan_participants[id_joueur] = {
                        "nom": nom_joueur,
                        "poids_atteint": float(poids_definitif),
                        "tour_atteint": nom_du_tour,
                        "victoires_totales": 0,
                    }
                else:
                    # Mise à jour conditionnelle : on ne conserve que la meilleure performance
                    # (la note numérique la plus basse correspond au tour le plus avancé)
                    poids_actuel = float(bilan_participants[id_joueur]["poids_atteint"])
                    if poids_definitif < poids_actuel:
                        bilan_participants[id_joueur]["poids_atteint"] = float(poids_definitif)
                        bilan_participants[id_joueur]["tour_atteint"] = nom_du_tour

                if performance.est_gagnant:
                    bilan_participants[id_joueur]["victoires_totales"] = (
                        int(bilan_participants[id_joueur]["victoires_totales"]) + 1
                    )

        liste_bilan = list(bilan_participants.values())

        # Règle de tri : la meilleure note (la plus petite) en premier, et en cas d'égalité, le plus de victoires
        def critere_de_tri(joueur: dict[str, Any]) -> tuple[float, int]:
            poids = float(joueur["poids_atteint"])
            victoires_inversees = -int(joueur["victoires_totales"])
            return (poids, victoires_inversees)

        liste_triee = sorted(liste_bilan, key=critere_de_tri)

        return liste_triee

    def _departager_finalistes(self, nom_du_tour: str, est_gagnant: bool, poids_de_base: int) -> float:
        """
        Attribue une note numérique finale selon le résultat dans un tour.

        Ce système permet de séparer le vainqueur du perdant d'un même match.
        Le gagnant d'une finale obtient 0.0 (1er), le perdant 1.0 (2e).

        Parameters
        ----------
        nom_du_tour : str
            L'appellation textuelle du tour (ex: "Final", "Bronze Medal Match").
        est_gagnant : bool
            Indique si le participant a remporté cette rencontre précise.
        poids_de_base : int
            La valeur de base du tour issue de la configuration JSON.

        Returns
        -------
        float
            La note de classement finale pour cette performance.
        """
        texte_tour = nom_du_tour.lower()

        est_grande_finale = ("gold" in texte_tour) or (
            "final" in texte_tour and "semi" not in texte_tour and "quarter" not in texte_tour
        )
        if est_grande_finale:
            return 0.0 if est_gagnant else 1.0

        est_petite_finale = "bronze" in texte_tour or "3rd" in texte_tour or "3e" in texte_tour
        if est_petite_finale:
            return 2.0 if est_gagnant else 3.0

        # Pénalité sous forme de décimal pour un perdant dans un tour classique.
        # Cela garantit qu'il soit classé derrière tous ceux ayant gagné ce
        # même tour, mais devant ceux éliminés au tour précédent.
        return float(poids_de_base) + 0.9
