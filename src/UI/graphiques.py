from typing import Any

import matplotlib.pyplot as plt


def generer_graphique_winrates(stats: dict[str, Any]) -> None:
    """Affiche un graphique à barres des meilleurs winrates."""
    if "meilleur_winrate" not in stats:
        print("Données insuffisantes pour le graphique des winrates.")
        return

    data = stats["meilleur_winrate"]
    noms = [data["nom"], "Moyenne Tournoi"]
    valeurs = [data["winrate"], 50.0]

    plt.figure(figsize=(8, 5))
    plt.bar(noms, valeurs)
    plt.ylabel("Winrate (%)")
    plt.title(f"Domination de {data['nom']}")
    plt.ylim(0, 100)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()


def generer_camembert_provenance(stats: dict[str, Any]) -> None:
    """Affiche la répartition géographique sous forme de camembert."""
    if "top_provenances" not in stats:
        print("Données de provenance manquantes.")
        return

    provenances = [item[0] for item in stats["top_provenances"]]
    comptes = [item[1] for item in stats["top_provenances"]]

    plt.figure(figsize=(7, 7))
    plt.pie(comptes, labels=provenances, autopct="%1.1f%%", startangle=140)
    plt.title("Répartition des Nations les plus représentées")
    plt.show()
