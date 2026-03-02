# 013-Django (PCNC Fusion)

Projet Django de migration/structuration autour de 4 apps métier :
- accounts
- academics
- imports
- journal

## Objectif
Ce dépôt sert à apprendre Django de façon progressive :
- comprendre la structure projet/apps,
- manipuler les routes, vues, modèles,
- exécuter les migrations,
- préparer une base propre pour continuer le développement.

## Prérequis
- Python 3.10+
- pip
- Git

## Installation rapide (Windows PowerShell)
1. Cloner le dépôt
   - `git clone https://github.com/patincubateur98-jpg/013-Django.git`
   - `cd 013-Django/pcnc_fusion_django`
2. Créer un environnement virtuel
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
3. Installer Django
   - `pip install django`
4. Appliquer les migrations
   - `python manage.py migrate`
5. Lancer le serveur
   - `python manage.py runserver`
6. Ouvrir
   - http://127.0.0.1:8000/

## Structure du projet
- `config/` : configuration globale (settings, urls, asgi, wsgi)
- `accounts/` : authentification et gestion des tuteurs
- `academics/` : classes, étudiants, présences (cœur académique)
- `imports/` : import CSV et journal d’import
- `journal/` : historique et traçabilité
- `templates/` : templates HTML partagés
- `static/` : assets statiques partagés

## Commandes utiles
- Créer des migrations
  - `python manage.py makemigrations`
- Appliquer les migrations
  - `python manage.py migrate`
- Créer un superutilisateur
  - `python manage.py createsuperuser`
- Ouvrir l’admin Django
  - http://127.0.0.1:8000/admin/

## Parcours d’étude recommandé
1. Lire `config/settings.py` et `config/urls.py`
2. Lire `academics/urls.py` puis `academics/views.py`
3. Étudier les modèles dans chaque app (`models.py`)
4. Comprendre les migrations dans chaque dossier `migrations/`
5. Comparer avec tes habitudes Flask pour renforcer la logique Django

## Ressource pédagogique du projet
- `TUTO_DJANGO_EXPLIQUE.md`

---
Si tu veux, je peux ensuite te préparer une version “guide de lecture du code” fichier par fichier avec exercices courts.
