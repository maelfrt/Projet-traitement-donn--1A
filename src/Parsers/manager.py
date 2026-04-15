import json
from pathlib import Path

import pandas as pd

from Model.athlete import Athlete
from Model.competition import Competition
from Model.match import Match
from Model.performance import Performance
from Parsers.gestionnaire_csv import GestionnaireCSV


class Manager:
    def __init__(self, dossier_donnees: str = "donnees", dossier_configs: str = "configs") -> None:
        self.dossier_configs = Path(dossier_configs)
        self.gestionnaire_csv = GestionnaireCSV(dossier_donnees)
        self.athletes_globaux: dict[str, Athlete] = {}
        self.competitions: dict[str, Competition] = {}

    def _mapper_donnees(self, ligne_csv: dict, mapping: dict) -> dict:
        """Traduit une ligne CSV en dictionnaire Python (Clé: Valeur_CSV)."""
        res = {}
        for cle, col_csv in mapping.items():
            val = ligne_csv.get(col_csv)
            if pd.notna(val):
                res[cle] = val
        return res

    def charger_sport(self, nom_fichier_json: str) -> Competition:
        chemin = self.dossier_configs / nom_fichier_json
        with open(chemin, "r", encoding="utf-8") as f:
            config = json.load(f)

        nom_sport = config["sport"]
        comp = Competition(id_competition=len(self.competitions) + 1, nom=nom_sport)

        # Chargement des athlètes (ou coachs)
        if "athlete" in config["fichiers"]:
            conf_ath = config["fichiers"]["athlete"]
            df = self.gestionnaire_csv.charger_fichier(conf_ath["nom_fichier"])
            for ligne in df.to_dict("records"):
                infos = self._mapper_donnees(ligne, conf_ath["mapping"])
                ath = Athlete(**infos)
                self.athletes_globaux[str(ath.id_personne)] = ath

        # Chargement des matchs
        if "match" in config["fichiers"]:
            conf_match = config["fichiers"]["match"]
            df = self.gestionnaire_csv.charger_fichier(conf_match["nom_fichier"])
            for ligne in df.to_dict("records"):

                # Création du match
                infos_m = self._mapper_donnees(ligne, conf_match["mapping_base"])
                m = Match(**infos_m)

                # Création des performances
                perfs_match = []
                for role, conf_p in conf_match["performances"].items():
                    id_part = str(ligne.get(conf_p["colonne_participant"]))
                    stats = self._mapper_donnees(ligne, conf_p["stats"])

                    # Victoire forcée (Tennis/LoL) ou par défaut
                    est_gagnant = conf_p.get("victoire_forcee", False)

                    # Victoire par valeur (ex: winner == "Blue")
                    if "valeur_victoire" in conf_p:
                        if str(ligne.get("winner")) == str(conf_p["valeur_victoire"]):
                            est_gagnant = True

                    p = Performance(id_participant=id_part, role=role, stats=stats, est_gagnant=est_gagnant)
                    m.ajouter_performance(role, p)
                    perfs_match.append(p)

                # Victoire calculée (Foot/Volley - si aucun vainqueur n'est encore défini)
                self._appliquer_logique_score(m, perfs_match, conf_match)
                comp.ajouter_match(m)

        self.competitions[nom_sport] = comp
        return comp

    def _appliquer_logique_score(self, match: Match, perfs: list[Performance], conf: dict):
        """Détermine le vainqueur par comparaison de score si la règle existe."""
        regle = conf.get("regle_victoire")
        if not regle or any(p.est_gagnant for p in perfs) or len(perfs) < 2:
            return

        s1 = float(perfs[0].stats.get(regle["stat_cible"], 0))
        s2 = float(perfs[1].stats.get(regle["stat_cible"], 0))

        # Exemple de cas pour les scores de matchs et le temps d'une course
        if regle["logique"] == "plus_grand":
            if s1 > s2:
                perfs[0].est_gagnant = True
            elif s2 > s1:
                perfs[1].est_gagnant = True
        elif regle["logique"] == "plus_petit":
            if s1 < s2:
                perfs[0].est_gagnant = True
            elif s2 < s1:
                perfs[1].est_gagnant = True

    def afficher_resultats(self, competition: Competition) -> None:
        print(f"\n{'=' * 80}")
        print(f"RÉSULTATS : {competition.nom.upper()}")
        print(f"{'=' * 80}")

        # On parcourt les matchs de la compétition
        for m in competition.liste_match:
            print(f"\n {m.date} | {m.lieu}")
            print(f"{'-' * 80}")

            # On affiche les performances (les participants et leurs scores)
            for role, perf in m.performances.items():
                # On essaie de récupérer le nom de l'athlète via le manager
                ath = self.athletes_globaux.get(perf.id_participant)
                nom_affiche = f"{ath.nom}" if ath else f"ID: {perf.id_participant}"

                # Petit indicateur visuel pour le vainqueur
                statut = "[GAGNANT]" if perf.est_gagnant else "  [PERDANT]"

                # Affichage des stats (score, kills, etc.)
                stats_str = " | ".join([f"{k}: {v}" for k, v in perf.stats.items()])

                # On aligne le texte pour que ça reste joli
                print(f"{role:<12} : {nom_affiche:<25} {statut:<12} | {stats_str}")

        print(f"\n{'=' * 80}\n")
