import pytest

from src.Core.app_controller import AppController
from src.Model.athlete import Athlete
from src.Model.coach import Coach
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance


@pytest.fixture
def athlete_standard() -> Athlete:
    """Fournit un joueur complet pour valider les calculs mathématiques (âge, IMC)."""
    return Athlete(
        nom="Dupont", prenom="Jean", id_personne="P001", date_naissance="1990-05-15", taille=185.0, poids=80.0
    )


@pytest.fixture
def coach_standard() -> Coach:
    """Fournit un entraîneur avec une spécialité pour tester les effectifs."""
    return Coach(nom="Jackson", prenom="Phil", id_personne="C001", specialite="Tactique")


@pytest.fixture
def equipe_standard() -> Equipe:
    """Fournit une structure vide prête à recevoir des membres."""
    return Equipe(nom="Lakers", id_equipe="E01", provenance="USA")


@pytest.fixture
def match_standard() -> Match:
    """Fournit une rencontre avec une date valide pour tester l'identification du gagnant."""
    return Match(id_match="M01", date="2024-07-25")


@pytest.fixture
def performance_gagnante(athlete_standard: Athlete) -> Performance:
    """Utilise l'athlète standard pour créer une performance de victoire prête à l'emploi."""
    return Performance(
        participant=athlete_standard, role="Domicile", est_gagnant=True, est_nul=False, stats={"points": 25}
    )


@pytest.fixture
def competition_championnat() -> Competition:
    """Fournit une coquille de tournoi pour tester le moteur de classement sans charger de CSV."""
    return Competition(id_competition="C01", nom="Ligue 1", type_format="championnat")


@pytest.fixture
def liste_participants_statistiques() -> list:
    """Fournit un échantillon diversifié pour les tests démographiques et géographiques."""
    return [
        Athlete(nom="Vieux Champion", id_personne="A1", provenance="France", date_naissance="1980-01-01"),
        Athlete(nom="Jeune Challenger", id_personne="A2", provenance="Espagne", date_naissance="2005-01-01"),
        Athlete(nom="Novice", id_personne="A3", provenance="France", date_naissance="1995-01-01"),
        Equipe(nom="Equipe Ignoree", id_equipe="E1"),
    ]


@pytest.fixture
def competition_statistiques(liste_participants_statistiques: list) -> Competition:
    """Fournit un tournoi complet avec 3 matchs pour valider les calculs complexes (ex: winrate)."""
    comp = Competition(id_competition="C_STAT", nom="Tournoi Stats")

    a1 = liste_participants_statistiques[0]  # Vieux Champion (France)
    a2 = liste_participants_statistiques[1]  # Jeune Challenger (Espagne)

    for i in range(3):
        m = Match(id_match=f"M{i}")
        m.ajouter_performance("Dom", Performance(a1, "Dom", est_gagnant=True))
        m.ajouter_performance("Ext", Performance(a2, "Ext", est_gagnant=False))
        comp.ajouter_match(m)

    return comp


@pytest.fixture
def controller_prepare(competition_statistiques: Competition, liste_participants_statistiques: list) -> AppController:
    """Fournit un contrôleur complet, avec la compétition chargée et la mémoire remplie."""
    controller = AppController()
    controller.competition_actuelle = competition_statistiques

    # On simule le travail du DataLoader en remplissant l'annuaire mémoire
    # indispensable pour que la recherche et l'inscription fonctionnent.
    controller.loader._annuaire_participants = {}
    for p in liste_participants_statistiques:
        controller.loader._annuaire_participants[str(p.id).lower()] = p
        if isinstance(p, Equipe):
            controller.loader._annuaire_participants[str(p.nom).lower()] = p

    return controller
