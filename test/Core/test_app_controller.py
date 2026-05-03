from typing import Any
from unittest.mock import patch

from src.Core.app_controller import AppController
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance


class TestAppController:
    def test_valider_et_convertir_date_succes(self) -> None:
        """Vérifie la conversion correcte d'une chaîne de caractères au format YYYY-MM-DD en objet datetime."""
        resultat = AppController.valider_et_convertir_date("2024-07-25")

        assert resultat is not None
        assert resultat.year == 2024
        assert resultat.month == 7

    def test_valider_et_convertir_date_echec(self) -> None:
        """Vérifie que la fonction retourne None lors de la soumission de formats de date invalides."""
        assert AppController.valider_et_convertir_date("25/07/2024") is None
        assert AppController.valider_et_convertir_date("N/A") is None
        assert AppController.valider_et_convertir_date(None) is None

    def test_calculer_bilan_historique(
        self, controller_prepare: AppController, liste_participants_statistiques: list
    ) -> None:
        """Vérifie l'exactitude du calcul des statistiques de victoires, nuls et défaites."""
        participant = liste_participants_statistiques[0]
        resultats = controller_prepare.calculer_bilan_historique(participant)

        stats_globales = resultats[0]
        assert stats_globales["total"] == 3
        assert stats_globales["victoires"] == 3
        assert stats_globales["defaites"] == 0

    def test_calculer_face_a_face(
        self, controller_prepare: AppController, liste_participants_statistiques: list
    ) -> None:
        """Vérifie le calcul des statistiques de confrontation directe entre deux participants."""
        participant_1 = liste_participants_statistiques[0]
        participant_2 = liste_participants_statistiques[1]

        stats_h2h = controller_prepare.calculer_face_a_face(participant_1, participant_2)

        assert stats_h2h["total"] == 3
        assert stats_h2h["victoires_p1"] == 3
        assert stats_h2h["victoires_p2"] == 0

    def test_calculer_moyennes_participant(self, equipe_standard: Equipe) -> None:
        """Vérifie le calcul mathématique des moyennes et l'exclusion des valeurs non numériques."""
        controller = AppController()
        comp_test = Competition(id_competition="C1", nom="Tournoi Test")
        controller.competition_actuelle = comp_test

        match1 = Match(id_match="m1")
        match1.ajouter_performance("Dom", Performance(equipe_standard, "Dom", stats={"buts": 2, "possession": "N/A"}))
        match2 = Match(id_match="m2")
        match2.ajouter_performance("Ext", Performance(equipe_standard, "Ext", stats={"buts": 4}))

        comp_test.liste_match = [match1, match2]
        moyennes = controller.calculer_moyennes_participant(equipe_standard)

        assert moyennes["buts"] == 3.0
        assert "possession" not in moyennes

    def test_calculer_moyennes_competition_complete(self) -> None:
        """Vérifie le calcul des moyennes sur l'ensemble d'une compétition."""
        controller = AppController()
        comp = Competition(id_competition="C1", nom="Coupe")

        eq1 = Equipe(nom="A")
        eq2 = Equipe(nom="B")

        m = Match(id_match="m1")
        m.ajouter_performance("P1", Performance(eq1, "P1", stats={"points": 100}))
        m.ajouter_performance("P2", Performance(eq2, "P2", stats={"points": 50}))
        comp.ajouter_match(m)

        moyennes = controller.calculer_moyennes_competition(comp)

        assert moyennes["points"] == 75.0

    def test_calculer_palmares(self, equipe_standard: Equipe) -> None:
        """Vérifie la génération de la liste des trophées à partir des classements de compétition."""
        controller = AppController()
        comp = Competition(id_competition="C1", nom="Tournoi Principal")
        controller.competition_actuelle = comp

        comp.classement_final = [{"nom": equipe_standard.nom, "victoires": 5}]

        sous_comp = comp.obtenir_ou_creer_sous_comp("Poule A")
        sous_comp.classement_final = [{"nom": equipe_standard.nom, "victoires": 3}]

        trophees = controller.calculer_palmares(equipe_standard)

        assert len(trophees) == 2
        assert any("Vainqueur principal" in t for t in trophees)
        assert any("1er de groupe" in t for t in trophees)

    def test_rechercher_et_obtenir_participants(self, controller_prepare: AppController) -> None:
        """Vérifie la récupération de la liste totale et la recherche filtrée des participants."""
        tous = controller_prepare.obtenir_tous_les_participants()
        assert len(tous) == 4

        recherche = controller_prepare.rechercher_participants_par_nom("Vieux")
        assert len(recherche) == 1
        assert recherche[0].nom == "Vieux Champion"

    def test_inscrire_participant(self, controller_prepare: AppController) -> None:
        """Vérifie l'instanciation d'un nouveau participant et son ajout dans l'annuaire mémoire."""
        nouvelle_equipe = controller_prepare.inscrire_participant(
            type_participant="2", nom="FC Nouveau", provenance="Italie"
        )

        assert nouvelle_equipe is not None
        assert nouvelle_equipe.nom == "FC Nouveau"
        assert len(controller_prepare.rechercher_participants_par_nom("Nouveau")) == 1

    def test_obtenir_structure_match_attendue(self, controller_prepare: AppController) -> None:
        """Vérifie la déduction du schéma de données de performance basé sur les matchs existants."""
        assert controller_prepare.competition_actuelle is not None

        match_test = controller_prepare.competition_actuelle.liste_match[0]
        match_test.performances["Dom"].stats = {"score": 10, "comportement": "Bon"}

        structure = controller_prepare.obtenir_structure_match_attendue()

        assert "Dom" in structure
        assert structure["Dom"]["stats"]["score"] == "nombre"
        assert structure["Dom"]["stats"]["comportement"] == "texte"

    def test_enregistrer_nouveau_match(
        self, controller_prepare: AppController, liste_participants_statistiques: list
    ) -> None:
        """Vérifie la création et l'insertion d'un objet Match dans la compétition courante."""
        assert controller_prepare.competition_actuelle is not None

        participant = liste_participants_statistiques[0]
        nb_matchs_avant = len(controller_prepare.competition_actuelle.liste_match)

        donnees_perf = [{"participant": participant, "role": "Vainqueur", "est_gagnant": True, "stats": {"points": 10}}]

        nouvel_id = controller_prepare.enregistrer_nouveau_match(
            date_match="2024-01-01", liste_donnees_perf=donnees_perf
        )

        assert nouvel_id.startswith("M-")
        assert len(controller_prepare.competition_actuelle.liste_match) == nb_matchs_avant + 1

    def test_modifier_et_supprimer_match(self, controller_prepare: AppController) -> None:
        """Vérifie les opérations de mise à jour et de suppression d'un match existant."""
        assert controller_prepare.competition_actuelle is not None

        match_cible = controller_prepare.competition_actuelle.liste_match[0]
        id_match = match_cible.id_match

        modifications = {"Dom": {"est_gagnant": False, "stats": {"nouveau_score": 99}}}
        succes_modif = controller_prepare.modifier_match(
            id_match, nouvelle_date="2025-01-01", mises_a_jour_perfs=modifications
        )

        assert succes_modif is True
        assert match_cible.date_objet is not None
        assert match_cible.date_objet.year == 2025
        assert match_cible.performances["Dom"].stats["nouveau_score"] == 99

        succes_suppr = controller_prepare.supprimer_match(id_match)

        assert succes_suppr is True
        assert all(m.id_match != id_match for m in controller_prepare.competition_actuelle.liste_match)

    @patch("src.Infrastructure.gestionnaire_csv.GestionnaireCSV.sauvegarder_fichier")
    def test_sauvegarder_matchs(self, mock_sauvegarde: Any, controller_prepare: AppController) -> None:
        """Vérifie l'appel au gestionnaire de fichiers avec les données formatées."""
        succes, nb_matchs, fichier = controller_prepare.sauvegarder_matchs("test.csv")

        assert succes is True
        assert nb_matchs == 3
        assert fichier == "test.csv"
        mock_sauvegarde.assert_called_once()

    def test_securite_aucune_competition_chargee(self) -> None:
        """Vérifie la robustesse des méthodes face à l'absence de compétition instanciée."""
        controller_vide = AppController()
        equipe_test = Equipe(nom="Test")

        assert controller_vide.obtenir_structure_match_attendue() == {}
        assert controller_vide.calculer_palmares(equipe_test) == []
        assert controller_vide.calculer_moyennes_participant(equipe_test) == {}
        assert controller_vide.supprimer_match("M-001") is False
        assert controller_vide.modifier_match("M-001") is False

        bilan, historique = controller_vide.calculer_bilan_historique(equipe_test)
        assert bilan["total"] == 0
        assert historique == []

        face_a_face = controller_vide.calculer_face_a_face(equipe_test, equipe_test)
        assert face_a_face["total"] == 0

    def test_gerer_match_inexistant(self, controller_prepare: AppController) -> None:
        """Vérifie le retour des fonctions de modification avec un identifiant non reconnu."""
        id_introuvable = "MATCH_INCONNU_123"

        succes_suppr = controller_prepare.supprimer_match(id_introuvable)
        succes_modif = controller_prepare.modifier_match(id_introuvable, nouvelle_date="2025-01-01")

        assert succes_suppr is False
        assert succes_modif is False

    def test_enregistrer_match_dans_sous_competition(
        self, controller_prepare: AppController, liste_participants_statistiques: list
    ) -> None:
        """Vérifie l'enregistrement d'un match au sein d'une sous-compétition spécifique."""
        participant = liste_participants_statistiques[0]
        donnees_perf = [{"participant": participant, "role": "Vainqueur", "est_gagnant": True, "stats": {"score": 5}}]

        nouvel_id = controller_prepare.enregistrer_nouveau_match(
            date_match="2024-01-01", liste_donnees_perf=donnees_perf, nom_sous_comp="Poule B"
        )

        comp_principale = controller_prepare.competition_actuelle
        assert comp_principale is not None
        assert "Poule B" in comp_principale.sous_competitions

        sous_comp = comp_principale.sous_competitions["Poule B"]
        assert len(sous_comp.liste_match) == 1
        assert sous_comp.liste_match[0].id_match == nouvel_id

    @patch("src.Infrastructure.gestionnaire_csv.GestionnaireCSV.sauvegarder_fichier")
    def test_sauvegarder_matchs_erreur_systeme(self, mock_sauvegarde: Any, controller_prepare: AppController) -> None:
        """Vérifie la gestion d'une exception levée par le système de fichiers lors de la sauvegarde."""
        mock_sauvegarde.side_effect = OSError("Disque plein ou acces refuse")

        succes, nb_matchs, message = controller_prepare.sauvegarder_matchs("test.csv")

        assert succes is False
        assert nb_matchs == 0
        assert "Disque plein" in message

    def test_sauvegarder_matchs_vide(self) -> None:
        """Vérifie l'annulation de l'opération de sauvegarde si la liste de matchs est vide."""
        controller = AppController()
        controller.competition_actuelle = Competition(id_competition="C1", nom="Vide")

        succes, nb_matchs, message = controller.sauvegarder_matchs("test.csv")

        assert succes is False
        assert nb_matchs == 0
        assert "Aucun match" in message
