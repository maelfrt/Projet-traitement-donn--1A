from src.Analysis.ranking_engine import RankingEngine
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance


class TestRankingEngine:
    # Tests de la logique de départage

    def test_departager_finalistes_et_petites_finales(self) -> None:
        """Vérifie l'attribution des notes pour les vainqueurs et perdants de finales."""
        moteur = RankingEngine()

        # Pour la grande finale, le gagnant obtient la note parfaite de 0.0 (1er) et le perdant 1.0 (2e)
        assert moteur._departager_finalistes(nom_du_tour="Final", est_gagnant=True, poids_de_base=1) == 0.0
        assert moteur._departager_finalistes(nom_du_tour="Final", est_gagnant=False, poids_de_base=1) == 1.0

        # C'est la même idée pour la petite finale (médaille de bronze), mais avec des notes décalées
        assert moteur._departager_finalistes(nom_du_tour="Bronze Medal", est_gagnant=True, poids_de_base=2) == 2.0
        assert moteur._departager_finalistes(nom_du_tour="Bronze Medal", est_gagnant=False, poids_de_base=2) == 3.0

    def test_departager_tour_classique(self) -> None:
        """Vérifie qu'un perdant d'un tour classique reçoit bien sa pénalité décimale."""
        moteur = RankingEngine()

        # La pénalité de +0.9 est une petite astuce mathématique : elle garantit que le perdant
        # est classé juste derrière tous les gagnants de ce même tour, sans pour autant
        # se retrouver à égalité avec les éliminés du tour précédent.
        assert moteur._departager_finalistes(nom_du_tour="Round of 16", est_gagnant=False, poids_de_base=4) == 4.9

    # Tests sur les différents formats de compétition

    def test_calculer_championnat(self) -> None:
        """Vérifie que le classement d'un championnat se base bien sur le nombre de victoires."""
        moteur = RankingEngine()
        comp = Competition(id_competition="C1", nom="Ligue", type_format="championnat")
        match = Match(id_match="m1")

        eq1 = Equipe(nom="Gagnant", id_equipe="E1")
        eq2 = Equipe(nom="Perdant", id_equipe="E2")

        match.ajouter_performance("Dom", Performance(eq1, "Dom", est_gagnant=True))
        match.ajouter_performance("Ext", Performance(eq2, "Ext", est_gagnant=False))
        comp.ajouter_match(match)

        classement = moteur._calculer_championnat(comp)

        # On s'assure que le système a bien comptabilisé la victoire pour faire passer l'équipe en premier
        assert len(classement) == 2
        assert classement[0]["nom"] == "Gagnant"
        assert classement[0]["victoires"] == 1
        assert classement[1]["nom"] == "Perdant"
        assert classement[1]["victoires"] == 0

    def test_calculer_elimination(self) -> None:
        """Vérifie le tri complexe basé sur le poids des tours dans un arbre d'élimination."""
        moteur = RankingEngine()
        poids = {"Final": 1, "Semi final": 2}
        comp = Competition(id_competition="C1", nom="Tournoi", type_format="elimination", poids_rounds=poids)

        vainqueur = Equipe(nom="Vainqueur", id_equipe="E1")
        finaliste = Equipe(nom="Finaliste", id_equipe="E2")
        demi_finaliste = Equipe(nom="Demi-Finaliste", id_equipe="E3")

        # On simule la grande finale
        m_finale = Match(id_match="m1", type_match="Final")
        m_finale.ajouter_performance("Dom", Performance(vainqueur, "Dom", est_gagnant=True))
        m_finale.ajouter_performance("Ext", Performance(finaliste, "Ext", est_gagnant=False))

        # Puis une demi-finale pour voir si le perdant est bien relégué derrière les finalistes
        m_demi = Match(id_match="m2", type_match="Semi final")
        m_demi.ajouter_performance("Dom", Performance(vainqueur, "Dom", est_gagnant=True))
        m_demi.ajouter_performance("Ext", Performance(demi_finaliste, "Ext", est_gagnant=False))

        comp.ajouter_match(m_finale)
        comp.ajouter_match(m_demi)

        classement = moteur._calculer_elimination(comp)

        # Dans ce format, la meilleure place correspond à la note (le poids) la plus basse.
        assert len(classement) == 3
        assert classement[0]["nom"] == "Vainqueur"
        assert classement[0]["poids_atteint"] == 0.0  # Gagnant de la finale
        assert classement[1]["nom"] == "Finaliste"
        assert classement[1]["poids_atteint"] == 1.0  # Perdant de la finale
        assert classement[2]["nom"] == "Demi-Finaliste"
        assert classement[2]["poids_atteint"] == 2.9  # Perdant de la demi-finale (Poids 2 + 0.9)

    # Tests de sécurité et de gestion de l'arborescence

    def test_classer_une_competition_sans_match(self) -> None:
        """Vérifie que le classement reste vide s'il n'y a aucune donnée à traiter."""
        moteur = RankingEngine()
        comp = Competition(id_competition="C1", nom="Vide", type_format="championnat")

        # L'algorithme ne doit pas planter s'il parcourt un objet vide
        moteur._classer_une_competition(comp)
        assert comp.classement_final == []

    def test_classer_une_competition_format_inconnu(self) -> None:
        """Vérifie qu'un format non prévu dans la configuration ne fait pas planter le système."""
        moteur = RankingEngine()
        comp = Competition(id_competition="C1", nom="Bizarre", type_format="nimportequoi")
        comp.ajouter_match(Match(id_match="M1"))

        moteur._classer_une_competition(comp)
        assert comp.classement_final == []

    def test_generer_classement_recursif(self) -> None:
        """Vérifie que l'algorithme fouille bien dans les sous-groupes (poules, etc.) de manière autonome."""
        moteur = RankingEngine()
        comp_principale = Competition(id_competition="C1", nom="Principale", type_format="championnat")
        sous_comp = comp_principale.obtenir_ou_creer_sous_comp("Poule A")

        eq = Equipe(nom="Team", id_equipe="E1")
        match = Match(id_match="m1")
        match.ajouter_performance("Dom", Performance(eq, "Dom", est_gagnant=True))

        # Le piège classique : on met le match dans la poule, pas à la racine de la compétition
        sous_comp.ajouter_match(match)

        moteur.generer_classement(comp_principale)

        # La compétition principale reste logiquement vide car elle n'a pas de matchs directs
        assert comp_principale.classement_final == []

        # Mais l'algorithme a bien fait son travail d'exploration et a classé la sous-compétition
        assert len(sous_comp.classement_final) == 1
        assert sous_comp.classement_final[0]["nom"] == "Team"
