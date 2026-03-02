# Django : Expliqué Étape par Étape 🎓

## Introduction : Qu'est-ce que Django ?

Django est un **framework web** comme Flask, mais beaucoup plus **structuré par défaut**. 
Si Flask te dit "fais ce que tu veux", Django te dit "respecte cette structure, ça facilitera ta vie".

### Différence clé Flask vs Django

| Aspect | Flask | Django |
|--------|-------|--------|
| **Philosophie** | Minimaliste (tu décides) | Batterie incluse (opinions fortes) |
| **Où vivent les URL?** | `app.py` (tout ensemble) | Chaque app a son `urls.py` |
| **Modèles BD** | `models.py` (un fichier) | Chaque app a son `models.py` |
| **HTML dynamique** | `render_template()` | `render(request, ...)` |
| **Admin auto?** | Non, tu le fais | Oui, `/admin` gratuit |
| **Locale/i18n** | Babel + configuration manuelle | Natif avec `makemessages`/`compilemessages` |

---

## Partie 1 : Le projet Django créé

### Structure créée

```
pcnc_fusion_django/
├── manage.py                 ← Commande magique pour tout (comme "python app.py" mais plus)
├── config/                   ← Dossier "configuration centrale" du projet
│   ├── settings.py          ← Les réglages (BD, apps, langue, etc.)
│   ├── urls.py              ← Les routes principales (point d'entrée du routeur)
│   ├── wsgi.py              ← Pour production (pas besoin maintenant)
│   └── asgi.py              ← Pour WebSocket (pas besoin maintenant)
├── accounts/                 ← App 1 : Authentification & tuteurs
│   ├── models.py            ← Modèles pour les tuteurs
│   ├── views.py             ← Ce qui affiche les pages login/logout
│   ├── urls.py              ← Routes de accounts (à créer)
│   ├── admin.py             ← Enregistrement dans /admin
│   └── apps.py
├── academics/               ← App 2 : Étudiants, classes, présences
│   ├── models.py
│   ├── views.py
│   ├── urls.py              ← Routes des étudiants/classes
│   └── ...
├── imports/                 ← App 3 : Import CSV
│   ├── models.py            ← ImportLog
│   ├── views.py             ← Vues d'import
│   ├── urls.py              ← Routes /import
│   └── ...
└── journal/                 ← App 4 : Journal historique
    ├── models.py            ← Modèle Journal
    ├── views.py
    ├── urls.py
    └── ...
```

### Que s'est-il passé ?

1. **`django-admin startproject config .`** 
   - Crée la structure projet avec le dossier `config/` (configuration centrale)
   - Génère `manage.py` (une "ligne de commande" pour Django)

2. **`python manage.py startapp accounts`** (et les 3 autres)
   - Crée 4 **apps** (modules métier isolés)
   - Chaque app = "un bout de fonctionnalité" 
     - `accounts` = qui se connecte, avec quel rôle
     - `academics` = affichage des étudiants, classes, présences
     - `imports` = import CSV, journal import
     - `journal` = historique modification réf-free

---

## Partie 2 : Le fichier `settings.py` - Le cœur de la config

C'est **le fichier le plus important** : il dit à Django comment marcher.

### Ce qu'on a modifié dedans

#### 1. **Déclarer les apps**

```python
# AVANT (Django par défaut)
INSTALLED_APPS = [
    'django.contrib.admin',         # Admin Django natif
    'django.contrib.auth',          # Authentification
    'django.contrib.contenttypes',  # Types de contenu
    'django.contrib.sessions',      # Sessions utilisateurs
    'django.contrib.messages',      # Messages flash
    'django.contrib.staticfiles',   # CSS/JS
]

# APRÈS (on rajoute nos apps)
INSTALLED_APPS = [
    # ... (tous les trucs natifs ci-dessus)
    'accounts',      # ← On enregistre notre app
    'academics',
    'imports',
    'journal',
]
```

**Pourquoi?** → Django scanne ces apps pour trouver les modèles, URL, templates, etc. Si l'app n'est pas dans `INSTALLED_APPS`, Django l'ignore.

#### 2. **Où habent les templates HTML**

```python
# AVANT
'DIRS': [],  # Vide = cherche templates seulement dans chaque app

# APRÈS
'DIRS': [BASE_DIR.parent / 'templates'],  # ← Cherche aussi le dossier Flask existant
```

**Pourquoi?** → Comme tes templates Flask sont déjà dans `../templates`, du coup Django les trouvera aussi. Migration douce = moins de travail!

#### 3. **Langue et timezone**

```python
LANGUAGE_CODE = 'fr-fr'        # Français au lieu de 'en-us'
TIME_ZONE = 'Europe/Paris'     # Ton fuseau au lieu de 'UTC'
```

**Pourquoi?** → Django adapte les formats de date/nombre selon la langue, et gère les fuseaux automatiquement.

#### 4. **Où Django cherche tes CSS/JS**

```python
STATICFILES_DIRS = [BASE_DIR.parent / 'static']  # Cherche le dossier Flask existant
```

**Pourquoi?** → Même raison : réutiliser tes assets Flask existants.

---

## Partie 3 : Les URLs (`urls.py`) - Le routeur

En Flask, tu faisais :
```python
@app.route("/etudiants")
def liste_etudiants():
    return render_template(...)
```

En Django, c'est **séparé en 2 fichiers**:

### Le fichier principal `config/urls.py`

```python
# C'est le "hub" central - on enregistre chaque app ici
from django.urls import include, path

urlpatterns = [
    path('', include('academics.urls')),    # Les URL de 'academics' 
    path('admin/', admin.site.urls),        # L'admin Django natif
]
```

**Pense à ça comme l'aiguillage principal d'une gare.**

### Le fichier `academics/urls.py`

```python
# C'est "dedans" academics

from django.urls import path
from .views import home

app_name = 'academics'  # Namespace (pour nommer les URL, ex: 'academics:home')

urlpatterns = [
    path('', home, name='home'),  # Route: GET / → affiche home()
]
```

**Quand tu accèdes à `/`, Django:**
1. Regarde `config/urls.py` → voit `path('', include('academics.urls'))`
2. Va dans `academics/urls.py` → voit `path('', home, ...)`
3. Appelle la fonction `home(request)` du fichier `academics/views.py`

### Avantage vs Flask

- **Modularité**: Chaque app gère ses propres routes.
- **Nommage**: `url_for('academics:home')` dans un template (équivalent de Flask `url_for('home')`) → plus lisible quand ça grandit.

---

## Partie 4 : Les modèles (Étape 1 : vide)

Ton fichier `academics/models.py` est vide pour l'instant:
```python
from django.db import models

# Create your models here.
```

Prochaine étape : on y mettra `Classe`, `Cours`, `Etudiant`, etc.

**Différence Flask vs Django:**

| Flask (SQLAlchemy) | Django ORM |
|-------------------|-----------|
| `from sqlalchemy.orm import declarative_base` | `from django.db import models` |
| `class Etudiant(Base): ...` | `class Etudiant(models.Model): ...` |
| `db.session.add(e)` | `e.save()` |
| `Etudiant.query.filter_by(id=1)` | `Etudiant.objects.filter(id=1).first()` |

---

## Partie 5 : Migrations - Django suit ta BD

En Flask, tu faisais:
```python
db.create_all()  # "Crée toutes les tables d'un coup"
```

En Django, c'est **migrations progressives** (comme des "commits" pour ta BD):

```bash
# 1. Après avoir changé models.py, tu dis à Django de repérer la change
python manage.py makemigrations

# 2. Django crée un fichier de migration (ex: 0001_initial.py)

# 3. Tu appliques la migration
python manage.py migrate
```

**Avantages:**
- Traçabilité : tu vois l'historique des changements BD.
- Reversibility : tu peux "défaire" une migration.
- Collab : quand tu receois du code, tu sais quels changements BD sont supposés.

**Exemple:** Imaginons tu ajoutes un champ `nom` à `Classe`:
```python
# academics/models.py
class Classe(models.Model):
    numero = models.IntegerField()
    nom = models.CharField(max_length=100)  # ← Nouveau champ
```

Ensuite:
```bash
python manage.py makemigrations  # Django dit: "Je vois que tu as ajouté 'nom'"
# → Crée academics/migrations/0001_initial.py
python manage.py migrate         # Exécute la création de la colonne
```

---

## Partie 6 : Les vues - Afficher des pages

### Vue simple (ce qu'on a là)

```python
# academics/views.py
from django.http import HttpResponse

def home(request):
    return HttpResponse("PCNC Fusion Django est prêt ✅")
```

**Quand tu accèdes à `/`:**
1. Django appelle `home(request)`
2. `request` = objet contenant GET/POST/session/user/etc. (équivalent de Flask `request`).
3. On retourne `HttpResponse(...)` = réponse HTTP brute.

### Vue avec template (prochaine étape)

```python
# academics/views.py
from django.shortcuts import render

def liste_etudiants(request):
    etudiants = Etudiant.objects.all()  # ← Récupère tous les étudiants (comme Flask)
    return render(request, 'etudiants/index.html', {
        'etudiants': etudiants  # Contexte = ce qui va dans le template
    })
```

**Template side (`templates/etudiants/index.html`):**
```html
<h1>Liste des étudiants</h1>
<ul>
{% for e in etudiants %}
    <li>{{ e.nom }} {{ e.prenom }}</li>
{% endfor %}
</ul>
```

**C'est identique à Flask (`render_template`).** Jinja2 fonctionne dans Django aussi!

---

## Partie 7 : L'admin Django 🎁 (gratuit!)

Django inclut une interface admin auto-générée à `/admin`.

```python
# accounts/admin.py
from django.contrib import admin
from .models import Tuteur

@admin.register(Tuteur)
class TuteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'role')
    search_fields = ('nom', 'email')
    list_filter = ('role',)
```

**Résultat:** Une interface CRUD complète sans CSS/HTML à écrire. Gratuit.

In Flask? Il faut une librairie genre `flask-admin` (tiers). In Django? C'est natif.

---

## Résumé des étapes 1-6

```
✅ Créé un projet Django avec 4 apps isolées
✅ Configuré settings.py (langue, timezone, apps déclarées)
✅ Créé les routes principales (config/urls.py)
✅ Créé une route d'accueil (academics/urls.py + views.py)
✅ Appliqué les migrations Django initiales

Prochaines étapes:
⏳ Créer les modèles Tuteur, Etudiant, Classe, Cours
⏳ Migrer chaque modèle avec "makemigrations"
⏳ Créer des vues & templates pour CRUD
⏳ Ajouter l'authentification (login/logout/permissions)
⏳ Importer les données Flask existantes
```

---

## Pour tester tout de suite

```bash
cd D:\001-APPRENTISSAGE PYTHON\PCNC2_FUSION\pcnc_fusion_django

# Lance le serveur Django
python manage.py runserver

# Puis visite:
# - http://127.0.0.1:8000/          ← Page d'accueil (vide pour l'instant)
# - http://127.0.0.1:8000/admin/    ← Admin Django (login requis)
```

---

## Questions courantes

**Q: Pourquoi "apps"? C'est pas plus compliqué que Flask "blueprints"?**
R: C'est le même concept (isoler du code par fonctionnalité), Django l'appelle juste "app" et c'est plus strict (oblige à déclarer dans `settings.py`).

**Q: Je dois réécrire tous mes templates?**
R: Non! Jinja2 fonctionne partout. Juste s'il y a des déprécations (ex: `url_for` → `url`), il faudra adapter.

**Q: Et la migration des données depuis Flask (`pcnc.db`)?**
R: On fera ça après avoir créé les modèles Django. Django peut lire la BD Flask existante.

**Q: Combien de temps pour la suite?**
R: Créer les modèles Tuteur/Etudiant/Classe/Cours ca prend 1-2h. Ensuite vues/templates ca avance vite.

---

**Prêt pour l'étape 2 ? 🚀**

---

## Étape 7 faite : modèles + migrations ✅

On vient de créer les modèles Django qui correspondent à votre Flask:

- Dans `academics/models.py`
    - `Classe`
    - `Cours`
    - `Tuteur`
    - `Etudiant`
    - `Presence`
    - `PresenceEtudiant`
    - `TuteurPresence`
- Dans `imports/models.py`
    - `ImportLog`
- Dans `journal/models.py`
    - `Journal`

### Pourquoi c'est important ?

Chaque `class ... (models.Model)` décrit une table SQL.
Django a ensuite généré les migrations (`0001_initial.py`) puis créé les tables automatiquement via `migrate`.

### Pont Flask → Django (très concret)

Flask (SQLAlchemy):

```python
class Etudiant(db.Model):
        nom = db.Column(db.String(100), nullable=False)
        classe_id = db.Column(db.Integer, db.ForeignKey("classe.id"), nullable=False)
```

Django:

```python
class Etudiant(models.Model):
        nom = models.CharField(max_length=100)
        classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name='etudiants')
```

### Commandes exécutées

```bash
python manage.py makemigrations academics imports journal
python manage.py migrate
python manage.py check
```

Résultat: **aucune erreur** (`System check identified no issues`).