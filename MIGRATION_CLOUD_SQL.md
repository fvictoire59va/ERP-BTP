# Migration vers Google Cloud SQL PostgreSQL

## Vue d'ensemble

Ce guide vous aide à migrer votre base de données PostgreSQL locale vers Google Cloud SQL.

## Prérequis

1. **Instance Cloud SQL PostgreSQL créée** sur Google Cloud Platform
2. **Connexion autorisée** depuis votre IP ou via Cloud SQL Proxy
3. **Identifiants Cloud SQL** :
   - Host/IP de l'instance
   - Port (généralement 5432)
   - Nom de la base de données
   - Utilisateur et mot de passe

## Méthode 1 : Export/Import avec pg_dump (Recommandé)

### Étape 1 : Exporter la base locale

```bash
# Export complet de la base de données
pg_dump -h localhost -p 5432 -U fred -d client_erpbtp_victoire -F c -f backup_erp.dump

# Ou export en SQL
pg_dump -h localhost -p 5432 -U fred -d client_erpbtp_victoire -f backup_erp.sql
```

### Étape 2 : Importer vers Cloud SQL

```bash
# Restaurer le dump
pg_restore -h <CLOUD_SQL_HOST> -p 5432 -U <CLOUD_SQL_USER> -d <CLOUD_SQL_DB> backup_erp.dump

# Ou avec fichier SQL
psql -h <CLOUD_SQL_HOST> -p 5432 -U <CLOUD_SQL_USER> -d <CLOUD_SQL_DB> -f backup_erp.sql
```

### Étape 3 : Vérifier la migration

```bash
# Compter les enregistrements
psql -h <CLOUD_SQL_HOST> -p 5432 -U <CLOUD_SQL_USER> -d <CLOUD_SQL_DB> -c "SELECT 'users' as table, COUNT(*) FROM users UNION SELECT 'clients', COUNT(*) FROM clients UNION SELECT 'devis', COUNT(*) FROM devis;"
```

## Méthode 2 : Via Cloud SQL Proxy (Plus sécurisé)

### Étape 1 : Installer Cloud SQL Proxy

```bash
# Télécharger
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.windows.amd64.exe

# Authentification
gcloud auth application-default login
```

### Étape 2 : Démarrer le proxy

```bash
# Remplacer INSTANCE_CONNECTION_NAME par votre nom d'instance (format: project:region:instance)
.\cloud-sql-proxy.exe --port 5433 INSTANCE_CONNECTION_NAME
```

### Étape 3 : Exporter/Importer via le proxy

```bash
# Export
pg_dump -h localhost -p 5432 -U fred -d client_erpbtp_victoire -F c -f backup_erp.dump

# Import via proxy (port 5433)
pg_restore -h localhost -p 5433 -U <CLOUD_SQL_USER> -d <CLOUD_SQL_DB> backup_erp.dump
```

## Configuration de l'application

### Mettre à jour .env

```bash
# Configuration Cloud SQL
POSTGRES_HOST=<CLOUD_SQL_PUBLIC_IP>
POSTGRES_PORT=5432
POSTGRES_DB=<CLOUD_SQL_DB>
POSTGRES_USER=<CLOUD_SQL_USER>
POSTGRES_PASSWORD=<CLOUD_SQL_PASSWORD>
```

### Mettre à jour docker-compose.yml

```yaml
environment:
  - POSTGRES_HOST=<CLOUD_SQL_PUBLIC_IP>
  - POSTGRES_PORT=5432
  - POSTGRES_DB=<CLOUD_SQL_DB>
  - POSTGRES_USER=<CLOUD_SQL_USER>
  - POSTGRES_PASSWORD=<CLOUD_SQL_PASSWORD>
```

**Important** : Retirez `host.docker.internal` des `extra_hosts` si vous utilisez Cloud SQL :

```yaml
# Supprimer cette section pour Cloud SQL
# extra_hosts:
#   - "host.docker.internal:host-gateway"
```

## Script de migration automatique

Utilisez le script `migrate_to_cloud_sql.bat` fourni :

```bash
migrate_to_cloud_sql.bat
```

## Sécurité Cloud SQL

### 1. Autoriser l'IP de connexion

Dans la console Cloud SQL :
- Allez dans **Connexions** > **Réseaux autorisés**
- Ajoutez votre IP publique

### 2. Utiliser Cloud SQL Proxy (Recommandé pour production)

Plus sécurisé que l'exposition directe de l'IP :
- Pas besoin d'autoriser des IPs
- Connexion chiffrée automatiquement
- Authentification via IAM

### 3. SSL/TLS

Activez SSL dans Cloud SQL :
```python
# Dans erp/core/database.py, ajouter ssl_mode
engine = create_engine(
    f"postgresql://{user}:{password}@{host}:{port}/{database}",
    connect_args={"sslmode": "require"}
)
```

## Connexion depuis Docker vers Cloud SQL

### Option 1 : IP publique Cloud SQL

```yaml
environment:
  - POSTGRES_HOST=<CLOUD_SQL_PUBLIC_IP>
```

### Option 2 : Cloud SQL Proxy dans Docker

```yaml
services:
  cloud-sql-proxy:
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest
    command:
      - "--port=5432"
      - "<INSTANCE_CONNECTION_NAME>"
    ports:
      - "5432:5432"
    volumes:
      - <path-to-service-account-key>:/config
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/config/key.json

  erp-btp:
    depends_on:
      - cloud-sql-proxy
    environment:
      - POSTGRES_HOST=cloud-sql-proxy
```

## Vérification post-migration

```bash
# Test de connexion
docker-compose exec erp-btp python -c "from erp.core.storage_config import get_data_manager; dm = get_data_manager(); print('Users:', len(dm.users_list)); print('Devis:', len(dm.devis_list))"
```

## Rollback en cas de problème

Si la migration échoue, restaurez la configuration locale :

```bash
# Restaurer .env
POSTGRES_HOST=localhost  # ou host.docker.internal dans Docker

# Redémarrer
docker-compose restart
```

## Performance et coûts

- **Instance minimale** : db-f1-micro (gratuit dans certaines limites)
- **Recommandé** : db-g1-small pour production
- **Sauvegardes automatiques** : Activez dans Cloud SQL
- **Haute disponibilité** : Option régionale pour failover automatique

## Troubleshooting

### Erreur de connexion
```
psql: error: connection to server failed: Connection refused
```
**Solution** : Vérifiez que votre IP est autorisée dans Cloud SQL

### Timeout
```
psql: error: connection to server failed: Connection timed out
```
**Solution** : Vérifiez les règles firewall et utilisez Cloud SQL Proxy

### Authentification échouée
```
psql: error: FATAL: password authentication failed
```
**Solution** : Vérifiez les identifiants et que l'utilisateur existe dans Cloud SQL
