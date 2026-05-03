import time as time_module
from datetime import UTC, datetime
from typing import Any

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
    Gestionnaire central coordonnant la logique et l'accès aux données.

    Cette classe sert d'interface entre l'interface utilisateur et
    les moteurs spécialisés. Elle maintient l'état de l'application (le sport
    actuellement chargé) et assure la synchronisation entre les recherches,
    les calculs de statistiques et les opérations de sauvegarde.
    """

    def __init__(self) -> None:
        """
        Initialise les composants du système et l'état de la session.
        """
        self.loader: DataLoader = DataLoader()
        self.ranker: RankingEngine = RankingEngine()
        self.searcher: SearchEngine = SearchEngine(self.loader)

        # Référence vers l'objet racine de la compétition en cours
        self.competition_actuelle: Competition | None = None

    @staticmethod
    def valider_et_convertir_date(date_texte: str | None) -> datetime | None:
        """
        Normalise et valide une saisie de date pour le système.

        Cette méthode utilitaire permet de transformer une chaîne de caractères
        souvent mal formatée en un objet date robuste, tout en gérant
        automatiquement le fuseau horaire UTC.

        Parameters
        ----------
        date_texte : str | None
            La chaîne de caractères représentant la date (format YYYY-MM-DD).

        Returns
        -------
        datetime | None
            L'objet date converti ou None si le format est invalide.
        """
        if not date_texte:
            return None

        try:
            # Extraction de la partie date pure pour ignorer d'éventuels horaires
            date_pure = str(date_texte).strip().split(" ")[0]
            return datetime.strptime(date_pure, "%Y-%m-%d").replace(tzinfo=UTC)
        except (ValueError, IndexError, AttributeError):
            return None

    def executer_chargement_complet(self, config_json: str) -> None:
        """
        Pilote le chargement d'un sport et initialise son classement.

        Le contrôleur demande au DataLoader de créer tous les objets,
        puis sollicite immédiatement le RankingEngine pour produire
        le tableau des scores initial.

        Parameters
        ----------
        config_json : str
            Le nom du fichier de configuration du sport à charger.
        """
        self.competition_actuelle = self.loader.initialiser_competition(config_json)

        if self.competition_actuelle:
            self.ranker.generer_classement(self.competition_actuelle)

    def obtenir_resultats(self) -> Competition | None:
        """
        Expose la compétition chargée pour consultation par l'interface.

        Returns
        -------
        Competition | None
            L'instance de compétition active ou None si aucune donnée n'est chargée.
        """
        return self.competition_actuelle

    def rechercher_participants_par_nom(self, nom: str) -> list[Any]:
        """
        Simplifie l'accès à la recherche pour l'interface utilisateur.

        Cette méthode fusionne les résultats des recherches d'équipes et
        d'athlètes pour offrir une expérience de recherche globale.

        Parameters
        ----------
        nom : str
            Le fragment de nom ou mot-clé à rechercher.

        Returns
        -------
        list[Any]
            Une liste d'objets participants correspondants.
        """
        return self.searcher.chercher_equipe_par_nom(nom) + self.searcher.chercher_athlete_par_nom(nom)

    def obtenir_tous_les_participants(self) -> list[Any]:
        """
        Récupère l'intégralité des participants d'un sport chargés en mémoire.

        Returns
        -------
        list[Any]
            Liste exhaustive et unique des participants inscrits.
        """
        if hasattr(self.loader, "_annuaire_participants"):
            return list(set(self.loader._annuaire_participants.values()))
        return []

    def calculer_palmares(self, participant: Participant) -> list[str]:
        """
        Analyse les classements pour identifier les titres gagnés par un participant.

        La méthode vérifie la présence du participant (ou de son équipe)
        à la première place du tournoi principal ou de n'importe quel sous-groupe.

        Parameters
        ----------
        participant : Participant
            Le joueur ou l'équipe dont on souhaite vérifier les titres.

        Returns
        -------
        list[str]
            Liste des mentions honorifiques et trophées identifiés.
        """
        if not self.competition_actuelle:
            return []

        trophees: list[str] = []
        noms_valides = [str(participant.nom).lower().strip()]

        # Pour un athlète, on considère aussi les titres de son équipe actuelle
        equipe = getattr(participant, "equipe_actuelle", None)
        if equipe:
            noms_valides.append(str(equipe).lower().strip())

        # Vérification récursive simplifiée sur le classement de chaque phase
        if self.competition_actuelle.classement_final:
            premier = self.competition_actuelle.classement_final[0]
            if str(premier.get("nom", "")).lower().strip() in noms_valides:
                trophees.append(f"🏆 Vainqueur principal : {self.competition_actuelle.nom}")

        for sous_comp in self.competition_actuelle.sous_competitions.values():
            if sous_comp.classement_final:
                premier = sous_comp.classement_final[0]
                if str(premier.get("nom", "")).lower().strip() in noms_valides:
                    trophees.append(f"🥇 1er de groupe : {sous_comp.nom}")

        return trophees

    def calculer_bilan_historique(self, participant: Participant) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Compile les statistiques de carrière et la liste des matchs disputés.

        Cette méthode est capable de détecter la participation d'un joueur
        même si celui-ci est masqué au sein d'une performance d'équipe.

        Parameters
        ----------
        participant : Participant
            Le participant cible de l'analyse.

        Returns
        -------
        tuple[dict[str, Any], list[dict[str, Any]]]
            Un dictionnaire de statistiques cumulées et la liste chronologique des matchs.
        """
        stats_vides = {"total": 0, "victoires": 0, "defaites": 0, "nuls": 0, "winrate": 0.0}
        if not self.competition_actuelle:
            return stats_vides, []

        tous_matchs = self.competition_actuelle.obtenir_tous_les_matchs()
        historique = []
        victoires = 0
        nuls = 0

        for m in tous_matchs:
            for role, perf in m.performances.items():
                a_participe = False

                # Vérification de l'identité directe ou de l'appartenance à l'effectif du match
                if str(perf.participant.id) == str(participant.id):
                    a_participe = True
                else:
                    joueurs = getattr(perf, "joueurs_match", []) or getattr(perf.participant, "liste_athlete", [])
                    if any(str(j.id) == str(participant.id) for j in joueurs):
                        a_participe = True

                if a_participe:
                    # Identification de l'adversaire pour le compte-rendu visuel
                    adv = "Inconnu"
                    for r_adv, p_adv in m.performances.items():
                        if r_adv != role:
                            adv = p_adv.participant.nom
                            break

                    historique.append(
                        {
                            "gagne": perf.est_gagnant,
                            "nul": getattr(perf, "est_nul", False),
                            "date": m.date_objet.strftime("%Y/%m/%d") if m.date_objet else "N/A",
                            "adversaire": adv,
                            "match": m,
                        }
                    )
                    if perf.est_gagnant:
                        victoires += 1
                    elif getattr(perf, "est_nul", False):
                        nuls += 1

        total = len(historique)
        if total == 0:
            return stats_vides, []

        stats = {
            "total": total,
            "victoires": victoires,
            "nuls": nuls,
            "defaites": total - victoires - nuls,
            "winrate": (victoires / total) * 100,
        }

        historique.sort(key=lambda x: str(x["date"]), reverse=True)
        return stats, historique

    def calculer_face_a_face(self, p1: Participant, p2: Participant) -> dict[str, Any]:
        """
        Analyse l'historique des rencontres directes entre deux adversaires.

        Parameters
        ----------
        p1 : Participant
            Le premier participant (Joueur ou Équipe).
        p2 : Participant
            Le second participant (Joueur ou Équipe).

        Returns
        -------
        dict[str, Any]
            Bilan chiffré des confrontations et liste des matchs partagés.
        """
        total, vic_p1, vic_p2, nuls = 0, 0, 0, 0
        historique: list[dict[str, Any]] = []

        if not self.competition_actuelle:
            return {"total": 0, "victoires_p1": 0, "victoires_p2": 0, "nuls": 0, "historique": []}

        tous_matchs = self.competition_actuelle.obtenir_tous_les_matchs()

        for m in tous_matchs:
            # État de présence et de résultat pour les deux participans dans le match actuel
            p1_present, p2_present = False, False
            p1_gagne, p2_gagne = False, False

            for perf in m.performances.values():
                # On réutilise la logique de détection des joueurs au sein des équipes
                joueurs = getattr(perf, "joueurs_match", []) or getattr(perf.participant, "liste_athlete", [])

                if str(perf.participant.id) == str(p1.id) or any(str(j.id) == str(p1.id) for j in joueurs):
                    p1_present, p1_gagne = True, perf.est_gagnant
                if str(perf.participant.id) == str(p2.id) or any(str(j.id) == str(p2.id) for j in joueurs):
                    p2_present, p2_gagne = True, perf.est_gagnant

            # Traitement si et seulement si les deux adversaires se sont croisés
            if p1_present and p2_present:
                total += 1

                if p1_gagne and not p2_gagne:
                    vic_p1 += 1
                    nom_vainqueur = p1.nom
                elif p2_gagne and not p1_gagne:
                    vic_p2 += 1
                    nom_vainqueur = p2.nom
                else:
                    nuls += 1
                    nom_vainqueur = "Nul"

                historique.append(
                    {
                        "date": m.date_objet.strftime("%Y/%m/%d") if m.date_objet else "N/A",
                        "match": m,
                        "vainqueur": nom_vainqueur,
                    }
                )

        historique.sort(key=lambda x: str(x["date"]), reverse=True)
        return {"total": total, "victoires_p1": vic_p1, "victoires_p2": vic_p2, "nuls": nuls, "historique": historique}

    def calculer_moyennes_participant(self, participant: Participant) -> dict[str, float]:
        """
        Compile les moyennes de performance d'un participant sur sa carrière.

        Cette méthode extrait l'historique complet des matchs du participant et
        calcule la moyenne arithmétique de chaque statistique numérique trouvée.
        Elle gère l'hétérogénéité des données en ignorant les valeurs textuelles.

        Parameters
        ----------
        participant : Participant
            L'athlète ou l'équipe dont on souhaite analyser les performances.

        Returns
        -------
        dict[str, float]
            Un dictionnaire associant le nom de la statistique à sa valeur
            moyenne arrondie à deux décimales.
        """
        if not self.competition_actuelle:
            return {}

        tous_matchs = self.competition_actuelle.obtenir_tous_les_matchs()
        somme_stats: dict[str, float] = {}
        compteur_matchs = 0

        for m in tous_matchs:
            a_joue = False
            stats_match = {}

            # On identifie si le participant était présent dans ce match précis
            for perf in m.performances.values():
                if str(perf.participant.id) == str(participant.id):
                    a_joue = True
                    stats_match = perf.stats
                else:
                    # Détection des joueurs au sein des effectifs d'équipe
                    joueurs = getattr(perf, "joueurs_match", []) or getattr(perf.participant, "liste_athlete", [])
                    if any(str(j.id) == str(participant.id) for j in joueurs):
                        a_joue = True
                        stats_match = perf.stats

            # Si une participation est validée, on cumule les données numériques
            if a_joue and stats_match:
                compteur_matchs += 1
                for cle, val in stats_match.items():
                    try:
                        valeur_num = float(val)
                        somme_stats[cle] = somme_stats.get(cle, 0.0) + valeur_num
                    except (ValueError, TypeError):
                        # On ignore silencieusement les données non calculables (ex: 'N/A')
                        pass

        if compteur_matchs == 0:
            return {}

        # Calcul final de la moyenne pour chaque catégorie de statistique
        return {cle: round(total / compteur_matchs, 2) for cle, total in somme_stats.items()}

    def calculer_moyennes_competition(self, competition: Competition) -> dict[str, float]:
        """
        Calcule les standards de performance pour un groupe de matchs précis.

        Cette méthode permet de définir le 'niveau moyen' d'une phase de jeu
        (poule, finale ou tournoi complet) en moyennant les statistiques
        de toutes les performances enregistrées dans ce périmètre.

        Parameters
        ----------
        competition : Competition
            L'objet compétition ou sous-compétition servant de périmètre d'analyse.

        Returns
        -------
        dict[str, float]
            Le profil statistique moyen par participant pour cette phase.
        """
        somme_stats: dict[str, float] = {}
        compteur_perfs = 0

        # On analyse uniquement les matchs directement rattachés à ce niveau
        for m in competition.liste_match:
            for perf in m.performances.values():
                if perf.stats:
                    compteur_perfs += 1
                    for cle, val in perf.stats.items():
                        try:
                            valeur_num = float(val)
                            somme_stats[cle] = somme_stats.get(cle, 0.0) + valeur_num
                        except (ValueError, TypeError):
                            pass

        if compteur_perfs == 0:
            return {}

        return {cle: round(total / compteur_perfs, 2) for cle, total in somme_stats.items()}

    def inscrire_participant(
        self, type_participant: str, nom: str, provenance: str | None = None
    ) -> Participant | None:
        """
        Crée et indexe un nouveau participant dans le système.

        Parameters
        ----------
        type_participant : str
            "1" pour un Athlète, "2" pour une Équipe.
        nom : str
            Nom du participant à créer.
        provenance : str | None
            Origine géographique.

        Returns
        -------
        Participant | None
            L'instance créée ou None en cas d'erreur.
        """
        prefixe = "P" if type_participant == "1" else "E"
        nouveau_id = f"{prefixe}-{int(time_module.time())}"

        nouvel_objet: Participant | None

        if type_participant == "1":
            nouvel_objet = Athlete(nom=nom, id_personne=nouveau_id, provenance=provenance)
            self.loader.ajouter_participant_en_memoire(nouvel_objet, "athlete")
        else:
            nouvel_objet = Equipe(nom=nom, id_equipe=nouveau_id, provenance=provenance)
            self.loader.ajouter_participant_en_memoire(nouvel_objet, "equipe")

        return nouvel_objet

    def enregistrer_nouveau_match(
        self, date_match: str, liste_donnees_perf: list[dict[str, Any]], nom_sous_comp: str | None = None
    ) -> str:
        """
        Instancie un match manuellement et déclenche la mise à jour des rangs.

        Parameters
        ----------
        date_match : str
            Date de la rencontre (YYYY-MM-DD).
        liste_donnees_perf : list[dict]
            Données brutes des performances saisies via le menu.
        nom_sous_comp : str | None
            Nom de la phase ou du groupe de destination.

        Returns
        -------
        str
            L'identifiant unique généré pour ce match.
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

        # Rangement dans l'arborescence et mise à jour immédiate du classement
        tournoi_cible = self.competition_actuelle
        if nom_sous_comp:
            tournoi_cible = self.competition_actuelle.obtenir_ou_creer_sous_comp(nom_sous_comp)

        tournoi_cible.ajouter_match(nouveau_match)
        self.ranker.generer_classement(self.competition_actuelle)

        return id_nouveau

    def obtenir_structure_match_attendue(self) -> dict[str, dict[str, Any]]:
        """
        Analyse les données existantes pour déduire le formulaire de saisie idéal.

        Cette méthode est cruciale pour la flexibilité du programme : elle
        permet au menu de savoir quelles statistiques demander sans avoir
        à coder les règles de chaque sport en dur.
        """
        if not self.competition_actuelle:
            return {}

        matchs = self.competition_actuelle.obtenir_tous_les_matchs()
        if not matchs:
            return {}

        structure = {}
        for role, perf in matchs[0].performances.items():
            stats_types = {}
            for stat_nom, stat_val in perf.stats.items():
                try:
                    float(stat_val)
                    stats_types[stat_nom] = "nombre"
                except (ValueError, TypeError):
                    stats_types[stat_nom] = "texte"

            structure[role] = {"stats": stats_types, "est_equipe": isinstance(perf.participant, Equipe)}

        return structure

    def supprimer_match(self, id_match: str) -> bool:
        """
        Retire un match de la base et recalcule les scores.
        """
        match, parent = self._trouver_match_et_parent(id_match)
        if match and parent:
            parent.liste_match.remove(match)
            if self.competition_actuelle:
                self.ranker.generer_classement(self.competition_actuelle)
            return True
        return False

    def modifier_match(
        self,
        id_match: str,
        nouvelle_date: str | None = None,
        mises_a_jour_perfs: dict[str, dict[str, Any]] | None = None,
    ) -> bool:
        """
        Applique des modifications ciblées sur un match existant.
        """
        match, _ = self._trouver_match_et_parent(id_match)
        if not match:
            return False

        if nouvelle_date:
            date_validee = self.valider_et_convertir_date(nouvelle_date)
            if date_validee:
                match.date_objet = date_validee

        if mises_a_jour_perfs:
            for role, modifications in mises_a_jour_perfs.items():
                if role in match.performances:
                    perf = match.performances[role]
                    if "est_gagnant" in modifications:
                        perf.est_gagnant = modifications["est_gagnant"]
                    if "stats" in modifications:
                        perf.stats.update(modifications["stats"])

        if self.competition_actuelle:
            self.ranker.generer_classement(self.competition_actuelle)
        return True

    def _trouver_match_et_parent(self, id_match: str) -> tuple[Match | None, Competition | None]:
        """Fouille l'arborescence pour localiser l'objet match et son groupe parent."""
        if not self.competition_actuelle:
            return None, None

        for m in self.competition_actuelle.liste_match:
            if str(m.id_match) == id_match:
                return m, self.competition_actuelle

        for sous_comp in self.competition_actuelle.sous_competitions.values():
            for m in sous_comp.liste_match:
                if str(m.id_match) == id_match:
                    return m, sous_comp

        return None, None

    def sauvegarder_matchs(self, nom_fichier: str = "sauvegarde.csv") -> tuple[bool, int, str]:
        """Exporte l'état actuel vers un fichier CSV physique."""
        if not self.competition_actuelle:
            return False, 0, "Aucune compétition chargée."

        matchs = self.competition_actuelle.obtenir_tous_les_matchs()
        if not matchs:
            return False, 0, "Aucun match à sauvegarder."

        donnees = [m.to_dict() for m in matchs]
        df_export = pd.DataFrame(donnees)

        try:
            self.loader.gestionnaire_csv.sauvegarder_fichier(df=df_export, nom_fichier=nom_fichier)
            return True, len(donnees), nom_fichier
        except OSError as e:
            return False, 0, str(e)
