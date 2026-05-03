from src.Model.competition import Competition
from src.Model.match import Match


class TestCompetition:
    # Initialisation et paramètres de base

    def test_initialisation_parametres_defaut(self) -> None:
        """Vérifie que les valeurs par défaut sont correctement attribuées si non précisées."""
        comp = Competition(id_competition="C1", nom="Tournoi Test")

        assert comp.id_competition == "C1"
        assert comp.nom == "Tournoi Test"
        assert comp.type_format is None

        # Le dictionnaire des poids doit être vide, jamais None
        assert comp.poids_rounds == {}
        assert comp.liste_match == []
        assert comp.sous_competitions == {}
        assert comp.classement_final == []

    def test_initialisation_avec_parametres(self, competition_championnat: Competition) -> None:
        """Vérifie l'initialisation avec des paramètres complets via la fixture."""
        assert competition_championnat.id_competition == "C01"
        assert competition_championnat.nom == "Ligue 1"
        assert competition_championnat.type_format == "championnat"
        assert competition_championnat.poids_rounds == {}

    # Arborescence et gestion des matchs

    def test_ajouter_match_racine(self, competition_championnat: Competition, match_standard: Match) -> None:
        """Vérifie que l'ajout d'un match incrémente bien la liste au niveau racine."""
        competition_championnat.ajouter_match(match_standard)

        assert len(competition_championnat.liste_match) == 1
        assert competition_championnat.liste_match[0] == match_standard

    def test_obtenir_ou_creer_sous_comp_nouvelle(self) -> None:
        """Vérifie la création d'une sous-compétition et l'héritage de ses paramètres."""
        comp_racine = Competition(id_competition="C1", nom="Test", type_format="elimination", poids_rounds={"F": 1})

        sous_comp = comp_racine.obtenir_ou_creer_sous_comp("Poule A")

        assert "Poule A" in comp_racine.sous_competitions
        assert sous_comp.id_competition == "C1_0"
        assert sous_comp.nom == "Poule A"
        assert sous_comp.type_format == "elimination"
        assert sous_comp.poids_rounds == {"F": 1}

    def test_obtenir_ou_creer_sous_comp_existante(self, competition_championnat: Competition) -> None:
        """Vérifie que l'appel sur une sous-compétition existante ne la recrée pas."""
        sous_comp_1 = competition_championnat.obtenir_ou_creer_sous_comp("Groupe 1")
        sous_comp_1.ajouter_match(Match(id_match="M1"))

        sous_comp_2 = competition_championnat.obtenir_ou_creer_sous_comp("Groupe 1")

        assert sous_comp_1 is sous_comp_2
        assert len(sous_comp_2.liste_match) == 1
        assert len(competition_championnat.sous_competitions) == 1

    def test_obtenir_tous_les_matchs_arborescence(
        self, competition_championnat: Competition, match_standard: Match
    ) -> None:
        """Vérifie que l'extraction récupère les matchs de la racine ET des sous-groupes."""
        competition_championnat.ajouter_match(match_standard)

        sous_comp = competition_championnat.obtenir_ou_creer_sous_comp("Phase Finale")
        match_finale = Match(id_match="M2")
        sous_comp.ajouter_match(match_finale)

        tous_matchs = competition_championnat.obtenir_tous_les_matchs()

        assert len(tous_matchs) == 2
        assert match_standard in tous_matchs
        assert match_finale in tous_matchs

    def test_obtenir_tous_les_matchs_vide(self, competition_championnat: Competition) -> None:
        """Vérifie le retour en cas d'absence totale de matchs."""
        assert competition_championnat.obtenir_tous_les_matchs() == []

    # Représentation texte

    def test_str_affichage(self, competition_championnat: Competition, match_standard: Match) -> None:
        """Vérifie le formatage de la chaîne de caractères avec et sans sous-groupes."""
        # Cas sans matchs et sans sous-groupes
        texte_vide = str(competition_championnat)
        assert "Ligue 1" in texte_vide
        assert "0 matchs" in texte_vide
        assert "sous-groupes" not in texte_vide

        # Cas avec des données
        competition_championnat.ajouter_match(match_standard)
        competition_championnat.obtenir_ou_creer_sous_comp("Poule A")

        texte_rempli = str(competition_championnat)
        assert "1 matchs" in texte_rempli
        assert "répartis dans 1 sous-groupes" in texte_rempli
