# Système de Gestion des Abonnements

## Vue d'ensemble

Ce système permet de vérifier automatiquement l'état de l'abonnement d'un client à chaque connexion à l'application ERP BTP. Il se connecte à une base de données PostgreSQL externe qui gère les abonnements de tous les clients.

## Architecture

### Base de données des abonnements

- **Hôte**: 176.131.66.167
- **Port**: 5433
- **Base de données**: erpbtp_clients
- **Table**: abonnements

### Structure de la table abonnements

```sql
CREATE TABLE abonnements (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    date_fin_essai DATE,
    statut VARCHAR(50) DEFAULT 'actif',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Colonnes importantes

- **client_id**: Identifiant du client (email ou username)
- **date_fin_essai**: Date de fin de la période d'essai ou d'abonnement
- **statut**: État de l'abonnement (actif, suspendu, etc.)
- **date_modification**: Date de dernière modification du statut

## Fonctionnement

### 1. Vérification à la connexion

Lors de chaque tentative de connexion :

1. L'utilisateur entre ses identifiants (username/email et mot de passe)
2. Le système vérifie les identifiants locaux
3. Si les identifiants sont corrects, le système interroge la base de données des abonnements
4. Le système vérifie :
   - Si l'abonnement existe
   - Si la date_fin_essai n'est pas dépassée
   - Si le statut n'est pas "suspendu"

### 2. Mise à jour automatique du statut

Si la date_fin_essai est dépassée :
- Le statut est automatiquement mis à jour à "suspendu"
- La date_modification est mise à jour automatiquement
- L'accès est refusé avec le message : "Votre abonnement a expiré. Veuillez renouveler votre abonnement."

### 3. Gestion des erreurs

En cas d'erreur de connexion à la base de données des abonnements :
- Le système log l'erreur
- Par défaut, l'accès est autorisé (pour ne pas bloquer tous les utilisateurs en cas de problème)
- Un message d'avertissement est enregistré dans les logs

## Fichiers modifiés

### 1. erp/services/subscription_service.py (nouveau)

Service dédié à la gestion des abonnements :
- `check_subscription(client_id)`: Vérifie l'état de l'abonnement
- `get_subscription_info(client_id)`: Récupère les informations d'abonnement
- `_update_subscription_status(cursor, abonnement_id, new_status)`: Met à jour le statut

### 2. erp/core/auth.py (modifié)

Modifications de la méthode `authenticate()` :
- Ajout de la vérification d'abonnement après validation des identifiants
- Retourne maintenant un tuple (User, session_id, error_message)
- error_message contient le message d'erreur si l'abonnement est expiré

Modifications de la méthode `register()` :
- Ajout de la vérification d'abonnement lors de l'inscription
- Même format de retour que authenticate()

### 3. erp/ui/panels/auth.py (modifié)

Modifications de `_handle_login()` :
- Gestion du nouveau format de retour de authenticate()
- Affichage du message d'erreur spécifique en cas d'abonnement expiré

Modifications de `_handle_register()` :
- Gestion du nouveau format de retour de register()
- Affichage du message d'erreur spécifique en cas d'abonnement expiré

### 4. .env.portainer et .env.example (modifiés)

Ajout des variables d'environnement :
```env
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=VotreMotDePasseIci
```

## Configuration

### Variables d'environnement

Assurez-vous de configurer les variables suivantes dans votre fichier `.env` ou `.env.portainer` :

```env
# Configuration PostgreSQL pour la base de données des abonnements
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=VotreMotDePasseSecrète
```

### Sécurité

⚠️ **Important** : 
- Ne committez JAMAIS le fichier `.env` avec les vrais mots de passe
- Utilisez `.env.example` comme template
- Configurez les variables d'environnement directement dans Portainer pour la production

## Messages d'erreur

### Pour l'utilisateur

- **Abonnement expiré** : "Votre abonnement a expiré. Veuillez renouveler votre abonnement."
- **Compte suspendu** : "Votre compte est suspendu. Veuillez renouveler votre abonnement."
- **Pas d'abonnement** : "Aucun abonnement actif. Veuillez contacter le support."

### Dans les logs

- Connexion réussie avec abonnement actif : `INFO: Abonnement actif pour le client: {email}`
- Abonnement expiré : `WARNING: Abonnement expiré pour {client_id}, statut mis à jour à 'suspendu'`
- Tentative avec compte suspendu : `WARNING: Tentative de connexion avec compte suspendu: {client_id}`
- Erreur de connexion à la DB : `ERROR: Erreur de connexion à la base des abonnements: {erreur}`

## Tests

Pour tester le système :

1. **Test avec abonnement actif** :
   - Insérer un enregistrement dans la table abonnements avec date_fin_essai future
   - Se connecter avec l'email/username correspondant
   - La connexion devrait réussir

2. **Test avec abonnement expiré** :
   - Insérer un enregistrement avec date_fin_essai passée
   - Se connecter
   - La connexion devrait être refusée
   - Vérifier que le statut a été mis à jour à "suspendu"

3. **Test sans abonnement** :
   - Se connecter avec un email qui n'existe pas dans la table abonnements
   - Un message d'erreur approprié devrait s'afficher

## Exemple SQL

### Créer un abonnement de test

```sql
-- Abonnement actif (expire dans 30 jours)
INSERT INTO abonnements (client_id, date_fin_essai, statut)
VALUES ('test@example.com', CURRENT_DATE + INTERVAL '30 days', 'actif');

-- Abonnement expiré
INSERT INTO abonnements (client_id, date_fin_essai, statut)
VALUES ('expired@example.com', CURRENT_DATE - INTERVAL '1 day', 'actif');

-- Compte suspendu
INSERT INTO abonnements (client_id, date_fin_essai, statut)
VALUES ('suspended@example.com', CURRENT_DATE + INTERVAL '30 days', 'suspendu');
```

### Vérifier les abonnements

```sql
-- Lister tous les abonnements
SELECT * FROM abonnements ORDER BY date_fin_essai;

-- Voir les abonnements expirés
SELECT * FROM abonnements 
WHERE date_fin_essai < CURRENT_DATE;

-- Voir les abonnements actifs
SELECT * FROM abonnements 
WHERE date_fin_essai >= CURRENT_DATE AND statut = 'actif';
```

## Maintenance

### Renouvellement manuel d'un abonnement

```sql
UPDATE abonnements
SET date_fin_essai = CURRENT_DATE + INTERVAL '365 days',
    statut = 'actif',
    date_modification = CURRENT_TIMESTAMP
WHERE client_id = 'client@example.com';
```

### Suspendre manuellement un compte

```sql
UPDATE abonnements
SET statut = 'suspendu',
    date_modification = CURRENT_TIMESTAMP
WHERE client_id = 'client@example.com';
```

### Réactiver un compte

```sql
UPDATE abonnements
SET statut = 'actif',
    date_modification = CURRENT_TIMESTAMP
WHERE client_id = 'client@example.com';
```

## Dépannage

### Erreur de connexion à la base de données

1. Vérifier que les variables d'environnement sont correctement configurées
2. Vérifier que le serveur PostgreSQL est accessible depuis l'application
3. Tester la connexion manuellement :
   ```bash
   psql -h 176.131.66.167 -p 5433 -U postgres -d erpbtp_clients
   ```

### Les abonnements ne sont pas vérifiés

1. Vérifier les logs de l'application
2. S'assurer que le service est correctement importé
3. Vérifier que la table `abonnements` existe dans la base de données

### Un utilisateur est bloqué par erreur

1. Vérifier l'état de l'abonnement dans la base de données
2. Mettre à jour manuellement si nécessaire
3. Vérifier les logs pour comprendre pourquoi le statut a été modifié
