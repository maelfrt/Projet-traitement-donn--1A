from src.Analysis.search_engine import SearchEngine
from src.Model.athlete import Athlete
from src.Model.equipe import Equipe


class AnnuaireSimule:
    """
    On crée un faux DataLoader simplifié.
    Cela permet d'injecter exactement les données que l'on veut tester,
    sans avoir besoin de charger de vrais fichiers CSV.
    """

    def __init__(self, participants: dict) -> None:
        self._annuaire_participants = participants if participants is not None else {}


class TestSearchEngine:
    def test_securite_annuaire_manquant(self) -> None:
        """Vérifie que l'application ne plante pas si on cherche avant d'avoir chargé un sport."""
        # On crée un objet Python vide qui n'a aucun attribut (donc pas de _annuaire_participants)
        objet_vide = object()

        moteur = SearchEngine(data_loader=objet_vide)
        resultats = moteur.chercher_athlete_par_nom("Djokovic")

        # Le moteur doit intercepter l'erreur et renvoyer une liste vide, sans faire planter le code
        assert resultats == []

    def test_objet_mal_forme_ignore(self) -> None:
        """Vérifie la robustesse si la mémoire contient un objet corrompu sans attribut 'nom'."""

        class ObjetCorrompu:
            pass  # Une classe vide sans attribut 'nom'

        joueur_valide = Athlete(nom="Valide", id_personne="1")

        # On glisse l'objet corrompu dans la base de données
        loader = AnnuaireSimule({"1": joueur_valide, "2": ObjetCorrompu()})
        moteur = SearchEngine(loader)

        # L'utilisation de getattr() dans le moteur doit ignorer l'objet corrompu sans planter
        assert len(moteur.chercher_athlete_par_nom("Valide")) == 1

    # Tests de Logique de Recherche Principale

    def test_recherche_insensible_casse_et_partielle(self) -> None:
        """Vérifie que le moteur pardonne les majuscules et les mots incomplets."""
        a1 = Athlete(nom="Novak Djokovic", id_personne="1")
        loader = AnnuaireSimule({"1": a1})
        moteur = SearchEngine(loader)

        # La recherche doit trouver le joueur peu importe la façon de l'écrire
        assert len(moteur.chercher_athlete_par_nom("novak")) == 1  # Tout en minuscules
        assert len(moteur.chercher_athlete_par_nom("DJOKO")) == 1  # Tout en majuscules
        assert len(moteur.chercher_athlete_par_nom("vak djo")) == 1  # Morceau à cheval sur deux mots

        # Une mauvaise recherche ne doit rien renvoyer
        assert len(moteur.chercher_athlete_par_nom("Nadal")) == 0

    def test_recherche_filtre_strictement_par_type(self) -> None:
        """Vérifie qu'on ne mélange pas les équipes et les joueurs."""
        # On crée un joueur et une équipe qui contiennent tous les deux le mot "Paris"
        athlete = Athlete(nom="Parisot", id_personne="A1")
        equipe = Equipe(nom="Paris Saint Germain", id_equipe="E1")

        loader = AnnuaireSimule({"A1": athlete, "E1": equipe})
        moteur = SearchEngine(loader)

        # Si on cherche un athlète, on ne doit pas récupérer le PSG
        resultats_athletes = moteur.chercher_athlete_par_nom("Paris")
        assert len(resultats_athletes) == 1
        assert isinstance(resultats_athletes[0], Athlete)

        # Si on cherche une équipe, on ne doit pas récupérer le joueur Parisot
        resultats_equipes = moteur.chercher_equipe_par_nom("Paris")
        assert len(resultats_equipes) == 1
        assert isinstance(resultats_equipes[0], Equipe)

    # Tests de Tri et de Gestion des Données

    def test_tri_alphabetique_et_gestion_doublons(self) -> None:
        """Vérifie que l'utilisation d'un 'set' fonctionne pour éliminer les doublons et que la liste est triée."""
        # Zizou et Titi
        a1 = Athlete(nom="Zidane", id_personne="1")
        a2 = Athlete(nom="Henry", id_personne="2")

        # On simule un bug en mémoire : Zidane a été chargé deux fois sous deux clés différentes
        loader = AnnuaireSimule({"cle1": a1, "cle2": a1, "cle3": a2})
        moteur = SearchEngine(loader)

        # Une recherche avec un texte vide ("") va ramener absolument tout ce qu'il y a en mémoire
        resultats = moteur.chercher_athlete_par_nom("")

        # Le 'set' (ensemble) du SearchEngine doit avoir fusionné les deux "Zidane" identiques
        assert len(resultats) == 2

        # Le tri final doit forcer l'ordre alphabétique : H avant Z
        assert resultats[0].nom == "Henry"
        assert resultats[1].nom == "Zidane"
