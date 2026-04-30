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
    Service central d'ingestion et de structuration des données.

    Cette classe agit comme le traducteur principal de l'application. Elle
    lit des fichiers plats en s'appuyant sur les règles définies dans la
    configuration, puis transforme ces lignes de texte en véritables objets
    Python interconnectés au sein de la mémoire.

    Choix d'architecture :
    La bibliothèque Pandas est sollicitée exclusivement pour sa puissance
    lors de la fusion de tableaux. Dès que les données sont propres, elles
    sont instanciées en objets Python natifs pour garantir des temps de
    calcul et de recherche extrêmement rapides lors des analyses.
    """

    def __init__(self, dossier_donnees: str = "donnees", dossier_configs: str = "configs") -> None:
        self.dossier_configs = Path(dossier_configs)

        # Le gestionnaire CSV opère comme un sous-module dédié uniquement à la lecture
        self.gestionnaire_csv = GestionnaireCSV(dossier_donnees)

        # Les DataFrames Pandas servent de stockage intermédiaire pour faciliter
        # l'affichage de tableaux bruts si l'interface utilisateur le demande.
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()

        # Le cache mémoire stocke tous les objets créés. Cela permet de retrouver
        # un participant instantanément au lieu de reparcourir toute la base de données.
        self._annuaire_participants: dict[str, Any] = {}

    @staticmethod
    def _est_valeur_valide(valeur: Any) -> bool:
        """
        Filtre de sécurité pour nettoyer les données entrantes.

        Les fichiers CSV contiennent souvent des cases vides interprétées
        différemment selon les logiciels. Cette méthode garantit une
        homogénéisation de la vérification.

        Parameters
        ----------
        valeur : Any
            La donnée brute extraite du fichier source.

        Returns
        -------
        bool
            True si la donnée est exploitable, False s'il s'agit d'une case vide.
        """
        if valeur is None:
            return False
        return str(valeur).strip().lower() not in ["", "nan", "none", "aucun", "inconnu"]

    # =========================================================================
    # ORCHESTRATION GLOBALE
    # =========================================================================

    def initialiser_competition(self, nom_fichier_json: str) -> Competition:
        """
        Point d'entrée principal construisant le graphe d'objets en mémoire.

        Cette méthode orchestre l'initialisation complète. Elle commence par
        lire le fichier de configuration, puis procède à la création des acteurs
        sportifs. Ces acteurs sont ensuite indexés en mémoire pour être liés
        rapidement lors de la construction de l'historique des rencontres.

        Parameters
        ----------
        nom_fichier_json : str
            Le nom du fichier de configuration à charger en mémoire.

        Returns
        -------
        Competition
            L'objet racine contenant toute l'arborescence du tournoi.
        """
        self._reinitialiser_bases()

        chemin_json = self.dossier_configs / nom_fichier_json
        with open(chemin_json, "r", encoding="utf-8") as fichier:
            config_sport = json.load(fichier)

        # Création des participants individuels et collectifs
        mapping_participants = [
            ("athlete", "base_athletes", Athlete),
            ("coach", "base_coaches", Coach),
            ("equipe", "base_equipes", Equipe),
        ]

        for cle_json, attribut_base, classe_python in mapping_participants:
            if cle_json in config_sport["fichiers"]:
                self._charger_participants(config_sport["fichiers"][cle_json], classe_python, attribut_base)

        # Instanciation de l'objet principal du tournoi
        competition_principale = Competition(
            id_competition=len(config_sport["sport"]),
            nom=config_sport["sport"],
            type_format=config_sport.get("type_format", "championnat"),
            poids_rounds=config_sport.get("poids_rounds"),
        )

        # Optimisation mémoire cruciale avant d'aborder les rencontres
        self._indexer_participants_en_cache()
        self._lier_athletes_aux_equipes()

        # Chargement de l'historique des rencontres sportives
        if "match" in config_sport["fichiers"]:
            config_match = config_sport["fichiers"]["match"]

            if "cle_groupement" in config_sport and "cle_groupement" not in config_match:
                config_match["cle_groupement"] = config_sport["cle_groupement"]

            self._charger_matchs(config_match, competition_principale)

        return competition_principale

    def _reinitialiser_bases(self) -> None:
        """
        Vide les DataFrames et le cache mémoire.
        Cette sécurité évite de mélanger les participants de différents sports
        lorsque l'utilisateur bascule d'une configuration à l'autre.
        """
        self.base_athletes = pd.DataFrame()
        self.base_equipes = pd.DataFrame()
        self.base_coaches = pd.DataFrame()
        self.base_matchs = pd.DataFrame()
        self._annuaire_participants = {}

    def _fusionner_et_nettoyer_csv(self, config_fichier: dict) -> pd.DataFrame:
        """
        Utilise la puissance de Pandas pour assembler des fichiers.

        Certains sports stockent les rencontres dans un fichier principal et
        les métadonnées dans des fichiers annexes. Cette méthode réalise des
        jointures pour tout regrouper dans un seul tableau unifié.

        Parameters
        ----------
        config_fichier : dict
            Le bloc de configuration décrivant les jointures à effectuer.

        Returns
        -------
        pd.DataFrame
            Le tableau consolidé et expurgé de ses valeurs nulles.
        """
        df_principal = self.gestionnaire_csv.charger_fichier(config_fichier["nom_fichier"])

        if "jointures" in config_fichier:
            for jointure in config_fichier["jointures"]:
                df_joint = self.gestionnaire_csv.charger_fichier(jointure["fichier"])
                if "renommer" in jointure:
                    df_joint = df_joint.rename(columns=jointure["renommer"])

                df_principal = pd.merge(
                    df_principal, df_joint, how="left", left_on=jointure["cle_source"], right_on=jointure["cle_cible"]
                )

        # Le remplacement des balises Pandas par des valeurs nulles natives
        # Python garantit une instanciation propre des objets par la suite.
        return df_principal.where(pd.notnull(df_principal), None)

    # =========================================================================
    # TRADUCTION DES LIGNES EN OBJETS
    # =========================================================================

    def _charger_participants(self, config_fichier: dict, classe_cible: Any, nom_base: str) -> None:
        """
        Transforme les lignes d'un tableau Pandas en instances de notre modèle.

        Parameters
        ----------
        config_fichier : dict
            Le bloc de configuration contenant les règles d'attribution des colonnes.
        classe_cible : Any
            La classe Python à instancier.
        nom_base : str
            Le nom de l'attribut interne où stocker le DataFrame final.
        """
        df_participants = self._fusionner_et_nettoyer_csv(config_fichier)

        if df_participants.empty:
            return

        # L'utilisation d'une compréhension de liste couplée à un déballage
        # de dictionnaire permet une création d'objets extrêmement véloce.
        objets_crees = [
            classe_cible(**self._filtrer_via_mapping_json(ligne, config_fichier["mapping"]))
            for ligne in df_participants.to_dict("records")
        ]

        df_final = pd.DataFrame({"objet": objets_crees})
        df_final["id_technique"] = [obj.id for obj in objets_crees]

        setattr(self, nom_base, df_final)

    # =========================================================================
    # CONSTRUCTION DES MATCHS ET RÈGLES DE VICTOIRE
    # =========================================================================

    def _charger_matchs(self, config_match: dict, competition_parente: Competition) -> None:
        """
        Instancie les matchs et les classe dans la structure du tournoi.

        Parameters
        ----------
        config_match : dict
            Les règles d'extraction définies pour le sport concerné.
        competition_parente : Competition
            Le tournoi racine accueillant ces rencontres.
        """
        df_matchs = self._fusionner_et_nettoyer_csv(config_match)

        if df_matchs.empty:
            return

        cle_groupement = config_match.get("cle_groupement")

        for i, ligne in enumerate(df_matchs.to_dict("records")):
            nouveau_match = self._instancier_match(ligne, config_match, index_ligne=i)

            # Rangement logique basé sur l'existence d'une sous-division
            if cle_groupement and self._est_valeur_valide(ligne.get(cle_groupement)):
                nom_sous_comp = str(ligne[cle_groupement]).strip().removesuffix(".0")
                if "section" in cle_groupement.lower():
                    nom_sous_comp = f"Section {nom_sous_comp}"

                sous_competition = competition_parente.obtenir_ou_creer_sous_comp(nom_sous_comp)
                sous_competition.ajouter_match(nouveau_match)
            else:
                competition_parente.ajouter_match(nouveau_match)

        self.base_matchs = df_matchs

    def _instancier_match(self, ligne_dict: dict, config_match: dict, index_ligne: int) -> Match:
        """
        Décode une ligne du tableau pour générer un objet Match complet.

        Parameters
        ----------
        ligne_dict : dict
            Une ligne de données transformée en dictionnaire.
        config_match : dict
            Les directives d'extraction issues de la configuration.
        index_ligne : int
            Valeur de secours pour générer un identifiant unique si nécessaire.

        Returns
        -------
        Match
            L'objet Match enrichi de ses performances et athlètes associés.
        """
        infos_base = self._filtrer_via_mapping_json(ligne_dict, config_match["mapping_base"])

        if not infos_base.get("id_match"):
            infos_base["id_match"] = f"M-{index_ligne:04d}"

        nouveau_match = Match(**infos_base)
        regle_victoire = config_match.get("regle_victoire", {})

        # Itération sur chaque rôle impliqué dans la rencontre
        for role, config_role in config_match["performances"].items():
            id_participant = str(ligne_dict.get(config_role.get("colonne_participant", "")))
            instance_participant = self._rechercher_participant(id_participant)

            if instance_participant:
                stats = self._filtrer_via_mapping_json(ligne_dict, config_role.get("stats", {}))

                est_gagnant = self._determiner_victoire(
                    ligne_dict, stats, role, config_role, regle_victoire, config_match
                )

                performance = Performance(instance_participant, role, est_gagnant, stats)

                # Rattachement spécifique des joueurs lors de sports collectifs
                for col_joueur in config_role.get("colonnes_joueurs", []):
                    val_joueur = ligne_dict.get(col_joueur)
                    if self._est_valeur_valide(val_joueur):
                        id_joueur = str(val_joueur).strip().removesuffix(".0")
                        joueur_trouve = self._rechercher_participant(id_joueur)
                        if joueur_trouve:
                            performance.joueurs_match.append(joueur_trouve)

                nouveau_match.ajouter_performance(role, performance)

        return nouveau_match

    def _determiner_victoire(
        self,
        ligne_dict: dict,
        stats: dict,
        role_actuel: str,
        config_role: dict,
        regle_victoire: dict,
        config_match_globale: dict,
    ) -> bool:
        """
        Moteur de règles arbitrant le résultat d'une rencontre.

        La méthode s'adapte dynamiquement à la nature du sport. Dans un format
        direct, une colonne précise indique le nom du vainqueur. Dans un format
        basé sur la comparaison, le système confronte purement mathématiquement
        les scores obtenus par les adversaires.

        Returns
        -------
        bool
            True si la performance analysée correspond au vainqueur du match.
        """
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

            # Application automatique de la victoire en cas de forfait adverse
            if score_brut_actuel in mots_victoire:
                return True

            # Recherche dynamique du score de l'adversaire direct
            roles_disponibles = list(config_match_globale["performances"].keys())
            role_adv = roles_disponibles[1] if roles_disponibles[0] == role_actuel else roles_disponibles[0]

            stats_adv = self._filtrer_via_mapping_json(
                ligne_dict, config_match_globale["performances"][role_adv]["stats"]
            )
            score_brut_adv = str(stats_adv.get(stat_cible, "0")).strip().lower()

            if score_brut_adv in mots_victoire:
                return False

            score_actuel = self._convertir_en_nombre(score_brut_actuel)
            score_adversaire = self._convertir_en_nombre(score_brut_adv)

            return (
                score_actuel > score_adversaire
                if regle_victoire.get("logique") == "plus_grand"
                else score_actuel < score_adversaire
            )

        return config_role.get("victoire_forcee") is True

    # =========================================================================
    # OUTILS ET OPTIMISATIONS MÉMOIRE
    # =========================================================================

    def _convertir_en_nombre(self, valeur: Any) -> float:
        """Nettoie et convertit les statistiques en nombres flottants de manière sécurisée."""
        if not self._est_valeur_valide(valeur):
            return 0.0
        try:
            return float(str(valeur).strip().lower())
        except ValueError:
            return 0.0

    def _filtrer_via_mapping_json(self, ligne_dict: dict, mapping: dict) -> dict:
        """
        Extrait sélectivement les données en suivant le dictionnaire de traduction.
        """
        return {
            cle_objet: ligne_dict[col_csv]
            for cle_objet, col_csv in mapping.items()
            if self._est_valeur_valide(ligne_dict.get(col_csv))
        }

    def _lier_athletes_aux_equipes(self) -> None:
        """
        Associe les instances des joueurs à leur formation respective en mémoire.
        Cette étape facilite grandement les calculs d'effectif ultérieurs.
        """
        for participant in self._annuaire_participants.values():
            if isinstance(participant, Athlete):
                nom_equipe = str(getattr(participant, "equipe_actuelle", "")).strip().lower()

                if self._est_valeur_valide(nom_equipe):
                    equipe_obj = self._annuaire_participants.get(nom_equipe)
                    if isinstance(equipe_obj, Equipe):
                        equipe_obj.ajouter_membre(participant)

    def _indexer_participants_en_cache(self) -> None:
        """
        Structure l'annuaire mémoire pour garantir un temps d'accès immédiat.
        Chaque participant est répertoriée par son identifiant unique, complété
        par une indexation secondaire sur le nom pour les équipes sportives.
        """
        self._annuaire_participants = {}
        for base in [self.base_equipes, self.base_athletes]:
            if base.empty or "objet" not in base.columns:
                continue

            for obj in base["objet"]:
                self._annuaire_participants[str(obj.id).strip().lower()] = obj

                if isinstance(obj, Equipe):
                    self._annuaire_participants[str(obj.nom).strip().lower()] = obj

    def _rechercher_participant(self, id_recherche: str) -> Any | None:
        """Sonde l'annuaire mémoire pour restituer l'instance demandée."""
        if not self._est_valeur_valide(id_recherche):
            return None
        return self._annuaire_participants.get(str(id_recherche).strip().lower())

    def ajouter_participant_en_memoire(self, objet: Any, type_participant: str) -> None:
        """
        Intègre un nouvel acteur au sein des bases de données
        et de l'annuaire mémoire suite à une saisie utilisateur.
        """
        nouvelle_ligne = pd.DataFrame([{"id_technique": objet.id, "objet": objet}])

        if type_participant == "athlete":
            self.base_athletes = pd.concat([self.base_athletes, nouvelle_ligne], ignore_index=True)
        elif type_participant == "equipe":
            self.base_equipes = pd.concat([self.base_equipes, nouvelle_ligne], ignore_index=True)
            self._annuaire_participants[str(objet.nom).strip().lower()] = objet

        self._annuaire_participants[str(objet.id).strip().lower()] = objet
