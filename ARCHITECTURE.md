# Architecture ERP-BTP

## Vue d'ensemble

ERP-BTP est une application de gestion pour entreprises du bâtiment, développée en Python avec NiceGUI pour l'interface utilisateur.

### Stack technique
- **Python** : 3.12.10
- **UI Framework** : NiceGUI (web-based, reactive UI)
- **Stockage** : Fichiers JSON
- **PDF** : ReportLab pour génération de devis
- **Build** : PyInstaller pour distribution Windows

## Structure du projet

```
erp/
├── config/          # Configuration et thème
│   └── theme.py     # Couleurs et styles
├── core/            # Logique métier
│   ├── auth.py      # Authentification utilisateurs
│   ├── constants.py # Constantes globales
│   ├── data_manager.py  # Gestion des données (CRUD)
│   └── models.py    # Modèles de données (@dataclass)
├── services/        # Services métier
│   └── pdf_service.py   # Génération PDF devis
├── ui/              # Interface utilisateur
│   ├── app.py       # Application principale
│   ├── components.py    # Composants réutilisables
│   ├── menu.py      # Menu principal
│   ├── styles.py    # Styles CSS
│   ├── utils.py     # Utilitaires UI (notifications)
│   └── panels/      # Écrans modulaires
│       ├── auth.py
│       ├── catalogue.py
│       ├── categories.py
│       ├── clients.py
│       ├── dashboard.py
│       ├── devis.py
│       ├── editeur_devis.py
│       ├── liste_articles.py
│       ├── liste_devis.py
│       ├── liste_ouvrages.py
│       ├── organisation.py
│       ├── ouvrages.py
│       ├── parametres.py
│       └── projets.py
└── utils/           # Utilitaires généraux
    ├── exceptions.py
    └── logger.py

data/                # Fichiers JSON de données
├── articles.json
├── categories.json
├── clients.json
├── devis.json
├── fournisseurs.json
├── organisation.json
├── ouvrages.json
├── projets.json
└── users.json
```

## Concepts clés

### 1. DataManager (`erp/core/data_manager.py`)

Gestionnaire centralisé de toutes les données. Singleton accessible via `app_instance.dm`.

**Responsabilités** :
- Chargement/sauvegarde des fichiers JSON
- CRUD sur tous les modèles
- Validation des données
- Gestion des IDs auto-incrémentés

**Exemple** :
```python
app_instance.dm.articles  # Liste des articles
app_instance.dm.save_data()  # Sauvegarde tout
app_instance.dm.load_data()  # Recharge tout
```

### 2. Modèles de données (`erp/core/models.py`)

Tous les modèles sont des `@dataclass` :
- `Organisation` : Infos entreprise
- `Client` : Clients
- `Fournisseur` : Fournisseurs
- `Article` : Articles du catalogue
- `Ouvrage` : Ensembles d'articles (avec composants)
- `ComposantOuvrage` : Ligne article dans un ouvrage
- `Devis` : Devis client
- `LigneDevis` : Ligne dans un devis
- `Chapitre` : Section dans un devis
- `Projet` : Projets clients
- `User` : Utilisateurs système

### 3. Panels modulaires (`erp/ui/panels/`)

Chaque écran est une fonction `create_xxx_panel(app_instance)` :
- Crée l'UI avec NiceGUI
- Utilise `app_instance.dm` pour les données
- Retourne implicitement (UI créée dans le contexte)

**Pattern standard** :
```python
def create_xxx_panel(app_instance):
    with ui.card().classes('w-full shadow-sm').style('padding: 24px;'):
        ui.label('Titre').classes('text-2xl font-bold mb-6')
        
        # Conteneur pour données dynamiques
        container = ui.column().classes('w-full')
        
        def refresh_display():
            container.clear()
            with container:
                # Afficher les données
                pass
        
        refresh_display()
```

### 4. Système de catégories hiérarchiques

**Structure** :
```json
{
  "id": "platrerie",
  "label": "Plâtrerie",
  "children": [
    {"id": "plaques_platre", "label": "Plaques de plâtre", "children": []},
    {"id": "ossature", "label": "Ossature", "children": []}
  ]
}
```

**Limitations** :
- Maximum 2 niveaux (parent → enfant)
- Pas de sous-catégorie de sous-catégorie
- Articles/Ouvrages stockent l'ID de la catégorie finale (parent ou enfant)

**Filtrage** :
- **Articles** : Filtre par catégorie (inclut enfants) OU par sous-catégorie (exact)
- **Ouvrages** : Filtre par catégorie uniquement (inclut enfants)

### 5. Système de devis

**Flux** :
1. Création devis → Client + Projet + Coefficient
2. Ajout d'ouvrages (avec quantité, remise)
3. Organisation en chapitres
4. Calcul automatique : Prix revient × Coefficient × (1 - Remise/100)
5. Génération PDF via `pdf_service.py`

**Calculs** :
- Prix unitaire ouvrage = Σ(composants) × coefficient_devis
- Prix ligne = prix_unitaire × quantité × (1 - remise/100)
- Total HT = Σ(lignes_ouvrages)
- TVA = Total HT × 0.20
- Total TTC = Total HT + TVA

## Conventions de code

### Nomenclature
- **Fichiers** : snake_case (`liste_articles.py`)
- **Classes** : PascalCase (`DataManager`, `Article`)
- **Fonctions** : snake_case (`create_panel`, `refresh_display`)
- **Variables** : snake_case (`app_instance`, `selected_filters`)

### UI Components
- **Boutons primaires** : `.classes('themed-button')`
- **Cartes** : `.classes('w-full shadow-sm')`
- **Titres** : `.classes('text-2xl font-bold mb-6')`
- **Labels** : `.classes('font-semibold text-base')`

### Notifications
```python
from erp.ui.utils import notify_success, notify_error, notify_info

notify_success('Opération réussie')
notify_error('Erreur détaillée')
notify_info('Information')
```

### Dialogues d'édition
```python
from erp.ui.components import create_edit_dialog

def save_callback(values):
    # values = {'field_key': value, ...}
    pass

dialog = create_edit_dialog(
    'Titre',
    fields=[
        {'type': 'input', 'label': 'Nom', 'value': '...', 'key': 'nom'},
        {'type': 'select', 'label': 'Type', 'options': {...}, 'value': '...', 'key': 'type'},
        {'type': 'number', 'label': 'Prix', 'value': 0, 'min': 0, 'step': 0.01, 'key': 'prix'},
        {'type': 'textarea', 'label': 'Description', 'value': '...', 'rows': 3, 'key': 'desc'},
        {'type': 'date', 'label': 'Date', 'value': '2024-01-01', 'key': 'date'},
    ],
    on_save=save_callback
)
dialog.open()
```

## État actuel (Décembre 2025)

### ✅ Fonctionnalités implémentées
- Authentification simple (users.json)
- Gestion clients, fournisseurs
- Catalogue articles avec types et catégories
- Ouvrages composés (multi-articles)
- **Catégories hiérarchiques** (parent → enfants)
- **Sous-catégories** pour articles et ouvrages
- Devis avec chapitres et remises
- Génération PDF devis
- Projets clients
- Organisation (infos entreprise + dates exercice)
- Paramètres (thème, coefficient défaut)

### 🚧 Points d'attention
- Stockage JSON (limites en multi-utilisateurs)
- Pas de gestion des stocks
- Pas d'historique des modifications
- Authentification basique (pas de hash passwords en production)

### 📋 Patterns à suivre pour nouveaux développements

1. **Nouveau panel** :
   - Créer `erp/ui/panels/mon_panel.py`
   - Fonction `create_mon_panel(app_instance)`
   - Importer dans `app.py`
   - Ajouter au menu si nécessaire

2. **Nouveau modèle** :
   - Ajouter `@dataclass` dans `models.py`
   - Ajouter liste dans `DataManager.__init__`
   - Ajouter chargement dans `load_data()`
   - Ajouter sauvegarde dans `save_data()`

3. **Nouvelle fonctionnalité** :
   - Utiliser composants existants (`components.py`)
   - Suivre pattern refresh/container
   - Notifier l'utilisateur (success/error)
   - Sauvegarder avec `app_instance.dm.save_data()`

## Décisions techniques

### Pourquoi NiceGUI ?
- Interface web moderne sans JavaScript
- Reactive binding facile
- Composants Material Design
- Packaging desktop simple

### Pourquoi JSON ?
- Simple pour démarrage
- Pas de serveur DB requis
- Facilement inspectable/debuggable
- Migration future vers SQLite prévue si croissance

### Pourquoi pas de framework web ?
- Application desktop-first
- Pas besoin multi-utilisateurs (pour l'instant)
- Simplicité de déploiement

## Ressources

- [NiceGUI Documentation](https://nicegui.io)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
