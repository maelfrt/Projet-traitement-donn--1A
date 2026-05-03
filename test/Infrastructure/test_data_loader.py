from unittest.mock import mock_open, patch

import numpy as np
import pandas as pd

from src.Infrastructure.data_loader import DataLoader
from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match


class TestDataLoader:
    def test_est_valeur_valide(self) -> None:
        """Vérifie la robustesse du filtre de données vides."""
        assert DataLoader._est_valeur_valide("LeBron James") is True
        assert DataLoader._est_valeur_valide(25) is True
        assert DataLoader._est_valeur_valide("") is False
        assert DataLoader._est_valeur_valide(None) is False
        assert DataLoader._est_valeur_valide(np.nan) is False

    def test_convertir_en_nombre(self) -> None:
        """Vérifie la sécurisation de la conversion numérique."""
        loader = DataLoader()
        assert loader._convertir_en_nombre("25") == 25.0
        assert loader._convertir_en_nombre("25.5") == 25.5
        assert loader._convertir_en_nombre("N/A") == 0.0
        assert loader._convertir_en_nombre("") == 0.0

    def test_filtrer_via_mapping_json(self) -> None:
        """Vérifie que seules les colonnes mappées sont conservées."""
        loader = DataLoader()
        ligne = {"col_a": "ValeurA", "col_b": "", "col_c": "ValeurC"}
        mapping = {"attribut_1": "col_a", "attribut_2": "col_b"}

        resultat = loader._filtrer_via_mapping_json(ligne, mapping)
        assert "attribut_1" in resultat
        assert "attribut_2" not in resultat

    def test_reinitialiser_bases(self) -> None:
        """Vérifie le nettoyage du cache lors d'un changement de sport."""
        loader = DataLoader()
        loader.base_athletes = pd.DataFrame([1, 2, 3])
        loader._annuaire_participants = {"test": "test"}

        loader._reinitialiser_bases()

        assert loader.base_athletes.empty
        assert len(loader._annuaire_participants) == 0

    def test_ajouter_participant_en_memoire(self) -> None:
        """Vérifie l'insertion à chaud d'un participant créé par l'utilisateur."""
        loader = DataLoader()
        joueur = Athlete(nom="Dupont", id_personne="P1")
        loader.ajouter_participant_en_memoire(joueur, "athlete")

        assert not loader.base_athletes.empty
        assert "p1" in loader._annuaire_participants

        equipe = Equipe(nom="PSG", id_equipe="E1")
        loader.ajouter_participant_en_memoire(equipe, "equipe")

        assert not loader.base_equipes.empty
        assert "psg" in loader._annuaire_participants

    def test_indexer_participants_en_cache_succes(self) -> None:
        """Vérifie la construction du dictionnaire d'accès rapide."""
        loader = DataLoader()
        joueur_1 = Athlete(nom="Dupont", id_personne="P1")
        equipe_1 = Equipe(nom="Lakers", id_equipe="E1")

        loader.base_athletes = pd.DataFrame([{"id_technique": "P1", "objet": joueur_1}])
        loader.base_equipes = pd.DataFrame([{"id_technique": "E1", "objet": equipe_1}])
        loader._indexer_participants_en_cache()

        assert len(loader._annuaire_participants) == 3
        assert loader._rechercher_participant("P1") == joueur_1

    def test_rechercher_participant(self) -> None:
        """Vérifie l'accès au cache et ses sécurités."""
        loader = DataLoader()
        loader._annuaire_participants = {"p1": "Test"}

        assert loader._rechercher_participant("P1") == "Test"
        assert loader._rechercher_participant("") is None

    def test_lier_athletes_aux_equipes(self) -> None:
        """Vérifie l'association automatique joueur/club post-chargement."""
        loader = DataLoader()
        joueur = Athlete(nom="Dupont", id_personne="P1", equipe_actuelle="Lakers")
        equipe = Equipe(nom="Lakers", id_equipe="E1")

        loader._annuaire_participants = {"p1": joueur, "lakers": equipe}
        loader._lier_athletes_aux_equipes()

        assert len(equipe.liste_athlete) == 1
        assert equipe.liste_athlete[0] == joueur

    def test_lecture_fichier_csv_temporaire(self, tmp_path) -> None:
        """Vérifie la bonne intégration avec l'API Pandas."""
        dossier_test = tmp_path / "donnees_test"
        dossier_test.mkdir()
        fichier_csv = dossier_test / "test_athletes.csv"
        fichier_csv.write_text("id,nom,age\n1,Dupont,25", encoding="utf-8")

        dataframe = pd.read_csv(fichier_csv)
        assert len(dataframe) == 1

    @patch("src.Infrastructure.gestionnaire_csv.GestionnaireCSV.charger_fichier")
    def test_fusionner_et_nettoyer_csv(self, mock_charger) -> None:
        """Vérifie la jointure SQL-like de Pandas via la configuration."""
        loader = DataLoader()
        df_principal = pd.DataFrame({"id": [1], "id_ligue": [10]})
        df_joint = pd.DataFrame({"id": [10], "nom_ligue": ["L1"]})

        mock_charger.side_effect = [df_principal, df_joint]

        config = {
            "nom_fichier": "principal.csv",
            "jointures": [
                {
                    "fichier": "joint.csv",
                    "cle_source": "id_ligue",
                    "cle_cible": "id",
                    "renommer": {"nom_ligue": "Ligue"},
                }
            ],
        }

        df_resultat = loader._fusionner_et_nettoyer_csv(config)
        assert "Ligue" in df_resultat.columns
        assert df_resultat.iloc[0]["Ligue"] == "L1"

    @patch("src.Infrastructure.data_loader.DataLoader._fusionner_et_nettoyer_csv")
    def test_charger_participants(self, mock_fusionner) -> None:
        """Vérifie l'instanciation en masse des objets Participant."""
        loader = DataLoader()
        mock_fusionner.return_value = pd.DataFrame({"id_personne": ["P1"], "nom": ["Test"]})

        config = {"mapping": {"id_personne": "id_personne", "nom": "nom"}}
        loader._charger_participants(config, Athlete, "base_athletes")

        assert not loader.base_athletes.empty
        assert loader.base_athletes.iloc[0]["objet"].nom == "Test"

    @patch("src.Infrastructure.data_loader.DataLoader._fusionner_et_nettoyer_csv")
    @patch("src.Infrastructure.data_loader.DataLoader._instancier_match")
    def test_charger_matchs(self, mock_instancier, mock_fusionner) -> None:
        """Vérifie le rangement des matchs dans l'arborescence (poules, etc.)."""
        loader = DataLoader()
        mock_fusionner.return_value = pd.DataFrame({"id_match": ["M1"], "groupe": ["A"]})

        faux_match = Match(id_match="M1")
        mock_instancier.return_value = faux_match
        comp = Competition(id_competition="C1", nom="Test")
        config = {"cle_groupement": "groupe"}

        loader._charger_matchs(config, comp)

        assert not loader.base_matchs.empty
        assert "A" in comp.sous_competitions
        assert len(comp.sous_competitions["A"].liste_match) == 1

    @patch("builtins.open", new_callable=mock_open, read_data='{"sport": "Test", "fichiers": {}}')
    def test_initialiser_competition(self, mock_fichier) -> None:
        """Vérifie le déclencheur principal lisant le JSON."""
        loader = DataLoader()
        comp = loader.initialiser_competition("test.json")
        assert comp.nom == "Test"

    def test_determiner_resultat_score_victoire(self) -> None:
        """Verifie une victoire classique aux points."""
        loader = DataLoader()
        ligne = {"buts_dom": 3, "buts_ext": 1}
        stats = {"buts": 3}
        regles = {"methode": "comparaison", "stat_cible": "buts", "logique": "plus_grand"}
        config_glob = {"performances": {"Dom": {"stats": {"buts": "buts_dom"}}, "Ext": {"stats": {"buts": "buts_ext"}}}}

        gagne, nul = loader._determiner_resultat(ligne, stats, "Dom", {}, regles, config_glob)
        assert gagne is True
        assert nul is False

    def test_determiner_resultat_score_egalite(self) -> None:
        """Verifie la detection d un match nul."""
        loader = DataLoader()
        ligne = {"buts_dom": 2, "buts_ext": 2}
        stats = {"buts": 2}
        regles = {"methode": "comparaison", "stat_cible": "buts", "logique": "plus_grand"}
        config_glob = {"performances": {"Dom": {"stats": {"buts": "buts_dom"}}, "Ext": {"stats": {"buts": "buts_ext"}}}}

        gagne, nul = loader._determiner_resultat(ligne, stats, "Dom", {}, regles, config_glob)
        assert gagne is False
        assert nul is True

    def test_determiner_resultat_victoire_par_defaut(self) -> None:
        """Verifie la gestion des abandons et forfaits."""
        loader = DataLoader()
        ligne = {"buts_dom": "forfait", "buts_ext": 0}
        stats = {"buts": "forfait"}
        regles = {"methode": "comparaison", "stat_cible": "buts", "victoire_par_defaut": ["forfait"]}
        config_glob = {"performances": {"Dom": {"stats": {"buts": "buts_dom"}}, "Ext": {"stats": {"buts": "buts_ext"}}}}

        gagne, nul = loader._determiner_resultat(ligne, stats, "Dom", {}, regles, config_glob)
        assert gagne is True
        assert nul is False

    def test_determiner_resultat_direct(self) -> None:
        """Verifie une logique de victoire déclarative (ex: badminton)."""
        loader = DataLoader()
        ligne = {"vainqueur": "equipe_1"}
        regles = {"methode": "directe", "colonne_cible": "vainqueur"}
        config_role = {"valeur_victoire": "equipe_1", "colonne_participant": "id"}

        gagne, nul = loader._determiner_resultat(ligne, {}, "Dom", config_role, regles, {})
        assert gagne is True
        assert nul is False

    def test_instancier_match_creation_complete(self) -> None:
        """Verifie l'extraction correcte d'un match avec toutes ses statistiques."""
        loader = DataLoader()

        # On peuple le cache NATIVEMENT avec de vrais objets (pas de Mocks capricieux)
        joueur_a = Athlete(nom="Alpha", id_personne="ID_A")
        joueur_b = Athlete(nom="Beta", id_personne="ID_B")
        loader._annuaire_participants = {"id_a": joueur_a, "id_b": joueur_b}

        ligne = {
            "id_match": "M01",
            "date": "2024-01-01",
            "joueur_a": "ID_A",
            "joueur_b": "ID_B",
            "score_a": 10,
            "score_b": 5,
        }

        config = {
            "mapping_base": {"id_match": "id_match", "date": "date"},
            "performances": {
                "Equipe A": {"colonne_participant": "joueur_a", "stats": {"points": "score_a"}},
                "Equipe B": {"colonne_participant": "joueur_b", "stats": {"points": "score_b"}},
            },
            "regle_victoire": {"methode": "comparaison", "stat_cible": "points", "logique": "plus_grand"},
        }

        match_cree = loader._instancier_match(ligne, config, index_ligne=1)

        assert match_cree is not None
        assert match_cree.id_match == "M01"
        assert "Equipe A" in match_cree.performances
        assert match_cree.performances["Equipe A"].est_gagnant is True
        assert match_cree.performances["Equipe A"].stats["points"] == 10
        assert match_cree.performances["Equipe B"].est_gagnant is False
        assert match_cree.performances["Equipe B"].stats["points"] == 5

    def test_instancier_match_participant_introuvable(self) -> None:
        """Verifie la gestion d une ligne ou le joueur n est pas dans l annuaire."""
        loader = DataLoader()

        # On laisse l'annuaire vide volontairement
        loader._annuaire_participants = {}

        ligne = {"id_match": "M01", "joueur_a": "INCONNU"}
        config = {
            "mapping_base": {"id_match": "id_match"},
            "performances": {"Dom": {"colonne_participant": "joueur_a"}},
            "regle_victoire": {},
        }

        match_cree = loader._instancier_match(ligne, config, index_ligne=1)
        assert len(match_cree.performances) == 0
