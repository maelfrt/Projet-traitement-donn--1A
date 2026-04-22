from src.Analysis.ranking_engine import RankingEngine
from src.Analysis.search_engine import SearchEngine
from src.Infrastructure.data_loader import DataLoader
from src.Model.competition import Competition


class AppController:
    """
    Organise chacun des différents modules
    """

    def __init__(self) -> None:
        self.loader: DataLoader = DataLoader()
        self.ranker: RankingEngine = RankingEngine()
        self.searcher: SearchEngine = SearchEngine(self.loader)

        # Stockage de la compétition actuelle
        self.competition_actuelle: Competition | None = None

    def executer_chargement_complet(self, config_json: str) -> None:
        """Pilote la séquence : Charger -> Calculer les classements."""
        print(f"\n--- Initialisation du sport : {config_json} ---")

        self.competition_actuelle = self.loader.initialiser_competition(config_json)

        if self.competition_actuelle:
            self.ranker.generer_classement(self.competition_actuelle)
            print(f"Succès : {self.competition_actuelle.nom} est prêt.")

    def obtenir_resultats(self) -> Competition | None:
        """Retourne la compétition traitée pour l'affichage."""
        return self.competition_actuelle

    def rechercher_joueur(self, nom: str) -> list:
        """Utilise le moteur de recherche interne."""
        return self.searcher.chercher_athlete_par_nom(nom)
