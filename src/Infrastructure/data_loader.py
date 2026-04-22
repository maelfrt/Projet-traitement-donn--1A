import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.Infrastructure.gestionnaire_csv import GestionnaireCSV
from src.Model.athlete import Athlete
from src.Model.coach import Coach
from src.Model.competition import Competition
from src.Model.equipe import Equipe
from src.Model.match import Match
from src.Model.performance import Performance


class DataLoader:
    """
    Service chargé de l'ingestion des données CSV, de l'application des configurations JSON,
    et de l'instanciation du graphe d'objets métier.
    """

    def __init__(self, dossier_donnees: str = "donnees", dossier_configs: str = "configs") -> None:
        self.dossier_configs = Path(dossier_configs)
        self.gestionnaire_csv = GestionnaireCSV(dossier_donnees)

        # DataFrames de stockage temporaire
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()

    # =========================================================
    # ÉTAPE 1 : INITIALISATION DE LA COMPÉTITION
    # =========================================================
    def initialiser_competition(self, nom_fichier_json: str) -> Competition:
        """Point d'entrée : Lit la configuration et orchestre le chargement des données."""

        # Vide le cache des anciennes compétitions
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()

        chemin_json = self.dossier_configs / nom_fichier_json
        with open(chemin_json, "r", encoding="utf-8") as fichier:
            config_sport = json.load(fichier)

        # Chargement des entités de base
        if "athlete" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["athlete"], Athlete, "base_athletes")

        if "coach" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["coach"], Coach, "base_coaches")

        if "equipe" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["equipe"], Equipe, "base_equipes")

        # Instanciation de l'objet principal Competition
        competition_principale = Competition(
            id_competition=len(config_sport["sport"]),
            nom=config_sport["sport"],
            type_format=config_sport.get("type_format", "championnat"),
            poids_rounds=config_sport.get("poids_rounds"),
        )

        # Chargement et intégration des matchs
        if "match" in config_sport["fichiers"]:
            config_match = config_sport["fichiers"]["match"]

            # Si la clé de groupement est placée à la racine du JSON, on la transfère aux paramètres du match
            if "cle_groupement" in config_sport and "cle_groupement" not in config_match:
                config_match["cle_groupement"] = config_sport["cle_groupement"]

            self._charger_matchs(config_match, competition_principale)

            self._lier_athletes_aux_equipes()

        return competition_principale

    # =========================================================
    # CHARGEMENT DES ENTITÉS
    # =========================================================
    def _charger_entites(self, config_fichier: dict, classe_cible: Any, nom_base: str) -> None:
        """Instancie les objets métiers simples (Athlete, Coach, Equipe) à partir du CSV."""
        df_entites = self.gestionnaire_csv.charger_fichier(config_fichier["nom_fichier"])

        def mapper_et_instancier(ligne_csv):
            donnees_extraites = self._extraire_champs(ligne_csv, config_fichier["mapping"])
            return classe_cible(**donnees_extraites)

        df_entites["objet"] = df_entites.apply(mapper_et_instancier, axis=1)
        df_entites["id_technique"] = df_entites["objet"].apply(lambda obj: getattr(obj, "id", None))

        setattr(self, nom_base, df_entites)

    # =========================================================
    # GESTION DES MATCHS
    # =========================================================
    def _charger_matchs(self, config_match: dict, competition_parente: Competition) -> None:
        """Instancie les objets Match et les associe à la structure de la compétition."""
        df_matchs = self.gestionnaire_csv.charger_fichier(config_match["nom_fichier"])

        df_matchs["objet"] = None

        if not df_matchs.empty:
            df_matchs["objet"] = df_matchs.apply(self._instancier_match, axis=1, args=(config_match,))

        self.base_matchs = df_matchs

        cle_groupement = config_match.get("cle_groupement")

        for ligne in df_matchs.itertuples(index=False):
            # Avec itertuples, 'ligne' n'est plus un dictionnaire mais un objet avec des attributs.
            instance_match = getattr(ligne, "objet", None)

            if instance_match is None:
                continue

            if cle_groupement:
                valeur_grp = getattr(ligne, cle_groupement, None)

                if pd.isna(valeur_grp) or str(valeur_grp).strip().lower() in ["", "nan", "none"]:
                    nom_sous_comp = "Tableau Principal"
                else:
                    nom_sous_comp = str(valeur_grp).strip().removesuffix(".0")
                    if "section" in cle_groupement.lower():
                        nom_sous_comp = f"Section {nom_sous_comp}"

                sous_competition = competition_parente.obtenir_ou_creer_sous_comp(nom_sous_comp)
                sous_competition.ajouter_match(instance_match)
            else:
                competition_parente.ajouter_match(instance_match)

    def _instancier_match(self, ligne_csv: pd.Series, config_match: dict) -> Match:
        """Crée une instance de Match et y associe ses objets Performance."""

        infos_base = self._extraire_champs(ligne_csv, config_match["mapping_base"])
        if not infos_base.get("id_match"):
            infos_base["id_match"] = str(ligne_csv.get("index", ligne_csv.name))
        nouveau_match = Match(**infos_base)

        regle_victoire = config_match.get("regle_victoire", {})

        for role, config_role in config_match["performances"].items():
            id_participant = str(ligne_csv[config_role["colonne_participant"]])
            instance_participant = self._rechercher_participant(id_participant)

            if instance_participant:
                stats = self._extraire_champs(ligne_csv, config_role["stats"])

                est_gagnant = self._determiner_victoire(
                    ligne_csv, stats, role, config_role, regle_victoire, config_match
                )

                performance = Performance(instance_participant, role, est_gagnant, stats)
                nouveau_match.ajouter_performance(role, performance)

        return nouveau_match

    # =========================================================
    # LOGIQUE DES RÉSULTATS
    # =========================================================
    def _determiner_victoire(
        self,
        ligne_csv: pd.Series,
        stats: dict,
        role: str,
        config_role: dict,
        regle_victoire: dict,
        config_match_globale: dict,
    ) -> bool:
        """Évalue les statistiques ou données brutes pour déterminer le gagnant du match."""
        methode_evaluation = regle_victoire.get("methode")

        if methode_evaluation == "comparaison":
            stat_cible = regle_victoire["stat_cible"]

            # On récupère la liste des mots déclenchant une victoire automatique
            mots_victoire = regle_victoire.get("victoire_par_defaut", [])
            # On s'assure que tout est en minuscules pour la comparaison
            mots_victoire = [str(mot).strip().lower() for mot in mots_victoire]

            score_brut_actuel = str(stats.get(stat_cible, "0")).strip().lower()

            if score_brut_actuel in mots_victoire:
                return True

            # Sécurité anti-crash pour le joueur actuel
            try:
                score_actuel = float(score_brut_actuel)
            except ValueError:
                score_actuel = 0.0

            role_adversaire = next((r for r in config_match_globale["performances"] if r != role), None)

            # Récupération du score de l'adversaire
            score_adversaire = 0.0
            if role_adversaire:
                stats_adversaire = self._extraire_champs(
                    ligne_csv, config_match_globale["performances"][role_adversaire]["stats"]
                )
                score_brut_adv = str(stats_adversaire.get(stat_cible, "0")).strip().lower()

                # Si par hasard c'est l'adversaire qui a bénéficié de la victoire par défaut
                if score_brut_adv in mots_victoire:
                    return False

                try:
                    score_adversaire = float(score_brut_adv)
                except ValueError:
                    score_adversaire = 0.0

            # Détermination du gagnant aux points
            if regle_victoire.get("logique") == "plus_grand":
                return score_actuel > score_adversaire
            return score_actuel < score_adversaire

        if methode_evaluation == "directe":
            colonne_cible = regle_victoire.get("colonne_cible", "winner")

            valeur_csv = str(ligne_csv.get(colonne_cible, "")).strip().lower()
            valeur_attendue = str(config_role.get("valeur_victoire", "")).strip().lower()
            id_participant = str(ligne_csv.get(config_role.get("colonne_participant", ""))).strip().lower()

            if valeur_csv == valeur_attendue or valeur_csv == id_participant:
                return True

        return config_role.get("victoire_forcee") is True

    # =========================================================
    # UTILITAIRES
    # =========================================================
    def _extraire_champs(self, ligne_csv: pd.Series, mapping: dict) -> dict:
        """Extrait et mappe les colonnes du CSV selon la configuration JSON."""
        return {
            cle_objet: ligne_csv[col_csv]
            for cle_objet, col_csv in mapping.items()
            if col_csv in ligne_csv and pd.notna(ligne_csv[col_csv])
        }

    def _lier_athletes_aux_equipes(self) -> None:
        """Parcourt les athlètes pour les ajouter à la liste d'athlètes de leur équipe respective."""
        if self.base_athletes.empty or self.base_equipes.empty:
            return

        # On crée un annuaire pour trouver les équipes instantanément
        annuaire_equipes = {}
        for _, ligne_equipe in self.base_equipes.iterrows():
            equipe_obj = ligne_equipe["objet"]
            if equipe_obj:
                # On référence l'équipe par son ID (ex: "th") ET par son nom (ex: "team heretics")
                annuaire_equipes[str(equipe_obj.id).strip().lower()] = equipe_obj
                annuaire_equipes[str(equipe_obj.nom).strip().lower()] = equipe_obj

        # On affecte chaque athlète
        for _, ligne_athlete in self.base_athletes.iterrows():
            athlete_obj = ligne_athlete["objet"]
            nom_equipe_cible = str(getattr(athlete_obj, "equipe_actuelle", "")).strip().lower()

            if nom_equipe_cible and nom_equipe_cible not in ["nan", "none", ""]:
                equipe_obj = annuaire_equipes.get(nom_equipe_cible)

                if equipe_obj and hasattr(equipe_obj, "ajouter_membre"):
                    equipe_obj.ajouter_membre(athlete_obj)

    def _rechercher_participant(self, id_recherche: str) -> Any | None:
        """Recherche et retourne une instance de participant (Equipe ou Athlete) via son ID technique."""
        if pd.isna(id_recherche) or str(id_recherche).strip().lower() in ["nan", "none", ""]:
            return None

        id_recherche_formate = str(id_recherche).strip().lower()

        for base in [self.base_equipes, self.base_athletes]:
            if not base.empty and "id_technique" in base.columns:
                colonne_formatee = base["id_technique"].astype(str).str.strip().str.lower()

                masque_recherche = colonne_formatee == id_recherche_formate
                if masque_recherche.any():
                    return base.loc[masque_recherche, "objet"].values[0]

        return None
