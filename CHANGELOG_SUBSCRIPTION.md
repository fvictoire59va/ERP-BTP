# CHANGELOG - Système de Gestion des Abonnements

## [2026-01-07] - Ajout du système de gestion des abonnements

### 🆕 Nouveaux fichiers créés

1. **erp/services/subscription_service.py**
   - Service de gestion des abonnements
   - Connexion à la base de données PostgreSQL externe (176.131.66.167:5433)
   - Vérification automatique de la date d'expiration
   - Mise à jour automatique du statut "suspendu"
   - Gestion des erreurs de connexion

2. **SUBSCRIPTION_MANAGEMENT.md**
   - Documentation complète du système d'abonnements
   - Guide d'utilisation et de configuration
   - Exemples SQL pour la maintenance
   - Guide de dépannage

3. **init-subscription-db.sql**
   - Script SQL pour créer la table `abonnements`
   - Triggers et fonctions PostgreSQL
   - Données de test
   - Requêtes utiles pour la maintenance

4. **test_subscription.py**
   - Script de test pour vérifier la connexion
   - Tests de vérification d'abonnements
   - Affichage de tous les abonnements
   - Tests automatiques des cas d'usage

### 🔧 Fichiers modifiés

1. **erp/core/auth.py**
   - `authenticate()` : Ajout de la vérification d'abonnement
     - Nouveau format de retour : `(User, session_id, error_message)`
     - Intégration du `SubscriptionService`
     - Refus d'accès si abonnement expiré
   - `register()` : Vérification d'abonnement lors de l'inscription
     - Même format de retour que `authenticate()`

2. **erp/ui/panels/auth.py**
   - `_handle_login()` : Gestion du nouveau format de retour d'`authenticate()`
     - Affichage du message d'erreur spécifique si abonnement expiré
     - Blocage de la connexion en cas d'abonnement suspendu
   - `_handle_register()` : Gestion du nouveau format de retour de `register()`
     - Vérification d'abonnement lors de l'inscription

3. **.env.portainer**
   - Ajout de la section "CONFIGURATION BASE DE DONNÉES ABONNEMENTS"
   - Variables : `SUBSCRIPTION_DB_HOST`, `SUBSCRIPTION_DB_PORT`, `SUBSCRIPTION_DB_NAME`, `SUBSCRIPTION_DB_USER`, `SUBSCRIPTION_DB_PASSWORD`

4. **.env.example**
   - Ajout des mêmes variables d'environnement pour le développement local

5. **README.md**
   - Ajout de la section "Système de gestion des abonnements"
   - Instructions de configuration
   - Exemples d'utilisation
   - Commandes de maintenance
   - Mise à jour de la documentation générale

### 📋 Structure de la base de données

**Table : `abonnements`**
```sql
CREATE TABLE abonnements (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL UNIQUE,
    date_fin_essai DATE,
    statut VARCHAR(50) DEFAULT 'actif',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ✨ Fonctionnalités ajoutées

1. **Vérification automatique à la connexion**
   - Vérifie si `date_fin_essai` est dépassée
   - Met à jour automatiquement le statut à "suspendu" si nécessaire
   - Refuse l'accès avec un message explicite

2. **Messages d'erreur personnalisés**
   - "Votre abonnement a expiré. Veuillez renouveler votre abonnement."
   - "Votre compte est suspendu. Veuillez renouveler votre abonnement."
   - "Aucun abonnement actif. Veuillez contacter le support."

3. **Gestion des erreurs**
   - En cas d'erreur de connexion à la DB des abonnements, l'accès est autorisé par défaut
   - Logging complet de tous les événements
   - Pas de blocage global en cas de problème technique

4. **API du service**
   - `check_subscription(client_id)` : Vérifie et met à jour l'abonnement
   - `get_subscription_info(client_id)` : Récupère les informations détaillées
   - `_update_subscription_status()` : Met à jour le statut (interne)

### 🔒 Sécurité

- Mots de passe stockés dans des variables d'environnement
- Pas de credentials en dur dans le code
- Connexion sécurisée à la base de données externe
- Timeout de connexion configuré (5 secondes)

### 📊 Logs et monitoring

Tous les événements sont loggés :
- Connexions réussies avec abonnement actif
- Abonnements expirés détectés
- Mises à jour de statut
- Tentatives de connexion avec compte suspendu
- Erreurs de connexion à la base de données

### 🧪 Tests

Script de test complet disponible :
```bash
python test_subscription.py
```

Tests inclus :
- Connexion à la base de données
- Vérification d'abonnements individuels
- Liste de tous les abonnements
- Mise à jour automatique des abonnements expirés

### 📝 Variables d'environnement requises

```env
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=VotreMotDePasse
```

### 🚀 Déploiement

1. Configurer les variables d'environnement dans `.env` ou Portainer
2. Exécuter `init-subscription-db.sql` sur la base de données externe
3. Tester avec `python test_subscription.py`
4. Déployer l'application

### 🔄 Migration

**Aucune migration requise** pour l'application existante :
- Les données utilisateurs locales ne sont pas modifiées
- Le système d'abonnements fonctionne en parallèle
- Compatible avec le système d'authentification existant

### ⚠️ Points d'attention

1. **Dépendance externe** : Le système dépend de la disponibilité de la base de données externe
2. **Mot de passe** : Configurer `SUBSCRIPTION_DB_PASSWORD` avant déploiement
3. **Firewall** : Vérifier que le port 5433 est accessible depuis l'application
4. **Identifiant client** : Utilise l'email en priorité, sinon le username

### 📚 Documentation

- Guide complet : [SUBSCRIPTION_MANAGEMENT.md](SUBSCRIPTION_MANAGEMENT.md)
- README mis à jour : [README.md](README.md)
- Script SQL : [init-subscription-db.sql](init-subscription-db.sql)

### 🐛 Problèmes connus

Aucun problème connu à ce jour.

### 🔮 Améliorations futures possibles

1. Interface d'administration pour gérer les abonnements
2. Notification par email avant expiration
3. Système de renouvellement automatique
4. Historique des abonnements
5. Différents types d'abonnements (mensuel, annuel, etc.)
6. Statistiques sur les abonnements
