# Projet de traitement de données - Gestion de compétitions sportives

## Description du sujet

Suite au succès des Jeux Olympiques de 2024, notre application permet aux utilisateurs de pouvoir consulter les résultats des compétitions ainsi que d'avoir accès à quelques statistiques. Elle modélise des objets tels que les athlètes, équipes, et des matchs tout en assurant la mise à jour des données en fonction de nouveaux résultats. L'application est conçue pour être modulaire et s'adapter à différents jeu de données.

## Installation et configuration

Conformément aux contraintes techniques, l'application utilise exclusiement le langage **Python**.

- Version de Python utilisée : 3.14
- Gestion des dépendances : Les paquets nécessaires sont listés dans le fichier pyproject.toml à la racine du dépôt

## Création de l'environnement virtuel

Pour installer l'application, il faudra exécuter les commandes suivantes :

1. Créer l'environnement virtuel : `python -m venv venv`

2. Activer l'environnement :  `.\venv\Scripts\activate.ps1`

3. Installer les dépendances : `pip install .` et `pip install ruff mypy`

<!--Commande à exécuter en cas de problème : Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process.


Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; python -m venv venv; .\venv\Scripts\activate.ps1;pip install -e .


Penser à rajouter le cas avec MacOS-->

## Utilisation

Pour lancer l'application et accéder au menu, exécuter la commande suivante à la racine du dépôt : `python -m main`
<!-- $env:PYTHONPATH = "src" si problème-->

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
