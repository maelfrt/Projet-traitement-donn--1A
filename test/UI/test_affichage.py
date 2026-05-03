from src.Model.athlete import Athlete
from src.UI.affichage import afficher_a_propos, afficher_en_tete, afficher_profil


class TestAffichage:
    def test_afficher_en_tete(self, capsys) -> None:
        """Verifie que la banniere principale s affiche correctement a l ecran"""
        afficher_en_tete()

        # capsys prend une photo de tout ce qui a ete affiche dans la console
        capture = capsys.readouterr()

        assert "APPLICATION DE TRAITEMENT" in capture.out

    def test_afficher_a_propos(self, capsys) -> None:
        """Verifie l affichage du manuel d aide et des noms de l equipe"""
        afficher_a_propos()

        capture = capsys.readouterr()

        assert "AIDE, INFORMATIONS ET CRÉDITS" in capture.out
        # On verifie qu un membre de l equipe est bien credite
        assert "Kilian Crumbach" in capture.out

    def test_afficher_profil_athlete(self, capsys, athlete_standard: Athlete) -> None:
        """Verifie que les donnees du joueur sont bien formatees en texte"""
        # On prepare des fausses donnees pour accompagner le profil
        palmares_test = ["Champion Olympique 2024"]
        moyennes_test = {"buts": 2.5}

        afficher_profil(partcipant=athlete_standard, palmares=palmares_test, moyennes=moyennes_test)

        capture = capsys.readouterr()

        # Verification des informations de base
        assert "FICHE PROFIL : JEAN DUPONT" in capture.out
        assert "Joueur" in capture.out

        # Verification de l affichage du palmares
        assert "Champion Olympique 2024" in capture.out

        # Verification de l affichage des moyennes
        assert "Buts" in capture.out
        assert "2.5" in capture.out
