# Projet de traitement de données - Gestion de compétitions sportives

## Description du sujet

Suite au succès des Jeux Olympiques de 2024, notre application permet aux utilisateurs de pouvoir consulter les résultats des compétitions ainsi que d'avoir accès à quelques statistiques. Elle modélise des objets tels que les athlètes, équipes, et des matchs tout en assurant la mise à jour des données en fonction de nouveaux résultats. L'application est conçue pour être modulaire et s'adapter à différents jeu de données.

## Installation et configuration

Conformément aux contraintes techniques, l'application utilise exclusivement le langage **Python** (version 3.13 ou supérieure requise).
La gestion des dépendances est centralisée dans le fichier `pyproject.toml` situé à la racine du dépôt.

### Comprendre les modes d'installation

Avant de lancer les commandes, il est important de comprendre la différence entre les deux méthodes d'installation possibles pour ce projet :
*   `pip install .` : Installe uniquement le cœur de l'application et ses dépendances strictes (Pandas, Matplotlib) pour une simple utilisation.
*   `pip install -e .[dev]` : Installe l'application en mode "éditable" (les modifications du code sont appliquées en temps réel sans avoir à réinstaller) et ajoute tous les outils de qualité de code requis pour le développement (Pytest, MyPy, Ruff, Black). **C'est la méthode recommandée ici.**

---

### 1. Installation locale (Sur son propre ordinateur)

Ouvrez votre terminal à la racine du projet et exécutez les commandes correspondant à votre système d'exploitation :

**Sous Windows (PowerShell) :**
1. Autoriser l'exécution des scripts (en cas d'erreur de droits) : `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`
2. Créer l'environnement virtuel : `python -m venv .venv`
3. Activer l'environnement : `.\.venv\Scripts\activate`
4. Installer le projet et les outils de développement : `pip install -e .[dev]`

**Commande tout-en-un :**

Pour aller plus vite et configurer tout votre environnement de développement en une seule ligne de commande, copiez-collez ceci dans votre terminal :

`python -m venv .venv ; .\.venv\Scripts\activate ; pip install -e ".[dev]"`

**Sous macOS / Linux :**
1. Créer l'environnement virtuel : `python3 -m venv .venv`
2. Activer l'environnement : `source .venv/bin/activate`
3. Installer le projet et les outils de développement : `pip install -e .[dev]`

**Commande tout-en-un :**

`python3 -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`

---

### 2. Installation sur Onyxia (SSP Cloud)

Sur la plateforme Onyxia, il est nécessaire de s'assurer que le terminal pointe bien vers votre dossier de travail avant de lancer la création de l'environnement virtuel.

**Procédure étape par étape :**
1. Se placer dans le répertoire du projet : `cd /home/onyxia/work/Projet-traitement-donn--1A`
2. Créer l'environnement virtuel : `python3 -m venv .venv`
3. Activer l'environnement : `source .venv/bin/activate`
4. Installer l'application et les outils de développement : `pip install -e .[dev]`

**Commande tout-en-un (Onyxia) :**

`cd /home/onyxia/work/Projet-traitement-donn--1A && python3 -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`

## Utilisation

Pour lancer l'application et accéder au menu, exécuter la commande suivante à la racine du dépôt : `python -m main`

## Outils de développement et contrôle de la qualité du code

L'application se doit de respecter les bonnes pratiques de programmation afin de s'assurer que de nouvelles personnes aient la possibilité de facilement comprendre le code sans problème.

- Style de documentation: Le code est documenté avec des docstrings suivant le style **Numpy**
- Linter et Formatter : Nous utilisons **Ruff** pour assurer la bonne mise en forme du style de code
    - Il faudra utiliser la commande `ruff check src`
- Typage : Nous utilisons également **mypy** pour vérifier le typage et éviter les erreurs
    - Il faudra utiliser la commande `mypy src`

## Tests et couverture

Les tests unitaires sont réalisés avec le paquet pytest, on pourra alors :

- Exécuter les tests en utilisant `pytest src`
- Vérifier la couverture du code en utilisant `pytest src --cov`

## Licence

Ce projet est distribué sous la licence décrite dans le fichier LICENSE situé à la racine du dépôt.
