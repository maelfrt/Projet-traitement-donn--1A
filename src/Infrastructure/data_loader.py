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
    et de l'instanciation du graphe d'objets métier. (Version Haute Performance)
    """

    def __init__(self, dossier_donnees: str = "donnees", dossier_configs: str = "configs") -> None:
        self.dossier_configs = Path(dossier_configs)
        self.gestionnaire_csv = GestionnaireCSV(dossier_donnees)

        # DataFrames de stockage
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()

    # =========================================================
    # ÉTAPE 1 : INITIALISATION DE LA COMPÉTITION
    # =========================================================
    def initialiser_competition(self, nom_fichier_json: str) -> Competition:
        """Point d'entrée : Lit la configuration et orchestre le chargement des données."""
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()

        chemin_json = self.dossier_configs / nom_fichier_json
        with open(chemin_json, "r", encoding="utf-8") as fichier:
            config_sport = json.load(fichier)

        if "athlete" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["athlete"], Athlete, "base_athletes")

        if "coach" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["coach"], Coach, "base_coaches")

        if "equipe" in config_sport["fichiers"]:
            self._charger_entites(config_sport["fichiers"]["equipe"], Equipe, "base_equipes")

        competition_principale = Competition(
            id_competition=len(config_sport["sport"]),
            nom=config_sport["sport"],
            type_format=config_sport.get("type_format", "championnat"),
            poids_rounds=config_sport.get("poids_rounds"),
        )

        # Création de l'annuaire O(1) AVANT les matchs
        self._construire_annuaire()

        # Lien rapide Athlètes -> Équipes
        self._lier_athletes_aux_equipes()

        if "match" in config_sport["fichiers"]:
            config_match = config_sport["fichiers"]["match"]
            if "cle_groupement" in config_sport and "cle_groupement" not in config_match:
                config_match["cle_groupement"] = config_sport["cle_groupement"]

            self._charger_matchs(config_match, competition_principale)

        return competition_principale

    def _charger_donnees_brutes(self, config_fichier: dict) -> pd.DataFrame:
        """Charge un CSV principal et effectue les jointures si spécifiées."""
        df_principal = self.gestionnaire_csv.charger_fichier(config_fichier["nom_fichier"])

        if "jointures" in config_fichier:
            for jointure in config_fichier["jointures"]:
                df_joint = self.gestionnaire_csv.charger_fichier(jointure["fichier"])
                if "renommer" in jointure:
                    df_joint = df_joint.rename(columns=jointure["renommer"])
                df_principal = pd.merge(
                    df_principal, df_joint, how="left", left_on=jointure["cle_source"], right_on=jointure["cle_cible"]
                )

        return df_principal

    # =========================================================
    # CHARGEMENT DES ENTITÉS
    # =========================================================
    def _charger_entites(self, config_fichier: dict, classe_cible: Any, nom_base: str) -> None:
        """Instancie les objets simples (Athlete, Coach, Equipe)."""
        df_entites = self._charger_donnees_brutes(config_fichier)

        if df_entites.empty:
            return

        # Remplacement des NaN par None pour une lecture pure Python
        df_entites = df_entites.where(pd.notnull(df_entites), None)
        lignes_dict = df_entites.to_dict("records")

        objets_crees = []
        for ligne in lignes_dict:
            donnees_extraites = self._extraire_champs(ligne, config_fichier["mapping"])
            objets_crees.append(classe_cible(**donnees_extraites))

        # On recrée un DataFrame léger juste pour stocker les objets (pour la recherche)
        df_final = pd.DataFrame({"objet": objets_crees})
        df_final["id_technique"] = df_final["objet"].apply(lambda obj: getattr(obj, "id", None))

        setattr(self, nom_base, df_final)

    # =========================================================
    # GESTION DES MATCHS
    # =========================================================
    def _charger_matchs(self, config_match: dict, competition_parente: Competition) -> None:
        """Instancie les objets Match et les associe en un seul passage."""
        df_matchs = self._charger_donnees_brutes(config_match)

        if df_matchs.empty:
            return

        # 1. Nettoyage Pandas ultra-rapide des NaN
        df_matchs = df_matchs.where(pd.notnull(df_matchs), None)

        # 2. Conversion en dictionnaires (Supprime le goulot d'étranglement de Pandas)
        lignes_dict = df_matchs.to_dict("records")
        cle_groupement = config_match.get("cle_groupement")

        # 3. Boucle unique
        for i, ligne in enumerate(lignes_dict):
            instance_match = self._instancier_match(ligne, config_match, index_ligne=i)

            if cle_groupement:
                valeur_grp = ligne.get(cle_groupement)

                if valeur_grp is None or str(valeur_grp).strip().lower() in ["", "nan", "none"]:
                    nom_sous_comp = "Tableau Principal"
                else:
                    nom_sous_comp = str(valeur_grp).strip().removesuffix(".0")
                    if "section" in cle_groupement.lower():
                        nom_sous_comp = f"Section {nom_sous_comp}"

                sous_competition = competition_parente.obtenir_ou_creer_sous_comp(nom_sous_comp)
                sous_competition.ajouter_match(instance_match)
            else:
                competition_parente.ajouter_match(instance_match)

        self.base_matchs = df_matchs

    def _instancier_match(self, ligne_dict: dict, config_match: dict, index_ligne: int) -> Match:
        """Crée une instance de Match depuis un dictionnaire natif Python."""
        infos_base = self._extraire_champs(ligne_dict, config_match["mapping_base"])

        if not infos_base.get("id_match"):
            infos_base["id_match"] = f"M-{index_ligne:04d}"

        nouveau_match = Match(**infos_base)
        regle_victoire = config_match.get("regle_victoire", {})

        for role, config_role in config_match["performances"].items():
            id_participant = str(ligne_dict.get(config_role.get("colonne_participant", "")))
            instance_participant = self._rechercher_participant(id_participant)

            if instance_participant:
                stats = self._extraire_champs(ligne_dict, config_role.get("stats", {}))
                est_gagnant = self._determiner_victoire(
                    ligne_dict, stats, role, config_role, regle_victoire, config_match
                )

                performance = Performance(instance_participant, role, est_gagnant, stats)

                if "colonnes_joueurs" in config_role:
                    for col_joueur in config_role["colonnes_joueurs"]:
                        val_joueur = ligne_dict.get(col_joueur)
                        if val_joueur is not None and str(val_joueur).strip() not in ["", "nan", "None"]:
                            id_joueur = str(val_joueur).strip().removesuffix(".0")
                            instance_joueur = self._rechercher_participant(id_joueur)
                            if instance_joueur:
                                performance.joueurs_match.append(instance_joueur)

                nouveau_match.ajouter_performance(role, performance)

        return nouveau_match

    # =========================================================
    # LOGIQUE DES RÉSULTATS
    # =========================================================

    def _determiner_victoire(
        self,
        ligne_dict: dict,
        stats: dict,
        role: str,
        config_role: dict,
        regle_victoire: dict,
        config_match_globale: dict,
    ) -> bool:
        """Évalue la victoire entre deux participants"""
        methode = regle_victoire.get("methode")

        if methode == "directe":
            colonne_cible = regle_victoire.get("colonne_cible", "winner")
            valeur_csv = str(ligne_dict.get(colonne_cible, "")).strip().lower()
            valeur_attendue = str(config_role.get("valeur_victoire", "")).strip().lower()
            id_participant = str(ligne_dict.get(config_role.get("colonne_participant", ""))).strip().lower()

            return valeur_csv in [valeur_attendue, id_participant]

        if methode == "comparaison":
            stat_cible = regle_victoire["stat_cible"]
            mots_victoire = [str(mot).strip().lower() for mot in regle_victoire.get("victoire_par_defaut", [])]

            score_brut_actuel = str(stats.get(stat_cible, "0")).strip().lower()
            if score_brut_actuel in mots_victoire:
                return True

            score_actuel = self._convertir_en_nombre(score_brut_actuel)
            score_adversaire = 0.0

            # Trouver le score de l'adversaire
            role_adv = next((r for r in config_match_globale["performances"] if r != role), None)
            if role_adv:
                stats_adv = self._extraire_champs(ligne_dict, config_match_globale["performances"][role_adv]["stats"])
                score_brut_adv = str(stats_adv.get(stat_cible, "0")).strip().lower()
                if score_brut_adv in mots_victoire:
                    return False  # Si l'adversaire a "forfait", on a déjà gagné plus haut. S'il a "w.o", il gagne.
                score_adversaire = self._convertir_en_nombre(score_brut_adv)

            return (
                score_actuel > score_adversaire
                if regle_victoire.get("logique") == "plus_grand"
                else score_actuel < score_adversaire
            )

        # Cas par défaut (ex: le JSON dit "victoire_forcee": true pour le rôle "Vainqueur")
        return config_role.get("victoire_forcee") is True

    # =========================================================
    # UTILITAIRES
    # =========================================================
    def _convertir_en_nombre(self, valeur: Any) -> float:
        """Nettoie les try/except du code principal."""
        val_propre = str(valeur).strip().lower()
        if val_propre in ["nan", "none", ""]:
            return 0.0
        try:
            return float(val_propre)
        except ValueError:
            return 0.0

    def _extraire_champs(self, ligne_dict: dict, mapping: dict) -> dict:
        """Extrait les champs depuis un dictionnaire (O(1)) et évite les vérifications lourdes."""
        resultat = {}
        for cle_objet, col_csv in mapping.items():
            valeur = ligne_dict.get(col_csv)
            if valeur is not None and str(valeur).strip() not in ["", "nan", "None"]:
                resultat[cle_objet] = valeur
        return resultat

    def _lier_athletes_aux_equipes(self) -> None:
        """Associe les athlètes à leurs équipes (Orienté Objet classique)."""
        if not hasattr(self, "_annuaire_participants"):
            return

        for participant in self._annuaire_participants.values():
            if isinstance(participant, Athlete):
                nom_equipe_cible = str(getattr(participant, "equipe_actuelle", "")).strip().lower()

                if nom_equipe_cible and nom_equipe_cible not in ["nan", "none", ""]:
                    equipe_obj = self._annuaire_participants.get(nom_equipe_cible)

                    if isinstance(equipe_obj, Equipe):
                        equipe_obj.ajouter_membre(participant)

    def _construire_annuaire(self) -> None:
        """Construit un dictionnaire (Hash Map) ultra-rapide pour trouver les participants."""
        self._annuaire_participants = {}
        for base in [self.base_equipes, self.base_athletes]:
            if not base.empty and "id_technique" in base.columns and "objet" in base.columns:
                for id_tech, obj in zip(base["id_technique"], base["objet"]):
                    if pd.notna(id_tech):
                        cle = str(id_tech).strip().lower()
                        self._annuaire_participants[cle] = obj
                        # On indexe aussi par nom d'équipe pour le rattachement
                        if isinstance(obj, Equipe):
                            self._annuaire_participants[str(obj.nom).strip().lower()] = obj

    def _rechercher_participant(self, id_recherche: str) -> Any | None:
        """Recherche instantanée (O(1)) dans le dictionnaire."""
        if not id_recherche or str(id_recherche).strip().lower() in ["nan", "none", ""]:
            return None

        id_recherche_formate = str(id_recherche).strip().lower()
        return self._annuaire_participants.get(id_recherche_formate)

    def ajouter_entite_en_memoire(self, objet: Any, type_entite: str) -> None:
        """Ajoute proprement un objet (Athlete/Equipe) dans les DataFrames et l'annuaire."""
        import pandas as pd

        nouvelle_ligne = pd.DataFrame([{"id_technique": objet.id, "objet": objet}])

        if type_entite == "athlete":
            self.base_athletes = pd.concat([self.base_athletes, nouvelle_ligne], ignore_index=True)
        elif type_entite == "equipe":
            self.base_equipes = pd.concat([self.base_equipes, nouvelle_ligne], ignore_index=True)
            self._annuaire_participants[str(objet.nom).strip().lower()] = objet

        self._annuaire_participants[str(objet.id).strip().lower()] = objet
