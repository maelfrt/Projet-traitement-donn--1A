from math import pi
from typing import Any

import matplotlib.pyplot as plt


def extraire_matchs(comp):
    matchs = list(comp.liste_match)
    for sc in comp.sous_competitions.values():
        matchs.extend(extraire_matchs(sc))
    return matchs


def generer_top_5_winrate(competition) -> None:
    """Affiche le Top 5 des participants par taux de victoire (Format Rapport/Clair)."""

    bilan: dict[str, dict] = {}

    tous_les_matchs = extraire_matchs(competition)

    for match in tous_les_matchs:
        for perf in match.performances.values():
            nom = perf.participant.nom
            if nom not in bilan:
                bilan[nom] = {"victoires": 0, "joues": 0}
            bilan[nom]["joues"] += 1
            if perf.est_gagnant:
                bilan[nom]["victoires"] += 1

    # Filtrage statistique (minimum 3 matchs)
    MIN_MATCHS = 3
    stats_winrate = []
    for nom, data in bilan.items():
        if data["joues"] >= MIN_MATCHS:
            winrate = (data["victoires"] / data["joues"]) * 100
            stats_winrate.append({"nom": nom, "winrate": winrate, "joues": data["joues"]})

    if not stats_winrate:
        print(f"⚠️ Données insuffisantes (min. {MIN_MATCHS} matchs requis).")
        return

    # Sélection et préparation du Top 5
    top_5 = sorted(stats_winrate, key=lambda x: x["winrate"], reverse=True)[:5]
    top_5.reverse()  # Inversion pour que le 1er soit en haut du graphique horizontal

    noms = [f"{x['nom']} ({x['joues']} m.)" for x in top_5]
    valeurs = [x["winrate"] for x in top_5]

    # --- DESIGN POUR RAPPORT (THÈME CLAIR) ---
    plt.style.use("seaborn-v0_8-whitegrid")
    _, ax = plt.subplots(figsize=(9, 5))

    # Couleur sobre (Bleu Acier) sans bordures dures pour un aspect institutionnel
    bars = ax.barh(noms, valeurs, color="#4682B4", alpha=0.85, edgecolor="none")

    # Ajout des étiquettes de pourcentage
    for bar in bars:
        ax.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1f}%",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#2c3e50",
        )  # Texte sombre pour contraster avec le fond clair

    # Titre et axes
    ax.set_title(
        f"Top 5 : Taux de réussite (Min. {MIN_MATCHS} matchs)", fontsize=13, fontweight="bold", pad=15, color="#2c3e50"
    )
    ax.set_xlabel("Pourcentage de victoire (%)", fontsize=11, color="#34495e")

    # Esthétique des bordures : on retire les traits inutiles pour aérer
    ax.set_xlim(0, 115)  # Marge pour ne pas couper le texte
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)  # On enlève la ligne verticale de gauche

    # On allège l'axe Y (les noms)
    ax.tick_params(axis="y", length=0)

    plt.tight_layout()
    plt.show()

    # Restauration du style par défaut pour ne pas impacter le reste
    plt.style.use("default")


def generer_distribution_matchs(competition) -> None:
    """Affiche la distribution des matchs avec regroupement automatique (bins)."""
    import matplotlib.pyplot as plt

    tous_les_matchs = extraire_matchs(competition)
    bilan_compteur: dict[str, int] = {}

    for match in tous_les_matchs:
        for perf in match.performances.values():
            nom = perf.participant.nom
            bilan_compteur[nom] = bilan_compteur.get(nom, 0) + 1

    if not bilan_compteur:
        print("⚠️ Aucune donnée trouvée.")
        return

    # On récupère la liste brute des nombres de matchs
    donnees = list(bilan_compteur.values())
    nb_participants = len(donnees)

    plt.style.use("seaborn-v0_8-whitegrid")
    _, ax = plt.subplots(figsize=(10, 6))

    # Calcul des intervalles
    val_min = min(donnees)
    val_max = max(donnees)
    plage = val_max - val_min

    if plage <= 10:
        step = 1
    elif plage <= 25:
        step = 2
    elif plage <= 60:
        step = 5
    elif plage <= 120:
        step = 10
    elif plage <= 200:
        step = 20
    elif plage <= 300:
        step = 25
    else:
        step = 50

    start_bin = (val_min // step) * step
    end_bin = ((val_max // step) + 1) * step

    custom_bins = list(range(start_bin, end_bin + step, step))

    n_counts, _, patches = ax.hist(
        donnees, bins=custom_bins, color="#4682B4", alpha=0.7, edgecolor="white", linewidth=1
    )

    # AFFICHAGE DES VALEURS AU-DESSUS DES BARRES
    for count, patch in zip(n_counts, patches):  # type: ignore
        if count > 0:
            x_center = patch.get_x() + patch.get_width() / 2
            y_height = patch.get_height()
            ax.text(
                x_center,
                y_height + 0.2,
                str(int(count)),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="#2c3e50",
            )

    ax.set_xticks(custom_bins)

    if len(custom_bins) > 15:
        plt.xticks(rotation=45, ha="right", fontsize=9)
    else:
        plt.xticks(fontsize=9)

    ax.set_title(f"Répartition de l'activité ({nb_participants} participants)", fontsize=14, fontweight="bold", pad=20)

    ax.set_xlabel("Nombre de matchs disputés (par intervalles)", fontsize=11)
    ax.set_ylabel("Nombre de participants", fontsize=11)

    plt.xticks(fontsize=9)

    ax.yaxis.grid(True, linestyle="--", alpha=0.6)
    ax.xaxis.grid(False)

    # Nettoyage des bordures
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()
    plt.style.use("default")


def generer_nuage_points_stats(competition, stat_x: str, stat_y: str) -> None:
    """Génère un nuage de points professionnel pour rapport (Thème clair et moyennes)."""

    bilan_joueurs: dict[str, Any] = {}

    for match in extraire_matchs(competition):
        for perf in match.performances.values():
            if stat_x in perf.stats and stat_y in perf.stats:
                try:
                    val_x = float(perf.stats[stat_x])
                    val_y = float(perf.stats[stat_y])
                    nom = perf.participant.nom

                    if nom not in bilan_joueurs:
                        bilan_joueurs[nom] = {"x": 0.0, "y": 0.0, "matchs": 0}

                    bilan_joueurs[nom]["x"] += val_x
                    bilan_joueurs[nom]["y"] += val_y
                    bilan_joueurs[nom]["matchs"] += 1
                except (ValueError, TypeError):
                    pass

    if not bilan_joueurs:
        print(f"⚠️ Données insuffisantes pour comparer '{stat_x}' et '{stat_y}'.")
        return

    # Calcul des moyennes par match
    noms, x_vals, y_vals, tailles = [], [], [], []
    for nom, data in bilan_joueurs.items():
        if data["matchs"] > 0:
            noms.append(nom)
            x_vals.append(data["x"] / data["matchs"])
            y_vals.append(data["y"] / data["matchs"])
            tailles.append(data["matchs"] * 12)  # Taille réduite pour la clarté

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Points semi-transparents avec une palette élégante (viridis)
    scatter = ax.scatter(
        x_vals, y_vals, s=tailles, alpha=0.5, c=y_vals, cmap="viridis", edgecolors="#2c3e50", linewidths=0.5
    )

    nom_x_propre = stat_x.replace("_", " ").capitalize()
    nom_y_propre = stat_y.replace("_", " ").capitalize()

    # Barre de couleur sobre
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label(f"{nom_y_propre} (Moyenne)", fontsize=10)

    # On n'affiche le nom que pour le top 3 en X et le top 3 en Y pour éviter la surcharge
    top_x_idx = sorted(range(len(x_vals)), key=lambda i: x_vals[i])[-3:]
    top_y_idx = sorted(range(len(y_vals)), key=lambda i: y_vals[i])[-3:]

    indices_a_nommer = set(top_x_idx + top_y_idx)

    for i in indices_a_nommer:
        ax.annotate(
            noms[i],
            (x_vals[i], y_vals[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            color="#2c3e50",
            arrowprops={"arrowstyle": "-", "color": "gray", "alpha": 0.3},
        )

    # Titres et labels
    ax.set_title(f"Analyse de Corrélation : {nom_x_propre} vs {nom_y_propre}", fontsize=12, fontweight="bold", pad=15)
    ax.set_xlabel(f"{nom_x_propre} (Moyenne par match)", fontsize=10)
    ax.set_ylabel(f"{nom_y_propre} (Moyenne par match)", fontsize=10)

    # Nettoyage final
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.show()
    plt.style.use("default")


def generer_radar_profil(competition, nom_cible: str) -> None:
    """Génère un profil (Radar Chart) normalisé d'un participant vs la Moyenne."""

    bilan: dict = {}

    # Extraction et somme des statistiques
    for match in extraire_matchs(competition):
        for perf in match.performances.values():
            nom = perf.participant.nom
            if nom not in bilan:
                bilan[nom] = {"matchs": 0, "stats": {}}

            bilan[nom]["matchs"] += 1
            for stat_nom, stat_val in perf.stats.items():
                try:
                    valeur = float(stat_val)
                    bilan[nom]["stats"][stat_nom] = bilan[nom]["stats"].get(stat_nom, 0.0) + valeur
                except (ValueError, TypeError):
                    pass

    # Calcul des moyennes
    moyennes_joueurs = {}
    for nom, data in bilan.items():
        if data["matchs"] > 0 and data["stats"]:
            moyennes_joueurs[nom] = {k: v / data["matchs"] for k, v in data["stats"].items()}

    vrai_nom = next((n for n in moyennes_joueurs if n.lower() == nom_cible.strip().lower()), None)
    if not vrai_nom:
        print(f"❌ Erreur : Aucune donnée de match trouvée pour '{nom_cible}' dans cette compétition.")
        print("Vérifiez que le participant a bien joué des matchs enregistrés.")
        return

    print(f"✅ Données trouvées pour {vrai_nom}. Préparation du graphique...")

    stats_cible = moyennes_joueurs[vrai_nom]
    categories = list(stats_cible.keys())

    # Calcul des Maxima et Moyennes globales
    max_stats = {cat: 0.0 for cat in categories}
    avg_stats = {cat: 0.0 for cat in categories}

    for stats in moyennes_joueurs.values():
        for cat in categories:
            if cat in stats:
                max_stats[cat] = max(max_stats[cat], stats[cat])
                avg_stats[cat] += stats[cat]

    nb_joueurs = len(moyennes_joueurs)
    for cat in categories:
        avg_stats[cat] /= nb_joueurs

    # Normalisation
    valeurs_cible = [stats_cible[c] / max_stats[c] if max_stats[c] > 0 else 0 for c in categories]
    valeurs_moyennes = [avg_stats[c] / max_stats[c] if max_stats[c] > 0 else 0 for c in categories]

    # Préparation de la géométrie
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    valeurs_cible += valeurs_cible[:1]
    valeurs_moyennes += valeurs_moyennes[:1]
    angles += angles[:1]

    # --- DESIGN DU GRAPHIQUE ---
    plt.style.use("seaborn-v0_8-whitegrid")

    _, ax = plt.subplots(figsize=(8, 9.5), subplot_kw={"polar": True})

    ax.set_position((0.125, 0.07, 0.75, 0.75))

    # Dessin des axes
    plt.xticks(
        angles[:-1], [c.replace("_", " ").capitalize() for c in categories], color="#2c3e50", size=10, fontweight="bold"
    )

    ax.tick_params(pad=25)

    ax.set_rlabel_position(30)  # type: ignore

    plt.yticks([0.25, 0.5, 0.75, 1.0], ["25%", "50%", "75%", "Record"], color="grey", size=8)
    plt.ylim(0, 1)

    # Tracés
    ax.plot(angles, valeurs_moyennes, linewidth=1, linestyle="dashed", label="Moyenne Tournoi", color="#e74c3c")
    ax.plot(angles, valeurs_cible, linewidth=2, label=vrai_nom, color="#4682B4")
    ax.fill(angles, valeurs_cible, "#4682B4", alpha=0.3)

    plt.title(f"Diagramme Radar : {vrai_nom}", size=12, fontweight="bold", pad=30)
    plt.legend(loc="upper right", bbox_to_anchor=(1.1, 1.1))

    ax.spines["polar"].set_visible(False)

    plt.show()
    plt.style.use("default")
