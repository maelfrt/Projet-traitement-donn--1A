from src.Model.coach import Coach


class TestCoach:
    # Exportation des données

    def test_initialisation_et_to_dict(self, coach_standard: Coach) -> None:
        """Vérifie l instanciation du staff et son formatage en dictionnaire pour Pandas."""
        assert coach_standard.nom == "Phil Jackson"
        assert coach_standard.specialite == "Tactique"

        dico = coach_standard.to_dict()

        assert dico["id_personne"] == "C001"
        assert dico["nom"] == "Phil Jackson"
        assert dico["specialite"] == "Tactique"

    # Représentation textuelle

    def test_str_affichage_dynamique(self, coach_standard: Coach) -> None:
        """Vérifie le formatage conditionnel de la chaîne de caractères du coach."""
        coach_standard.provenance = "USA"
        texte_complet = str(coach_standard)

        assert "Coach : Phil Jackson" in texte_complet
        assert "(USA)" in texte_complet
        assert "Spécialité : Tactique" in texte_complet
        assert "ID: C001" in texte_complet

        coach_minimal = Coach(nom="Inconnu", id_personne="C2")
        texte_minimal = str(coach_minimal)

        assert "()" not in texte_minimal
        assert "Spécialité" not in texte_minimal
