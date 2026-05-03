from typing import Any
from unittest.mock import patch

from src.Analysis.statistiques import calculer_statistiques_globales
from src.Core.app_controller import AppController
from src.Model.athlete import Athlete
from src.Model.competition import Competition


class TestIntegrationEtFonctionnel:
    # Scenarios complets de bout en bout

    @patch("src.Core.app_controller.time_module.time", side_effect=range(1000, 2000))
    def test_simulation_complete_championnat(self, mock_time: Any) -> None:
        """Verifie le cycle de vie complet d un tournoi de l inscription au palmares final"""
        controller = AppController()

        # Initialisation manuelle d une competition vierge
        comp = Competition(id_competition="L1", nom="Ligue Test", type_format="championnat")
        controller.competition_actuelle = comp

        # Inscription des participants via le controleur
        psg = controller.inscrire_participant("2", "PSG", "Paris")
        om = controller.inscrire_participant("2", "OM", "Marseille")
        ol = controller.inscrire_participant("2", "OL", "Lyon")

        assert psg is not None and om is not None and ol is not None

        # Creation du match 1 PSG gagne contre OM
        perf_m1: list[dict[str, Any]] = [
            {"participant": psg, "role": "Dom", "est_gagnant": True, "stats": {"buts": 2}},
            {"participant": om, "role": "Ext", "est_gagnant": False, "stats": {"buts": 0}},
        ]
        controller.enregistrer_nouveau_match("2024-01-01", perf_m1)

        # Creation du match 2 PSG gagne contre OL
        perf_m2: list[dict[str, Any]] = [
            {"participant": psg, "role": "Dom", "est_gagnant": True, "stats": {"buts": 3}},
            {"participant": ol, "role": "Ext", "est_gagnant": False, "stats": {"buts": 1}},
        ]
        controller.enregistrer_nouveau_match("2024-01-08", perf_m2)

        # Creation du match 3 OM gagne contre OL
        perf_m3: list[dict[str, Any]] = [
            {"participant": om, "role": "Dom", "est_gagnant": True, "stats": {"buts": 1}},
            {"participant": ol, "role": "Ext", "est_gagnant": False, "stats": {"buts": 0}},
        ]
        controller.enregistrer_nouveau_match("2024-01-15", perf_m3)

        # Validation du moteur de classement
        classement = comp.classement_final
        assert len(classement) == 3

        # Le PSG doit etre premier avec 2 victoires
        assert classement[0]["nom"] == "PSG"
        assert classement[0]["victoires"] == 2

        # L OM doit etre deuxieme avec 1 victoire
        assert classement[1]["nom"] == "OM"
        assert classement[1]["victoires"] == 1

        # Validation de l attribution du palmares
        trophees_psg = controller.calculer_palmares(psg)
        assert len(trophees_psg) == 1
        assert "Vainqueur principal" in trophees_psg[0]

    @patch("src.Core.app_controller.time_module.time", side_effect=range(2000, 3000))
    def test_integration_recherche_et_historique(self, mock_time: Any) -> None:
        """Verifie que le moteur de recherche communique bien avec l historique des matchs"""
        controller = AppController()
        comp = Competition(id_competition="T1", nom="Tournoi Tennis", type_format="elimination")
        controller.competition_actuelle = comp

        joueur_a = controller.inscrire_participant("1", "Federer", "SUI")
        joueur_b = controller.inscrire_participant("1", "Nadal", "ESP")

        assert joueur_a is not None and joueur_b is not None

        # Creation d une confrontation directe
        perf_finale: list[dict[str, Any]] = [
            {"participant": joueur_a, "role": "Vainqueur", "est_gagnant": True, "stats": {}},
            {"participant": joueur_b, "role": "Perdant", "est_gagnant": False, "stats": {}},
        ]
        controller.enregistrer_nouveau_match("2024-06-01", perf_finale)

        # Etape 1 Recherche textuelle simulant l action utilisateur
        resultats_recherche = controller.rechercher_participants_par_nom("fede")
        assert len(resultats_recherche) == 1
        cible = resultats_recherche[0]

        # Etape 2 Generation du bilan a partir du resultat de la recherche
        stats, historique = controller.calculer_bilan_historique(cible)

        assert stats["total"] == 1
        assert stats["victoires"] == 1
        assert historique[0]["adversaire"] == "Nadal"

    @patch("src.Core.app_controller.time_module.time", side_effect=range(3000, 4000))
    def test_integration_statistiques_globales(self, mock_time: Any) -> None:
        """Verifie la compilation des statistiques globales sur une base de donnees peuplee"""
        controller = AppController()
        comp = Competition(id_competition="S1", nom="Saison Echecs")
        controller.competition_actuelle = comp

        # Ajout de joueurs avec des ages varies pour tester la demographie
        j1 = controller.inscrire_participant("1", "Carlsen", "NOR")
        j2 = controller.inscrire_participant("1", "Firouzja", "FRA")

        # Conversion du typage pour eviter les erreurs union attr de MyPy
        assert isinstance(j1, Athlete)
        assert isinstance(j2, Athlete)

        j1.date_naissance = controller.valider_et_convertir_date("1990-11-30")
        j2.date_naissance = controller.valider_et_convertir_date("2003-06-18")

        # Match declare nul
        perf_nulle: list[dict[str, Any]] = [
            {"participant": j1, "role": "J1", "est_gagnant": False, "est_nul": True, "stats": {}},
            {"participant": j2, "role": "J2", "est_gagnant": False, "est_nul": True, "stats": {}},
        ]
        controller.enregistrer_nouveau_match("2024-02-01", perf_nulle)

        # Execution du moteur de statistiques
        tous_participants = controller.obtenir_tous_les_participants()
        stats_globales = calculer_statistiques_globales(comp, tous_participants)

        # Validation des aggregations croisees
        assert stats_globales["total_matchs"] == 1
        assert stats_globales["total_athletes"] == 2
        assert stats_globales["plus_jeune"]["nom"] == "Firouzja"
        assert stats_globales["plus_age"]["nom"] == "Carlsen"

    @patch("src.Core.app_controller.time_module.time", side_effect=range(4000, 5000))
    def test_integration_modification_match_et_recalcul(self, mock_time: Any) -> None:
        """Verifie qu une modification de match declenche bien la mise a jour des donnees transversales"""
        controller = AppController()
        comp = Competition(id_competition="C1", nom="Test Modif", type_format="championnat")
        controller.competition_actuelle = comp

        eq_a = controller.inscrire_participant("2", "Equipe A")
        eq_b = controller.inscrire_participant("2", "Equipe B")

        assert eq_a is not None and eq_b is not None

        # Match initial A gagne
        perf: list[dict[str, Any]] = [
            {"participant": eq_a, "role": "Dom", "est_gagnant": True, "stats": {"score": 2}},
            {"participant": eq_b, "role": "Ext", "est_gagnant": False, "stats": {"score": 0}},
        ]
        id_match = controller.enregistrer_nouveau_match("2024-01-01", perf)

        assert comp.classement_final[0]["nom"] == "Equipe A"

        # L administrateur modifie le resultat B gagne sur tapis vert
        modifications = {
            "Dom": {"est_gagnant": False, "stats": {"score": 0}},
            "Ext": {"est_gagnant": True, "stats": {"score": 3}},
        }
        controller.modifier_match(id_match, mises_a_jour_perfs=modifications)

        # Le classement doit avoir ete recalcule automatiquement par le controleur
        assert comp.classement_final[0]["nom"] == "Equipe B"
        assert comp.classement_final[0]["victoires"] == 1
        assert comp.classement_final[1]["nom"] == "Equipe A"
        assert comp.classement_final[1]["victoires"] == 0
