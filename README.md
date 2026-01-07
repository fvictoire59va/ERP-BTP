# ERP pour le BTP - Second Œuvre

Application de gestion de devis complète basée sur NiceGUI avec système d'authentification et gestion des abonnements.

## Fonctionnalités principales

- ✅ Gestion des clients et projets
- ✅ Catalogue d'articles et ouvrages
- ✅ Création et édition de devis
- ✅ Export PDF des devis
- ✅ Authentification utilisateur
- ✅ **Gestion des abonnements avec vérification automatique**
- ✅ Support PostgreSQL et JSON

## Structure du projet

```
erp/
├── core/               # Cœur de l'application
│   ├── auth.py        # Système d'authentification
│   ├── database.py    # Gestion PostgreSQL
│   └── models.py      # Modèles de données
├── services/          # Services externes
│   ├── email_service.py       # Envoi d'emails
│   ├── pdf_service.py         # Génération PDF
│   └── subscription_service.py # Gestion des abonnements ⭐
├── ui/                # Interface utilisateur
│   ├── app.py         # Application principale
│   └── panels/        # Panneaux de l'interface
└── utils/             # Utilitaires
```

## 🔐 Système de gestion des abonnements

L'application vérifie automatiquement l'état de l'abonnement à chaque connexion.

### Configuration

1. Copier `.env.example` vers `.env`
2. Configurer les paramètres de connexion à la base de données des abonnements :

```env
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=VotreMotDePasse
```

### Base de données des abonnements

La table `abonnements` doit contenir les colonnes suivantes :
- `client_id` : Identifiant du client (email ou username)
- `date_fin_essai` : Date de fin d'abonnement
- `statut` : État de l'abonnement (actif, suspendu, etc.)

📖 **Documentation complète** : Voir [SUBSCRIPTION_MANAGEMENT.md](SUBSCRIPTION_MANAGEMENT.md)

### Initialisation de la base

```bash
# Exécuter le script SQL d'initialisation
psql -h 176.131.66.167 -p 5433 -U postgres -d erpbtp_clients -f init-subscription-db.sql
```

### Test du système

```bash
# Tester la connexion et le système d'abonnements
python test_subscription.py
```

## Installation et démarrage

### Prérequis

- Python 3.9+
- PostgreSQL (optionnel, peut utiliser JSON)

### Installation locale

```powershell
# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Lancer l'application
python main.py
```

### Déploiement avec Docker & Portainer

```bash
# 1. Copier et configurer les variables d'environnement
cp .env.portainer .env.portainer.local
# Éditer .env.portainer.local avec vos paramètres

# 2. Déployer avec Docker Compose
docker-compose -f docker-compose.portainer.yml up -d
```

## Configuration

### Variables d'environnement principales

```env
# Backend de stockage
ERP_STORAGE_BACKEND=postgres  # ou 'json'

# Base de données principale (données ERP)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp_btp
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=VotreMotDePasse

# Base de données des abonnements (externe)
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=VotreMotDePasse

# Configuration email (optionnel)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
```

## Utilisation

1. **Connexion** : Accédez à l'application via votre navigateur
2. **Authentification** : Le système vérifie automatiquement votre abonnement
3. **Gestion** : Créez vos devis, clients, et projets

### Messages d'erreur d'abonnement

- ❌ "Votre abonnement a expiré. Veuillez renouveler votre abonnement."
- ❌ "Votre compte est suspendu. Veuillez renouveler votre abonnement."
- ❌ "Aucun abonnement actif. Veuillez contacter le support."

## Sécurité

⚠️ **Important** :
- Ne committez JAMAIS de fichier `.env` avec de vrais mots de passe
- Utilisez des mots de passe forts pour la production
- Changez `SECRET_KEY` pour chaque installation
- Configurez correctement le pare-feu pour PostgreSQL

## Support et Documentation

- 📄 [Gestion des abonnements](SUBSCRIPTION_MANAGEMENT.md)
- 📄 [Architecture](ARCHITECTURE.md)
- 🐛 Issues : Créez une issue sur GitHub

## Maintenance

### Renouveler un abonnement

```sql
UPDATE abonnements
SET date_fin_essai = CURRENT_DATE + INTERVAL '365 days',
    statut = 'actif'
WHERE client_id = 'client@example.com';
```

### Vérifier les abonnements expirés

```sql
SELECT * FROM abonnements 
WHERE date_fin_essai < CURRENT_DATE;
```

## Notes techniques

- Les données sont sauvegardées dans `data/` (mode JSON) ou PostgreSQL
- Les PDFs générés sont stockés dans `data/pdf/`
- Les logs sont dans `logs/`
- Export PDF intégré avec reportlab

