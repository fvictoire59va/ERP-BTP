# Import vers Cloud SQL via l'interface Google Cloud

## Étape 1 : Exporter la base locale

Exécutez le script pour créer un fichier SQL :

```bash
.\export_for_cloud_sql.bat
```

Mot de passe : `victoire`

Cela créera le fichier : `backup_erp_cloud_sql.sql`

## Étape 2 : Upload vers Cloud Storage

### Option A : Via la console Google Cloud

1. Allez sur https://console.cloud.google.com/storage
2. Créez un bucket ou utilisez-en un existant
3. Uploadez le fichier `backup_erp_cloud_sql.sql`

### Option B : Via gcloud CLI

```bash
# Créer un bucket (si nécessaire)
gsutil mb gs://votre-bucket-erp/

# Uploader le fichier
gsutil cp backup_erp_cloud_sql.sql gs://votre-bucket-erp/
```

## Étape 3 : Importer dans Cloud SQL

### Via l'interface Cloud SQL :

1. **Accédez à votre instance** : https://console.cloud.google.com/sql/instances
2. **Sélectionnez votre instance** Cloud SQL PostgreSQL
3. **Cliquez sur "IMPORTER"**
4. **Configurez l'import** :
   - Source : `gs://votre-bucket-erp/backup_erp_cloud_sql.sql`
   - Format : SQL
   - Base de données : Sélectionnez votre base cible

5. **Cliquez sur "Importer"**
6. **Attendez** la fin de l'import (visible dans "Opérations")

### Permissions nécessaires

Si l'import échoue avec une erreur de permissions :

1. Allez dans l'onglet **"Comptes de service"** de votre instance
2. Copiez l'adresse email du compte de service (format : `xxx@xxx.iam.gserviceaccount.com`)
3. Dans Cloud Storage, donnez les permissions de lecture à ce compte sur votre bucket

## Étape 4 : Vérifier l'import

```bash
# Se connecter à Cloud SQL
gcloud sql connect VOTRE_INSTANCE --user=postgres --database=VOTRE_DB

# Vérifier les données
SELECT 'users' as table_name, COUNT(*) FROM users
UNION SELECT 'clients', COUNT(*) FROM clients
UNION SELECT 'devis', COUNT(*) FROM devis
UNION SELECT 'projets', COUNT(*) FROM projets;
```

## Étape 5 : Mettre à jour l'application

### Modifier .env

```bash
POSTGRES_HOST=CLOUD_SQL_PUBLIC_IP
POSTGRES_PORT=5432
POSTGRES_DB=VOTRE_DB
POSTGRES_USER=VOTRE_USER
POSTGRES_PASSWORD=VOTRE_PASSWORD
```

### Modifier docker-compose.yml

Retirez `extra_hosts` et mettez à jour les variables d'environnement :

```yaml
services:
  erp-btp:
    # ... autres configurations ...
    # Supprimer:
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"
    
    environment:
      - POSTGRES_HOST=VOTRE_CLOUD_SQL_IP
      - POSTGRES_PORT=5432
      - POSTGRES_DB=VOTRE_DB
      - POSTGRES_USER=VOTRE_USER
      - POSTGRES_PASSWORD=VOTRE_PASSWORD
```

### Redémarrer l'application

```bash
docker-compose down
docker-compose up -d
```

## Alternative : Import direct via psql

Si votre fichier est petit (<100 MB) et que vous avez accès direct à Cloud SQL :

```bash
# Via Docker avec psql
docker run --rm -i -v "%cd%:/backup" -e PGPASSWORD=CLOUD_SQL_PASSWORD postgres:15 psql -h CLOUD_SQL_IP -p 5432 -U CLOUD_SQL_USER -d CLOUD_SQL_DB -f /backup/backup_erp_cloud_sql.sql
```

## Troubleshooting

### Erreur de permissions sur Cloud Storage

```
Error: Access Denied
```

**Solution** : Donnez les permissions "Storage Object Viewer" au compte de service Cloud SQL

### Timeout pendant l'import

**Solution** : 
- Vérifiez que l'IP source est autorisée dans Cloud SQL
- Augmentez le timeout dans les paramètres Cloud SQL
- Utilisez un fichier plus petit ou import incrémental

### Erreur "database does not exist"

**Solution** : Créez la base de données d'abord :

```sql
CREATE DATABASE votre_db;
```

Puis relancez l'import.
