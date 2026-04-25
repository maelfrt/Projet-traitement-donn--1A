import time as time_module

import pandas as pd

from src.Analysis.ranking_engine import RankingEngine
from src.Analysis.search_engine import SearchEngine
from src.Infrastructure.data_loader import DataLoader
from src.Model.athlete import Athlete
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.participant import Participant
from src.Model.performance import Performance


class AppController:
    """
    Façade centrale de l'application.
    Orchestre les modules (Data, Search, Ranking) et gère la logique métier.
    """

    def __init__(self) -> None:
        self.loader: DataLoader = DataLoader()
        self.ranker: RankingEngine = RankingEngine()
        self.searcher: SearchEngine = SearchEngine(self.loader)

        # Stockage de la compétition actuelle
        self.competition_actuelle: Competition | None = None

    # =========================================================
    # INITIALISATION ET ACCÈS
    # =========================================================

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

    # =========================================================
    # RECHERCHE (Délégation au SearchEngine)
    # =========================================================

    def rechercher_joueur(self, nom: str) -> list:
        """Recherche des athlètes par nom partiel."""
        return self.searcher.chercher_athlete_par_nom(nom)

    def rechercher_equipe(self, nom: str) -> list:
        """Recherche des équipes par nom partiel."""
        return self.searcher.chercher_equipe_par_nom(nom)

    # =========================================================
    # GESTION DES PARTICIPANTS
    # =========================================================

    def inscrire_participant(
        self, type_participant: str, nom: str, provenance: str | None = None, equipe_actuelle: str | None = None
    ) -> Participant | None:
        """
        Inscrit un nouvel athlète ou une nouvelle équipe dans le système.
        Gère la création d'ID, l'instanciation et la mise à jour des bases de données.
        """
        prefixe = "P" if type_participant == "1" else "E"
        nouveau_id = f"{prefixe}-{int(time_module.time())}"

        nouvel_objet: Participant | None = None

        if type_participant == "1":
            nouvel_objet = Athlete(
                nom=nom, id_personne=nouveau_id, provenance=provenance, equipe_actuelle=equipe_actuelle
            )
            self.loader.ajouter_entite_en_memoire(nouvel_objet, "athlete")

        elif type_participant == "2":
            nouvel_objet = Equipe(nom=nom, id_equipe=nouveau_id, provenance=provenance)
            self.loader.ajouter_entite_en_memoire(nouvel_objet, "equipe")

        if nouvel_objet and hasattr(self.loader, "_annuaire_participants"):
            cle_annuaire = str(nouveau_id).strip().lower()
            self.loader._annuaire_participants[cle_annuaire] = nouvel_objet

            if isinstance(nouvel_objet, Equipe):
                self.loader._annuaire_participants[str(nouvel_objet.nom).strip().lower()] = nouvel_objet

        return nouvel_objet

    def obtenir_tous_les_participants(self) -> list:
        """Retourne la liste complète de tous les objets participants."""
        if hasattr(self.loader, "_annuaire_participants"):
            return list(set(self.loader._annuaire_participants.values()))
        return []

    # =========================================================
    # GESTION DES MATCHS
    # =========================================================

    def enregistrer_nouveau_match(
        self, date_match: str, liste_donnees_perf: list[dict], nom_sous_comp: str | None = None
    ) -> str:
        """
        Crée un match complet, l'ajoute au tournoi et met à jour les classements.
        """
        if not self.competition_actuelle:
            raise ValueError("Aucune compétition n'est chargée.")

        id_nouveau = f"M-{int(time_module.time())}"
        nouveau_match = Match(id_match=id_nouveau, date=date_match)

        for data in liste_donnees_perf:
            perf = Performance(
                participant=data["participant"], role=data["role"], est_gagnant=data["est_gagnant"], stats=data["stats"]
            )
            nouveau_match.ajouter_performance(data["role"], perf)

        tournoi_cible = self.competition_actuelle
        if nom_sous_comp:
            tournoi_cible = self.competition_actuelle.obtenir_ou_creer_sous_comp(nom_sous_comp)

        tournoi_cible.ajouter_match(nouveau_match)
        self.ranker.generer_classement(self.competition_actuelle)

        return id_nouveau

    def obtenir_match_par_id(self, id_match: str) -> Match | None:
        """Cherche et renvoie un match spécifique dans l'arborescence."""
        match, _ = self._trouver_match_et_parent(id_match)
        return match

    def supprimer_match(self, id_match: str) -> bool:
        """Supprime un match et recalcule les classements."""
        match, parent = self._trouver_match_et_parent(id_match)
        if match and parent:
            parent.liste_match.remove(match)
            if self.competition_actuelle:
                self.ranker.generer_classement(self.competition_actuelle)
            return True
        return False

    def modifier_match(self, id_match: str, nouvelle_date: str, liste_donnees_perf: list[dict]) -> bool:
        """Met à jour les données d'un match existant."""
        match, _ = self._trouver_match_et_parent(id_match)
        if not match:
            return False

        match.date = nouvelle_date
        for data in liste_donnees_perf:
            perf = Performance(
                participant=data["participant"], role=data["role"], est_gagnant=data["est_gagnant"], stats=data["stats"]
            )
            match.performances[data["role"]] = perf

        if self.competition_actuelle:
            self.ranker.generer_classement(self.competition_actuelle)
        return True

    def _trouver_match_et_parent(self, id_match: str) -> tuple[Match | None, Competition | None]:
        """Parcourt récursivement pour trouver un match et son conteneur."""
        if not self.competition_actuelle:
            return None, None

        for m in self.competition_actuelle.liste_match:
            if str(m.id_match) == id_match:
                return m, self.competition_actuelle

        # Recherche sous-tournois
        for sous_comp in self.competition_actuelle.sous_competitions.values():
            for m in sous_comp.liste_match:
                if str(m.id_match) == id_match:
                    return m, sous_comp
        return None, None

    # =========================================================
    # INFRASTRUCTURE / SAUVEGARDE
    # =========================================================

    def sauvegarder_matchs(self, nom_fichier: str = "matchs_sauvegarde.csv") -> tuple[bool, int, str]:
        """
        Extrait l'historique complet et l'exporte en CSV via le DataLoader.
        """
        if not self.competition_actuelle:
            return False, 0, "Aucune compétition chargée."

        def extraire_tous_les_matchs(comp):
            matchs = list(comp.liste_match)
            for sc in comp.sous_competitions.values():
                matchs.extend(extraire_tous_les_matchs(sc))
            return matchs

        liste_totale = extraire_tous_les_matchs(self.competition_actuelle)
        if not liste_totale:
            return False, 0, "Aucun match enregistré."

        donnees = [m.to_dict() for m in liste_totale]
        df_export = pd.DataFrame(donnees)

        try:
            self.loader.gestionnaire_csv.sauvegarder_fichier(df=df_export, nom_fichier=nom_fichier)
            return True, len(donnees), nom_fichier
        except OSError as e:
            return False, 0, str(e)
