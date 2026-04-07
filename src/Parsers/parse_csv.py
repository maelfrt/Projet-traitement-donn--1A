import csv
import pandas as pd
from src.Model.athlete import Athlete
from src.Model.match import Match
from src.Model.equipe import Equipe

"""def parse_players_csv(filepath: str, sep: str = ",") -> list:
    raise Exception(
        "Oh non, la méthode parce_csv n'a pas été implémentée, "
        "vous allez devoir le faire vous-mêmes :("
    )
    return list()"""

# c'est soit on fait full python natif pour load + stats ou soit on utilise pandas :


def parse_athlete_csv(filepath: str, sep: str = ";") -> list:
    """
    Lit un fichier CSV contenant des joueurs et retourne une liste d'objets Athlete.
    """
    athletes_list = []

    # 1. Ouverture du fichier de manière sécurisée avec 'with'
    try:
        with open(filepath, mode='r', encoding='utf-8') as fichier_csv:

            # 2. Utilisation de DictReader pour lire sous forme de dictionnaire
            lecteur_csv = csv.DictReader(fichier_csv, delimiter=sep)

            # 3. Parcours de chaque ligne du fichier
            for ligne in lecteur_csv:

                # 'ligne' est un dictionnaire. Ex: {'Nom': 'Mbappé', 'Age': '25', ...}
                # 4. Extraction et conversion des données
                nom_joueur = ligne.get('name', 'Inconnu')
                age_joueur = int(ligne.get('age', 0))  # On convertit l'âge en entier
                equipe_joueur = ligne.get('team', 'Sans club')

                # 5. Instanciation de l'objet Athlete
                nouvel_athlete = Athlete(
                    nom=nom_joueur,
                    age=age_joueur,
                    equipe=equipe_joueur
                )

                # 6. Ajout à notre liste finale
                athletes_list.append(nouvel_athlete)

    except FileNotFoundError:
        print(f"Erreur : Le fichier {filepath} est introuvable.")
    except Exception as e:
        print(f"Une erreur est survenue lors de la lecture : {e}")

    # 7. Retour de la liste remplie
    return athletes_list


def parse_athlete_df(filepath: str, sep: str = ",") -> pd.DataFrame:
    return pd.read_csv(filepath, sep=sep)
