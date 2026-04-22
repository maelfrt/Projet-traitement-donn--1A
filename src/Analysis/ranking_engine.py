from typing import Any

from src.Model.competition import Competition


class RankingEngine:
    """
    Moteur responsable de générer le classement final d'une compétition.
    """

    def generer_classement(self, competition: Competition) -> None:
        """Point d'entrée principal. Détecte le format et lance le bon calcul à tous les niveaux."""

        # On fait le calcul aux sous-tournois
        # Ainsi, Brisbane, Roland Garros, etc., auront tous leur classement calculé
        for sous_comp in competition.sous_competitions.values():
            self.generer_classement(sous_comp)

        # Vérification des matchs au niveau actuel
        if not hasattr(competition, "liste_match") or not competition.liste_match:
            competition.classement_final = []
            return

        format_cible = str(getattr(competition, "type_format", "championnat")).strip().lower()

        if format_cible == "championnat":
            resultats = self._calculer_championnat(competition)
        elif format_cible == "elimination":
            resultats = self._calculer_elimination(competition)
        else:
            resultats = []

        competition.classement_final = resultats

    def _calculer_championnat(self, competition: Competition) -> list[dict[str, Any]]:
        bilan_participants: dict[str, dict[str, Any]] = {}

        for match in competition.liste_match:
            for performance in match.performances.values():
                id_joueur = str(performance.participant.id)
                nom_joueur = str(performance.participant.nom)

                if id_joueur not in bilan_participants:
                    bilan_participants[id_joueur] = {"nom": nom_joueur, "victoires": 0, "matchs_joues": 0}

                bilan_participants[id_joueur]["matchs_joues"] = int(bilan_participants[id_joueur]["matchs_joues"]) + 1
                if performance.est_gagnant:
                    bilan_participants[id_joueur]["victoires"] = int(bilan_participants[id_joueur]["victoires"]) + 1

        liste_bilan = list(bilan_participants.values())

        liste_triee = sorted(liste_bilan, key=lambda x: int(x["victoires"]), reverse=True)

        return liste_triee

    def _calculer_elimination(self, competition: Competition) -> list[dict[str, Any]]:
        bilan_participants: dict[str, dict[str, Any]] = {}
        hierarchie_json = competition.poids_rounds or {}

        for match in competition.liste_match:
            nom_du_tour = str(match.type_match)
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
                    poids_actuel = float(bilan_participants[id_joueur]["poids_atteint"])
                    if poids_definitif < poids_actuel:
                        bilan_participants[id_joueur]["poids_atteint"] = float(poids_definitif)
                        bilan_participants[id_joueur]["tour_atteint"] = nom_du_tour

                if performance.est_gagnant:
                    bilan_participants[id_joueur]["victoires_totales"] = (
                        int(bilan_participants[id_joueur]["victoires_totales"]) + 1
                    )

        liste_bilan = list(bilan_participants.values())

        liste_triee = sorted(liste_bilan, key=lambda x: (float(x["poids_atteint"]), -int(x["victoires_totales"])))

        return liste_triee

    def _departager_finalistes(self, nom_du_tour: str, est_gagnant: bool, poids_de_base: int) -> float:
        texte_tour = nom_du_tour.lower()

        est_grande_finale = ("gold" in texte_tour) or (
            "final" in texte_tour and "semi" not in texte_tour and "quarter" not in texte_tour
        )
        if est_grande_finale:
            return 0.0 if est_gagnant else 1.0

        est_petite_finale = "bronze" in texte_tour or "3rd" in texte_tour or "3e" in texte_tour
        if est_petite_finale:
            return 2.0 if est_gagnant else 3.0

        return float(poids_de_base) + 0.9
