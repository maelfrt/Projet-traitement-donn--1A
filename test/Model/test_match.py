from datetime import UTC, datetime

from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance


class TestMatch:
    def test_initialisation_dates_multiples(self, match_standard: Match) -> None:
        """Vérifie la tolérance du constructeur face à différents formats de date."""
        assert match_standard.date_objet is not None
        assert match_standard.date_objet.year == 2024
        assert match_standard.date_objet.tzinfo == UTC

        date_native = datetime(2025, 1, 1, tzinfo=UTC)
        match_obj = Match(date=date_native)
        assert match_obj.date_objet is not None
        assert match_obj.date_objet.year == 2025

        match_invalide = Match(date="Hier après-midi")
        assert match_invalide.date_objet is None

        match_vide = Match(date=None)
        assert match_vide.date_objet is None

    def test_initialisation_kwargs_supplementaires(self) -> None:
        """Vérifie la capture des paramètres additionnels non définis dans le constructeur."""
        match_param = Match(id_match="M1", arbitre="Colina", meteo="Pluie")

        assert "arbitre" in match_param.infos_supplementaires
        assert match_param.infos_supplementaires["meteo"] == "Pluie"

    def test_renvoyer_gagnant_victoire_classique(self, match_standard: Match, equipe_standard: Equipe) -> None:
        """Vérifie l'extraction du nom du vainqueur basé sur le flag est_gagnant."""
        eq_exterieur = Equipe(nom="Celtics")

        perf_dom = Performance(equipe_standard, role="Domicile", est_gagnant=True)
        perf_ext = Performance(eq_exterieur, role="Exterieur", est_gagnant=False)

        match_standard.ajouter_performance("Domicile", perf_dom)
        match_standard.ajouter_performance("Exterieur", perf_ext)

        assert match_standard.renvoyer_gagnant() == "Lakers (Domicile)"

    def test_renvoyer_gagnant_match_nul(self, match_standard: Match, equipe_standard: Equipe) -> None:
        """Vérifie la détection d'égalité lorsque personne n'a le statut est_gagnant."""
        eq_exterieur = Equipe(nom="Celtics")

        perf_dom = Performance(equipe_standard, role="Domicile", est_gagnant=False, est_nul=True)
        perf_ext = Performance(eq_exterieur, role="Exterieur", est_gagnant=False, est_nul=True)

        match_standard.ajouter_performance("Domicile", perf_dom)
        match_standard.ajouter_performance("Exterieur", perf_ext)

        assert match_standard.renvoyer_gagnant() == "Match nul"

    def test_renvoyer_gagnant_sans_performances(self, match_standard: Match) -> None:
        """Vérifie le message de sécurité retourné si le match est vide."""
        assert match_standard.renvoyer_gagnant() == "Résultat non saisi"

    def test_to_dict_formatage_complet(self, performance_gagnante: Performance) -> None:
        """Vérifie la sérialisation de l'objet pour Pandas et l'aplatissement du dictionnaire."""
        match_test = Match(id_match="M-TEST", date="2024-01-01", lieu="Paris", bonus="Oui")

        match_test.ajouter_performance("Equipe Domicile", performance_gagnante)

        dico = match_test.to_dict()

        assert dico["id_match"] == "M-TEST"
        assert dico["date"] == "2024-01-01"
        assert dico["lieu"] == "Paris"
        assert dico["bonus"] == "Oui"

        assert "equipe_domicile_nom" in dico
        assert dico["equipe_domicile_nom"] == "Jean Dupont"
        assert dico["equipe_domicile_est_gagnant"] is True
        assert dico["equipe_domicile_points"] == 25

    def test_to_dict_date_inconnue(self) -> None:
        """Vérifie la valeur de repli dans le dictionnaire si la date est absente."""
        match_sans_date = Match()
        dico = match_sans_date.to_dict()
        assert dico["date"] == "Date inconnue"

    def test_str_affichage_dynamique(self, match_standard: Match, equipe_standard: Equipe) -> None:
        """Vérifie l'adaptation de la chaîne retournée selon le nombre de participants et l'état de la date."""
        eq_exterieur = Equipe(nom="Celtics")

        texte_vide = str(match_standard)
        assert "[2024/07/25]" in texte_vide
        assert "Match sans participants" in texte_vide
        assert "Non joué" in texte_vide

        match_standard.ajouter_performance("Dom", Performance(equipe_standard, "Dom", est_gagnant=True))
        texte_seul = str(match_standard)
        assert "Lakers vs Adversaire inconnu" in texte_seul
        assert "🏆 Lakers" in texte_seul

        match_standard.ajouter_performance("Ext", Performance(eq_exterieur, "Ext", est_gagnant=False))
        texte_complet = str(match_standard)
        assert "Lakers vs Celtics" in texte_complet
        assert "🏆 Lakers" in texte_complet

        m_nul = Match()
        m_nul.ajouter_performance("Dom", Performance(equipe_standard, "Dom", est_nul=True))
        m_nul.ajouter_performance("Ext", Performance(eq_exterieur, "Ext", est_nul=True))
        texte_nul = str(m_nul)
        assert "🤝 Match nul" in texte_nul
