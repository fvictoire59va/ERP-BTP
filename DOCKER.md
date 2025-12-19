# Déploiement Docker - ERP BTP

## Prérequis
- Docker Desktop installé et démarré

## Architecture

L'application utilise deux conteneurs :
1. **PostgreSQL 15** - Base de données (port 5433 en externe, 5432 en interne)
2. **ERP-BTP** - Application web (port 8080)

Les données PostgreSQL sont persistées dans un volume Docker nommé `erpbtp_postgres_data`.

## Méthode 1 : Docker Compose (Recommandé)

La méthode la plus simple :

```powershell
docker-compose up --build -d
```

Ou utilisez le script fourni :
```powershell
.\docker-compose-start.bat
```

## Méthode 2 : Docker classique

Construire l'image :
```powershell
docker build -t erp-btp:latest .
```

Démarrer le conteneur :
```powershell
docker run -d `
    --name erp-btp `
    -p 8080:8080 `
    -v "${PWD}\data:/app/data" `
    -v "${PWD}\logs:/app/logs" `
    --restart unless-stopped `
    erp-btp:latest
```

Ou utilisez le script fourni :
```powershell
.\docker-start.bat
```

## Accès à l'application

Une fois démarré, l'application est accessible à :
- **Local** : http://localhost:8080
- **Réseau local** : http://[IP-de-votre-machine]:8080

## Commandes utiles

### Docker Compose
```powershell
# Voir les logs de l'application
docker-compose logs -f erp-btp

# Voir les logs de PostgreSQL
docker-compose logs -f postgres

# Voir l'état des conteneurs
docker-compose ps

# Vérifier PostgreSQL
.\docker-check.bat

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Arrêter et supprimer les conteneurs (garde les données)
docker-compose down
```

### Docker classique
```powershell
# Voir les logs
docker logs -f erp-btp

# Arrêter
docker stop erp-btp

# Démarrer
docker start erp-btp

# Redémarrer
docker restart erp-btp

# Supprimer le conteneur
docker stop erp-btp
docker rm erp-btp

# Supprimer l'image
docker rmi erp-btp:latest
```

## Volumes et Persistance

Les données sont persistées via des volumes Docker :
- `./data` → `/app/data` (PDFs uniquement)
- `./logs` → `/app/logs` (fichiers logs)
- `postgres_data` → Volume Docker pour PostgreSQL (base de données)

Les données restent sauvegardées même si vous supprimez les conteneurs.

### Accès à PostgreSQL

Depuis votre machine locale :
```powershell
# Via psql (si installé)
psql -h localhost -p 5433 -U fred -d client_erpbtp_victoire

# Via Docker
docker exec -it erp-btp-postgres psql -U fred -d client_erpbtp_victoire
```

Mot de passe : `victoire`

## Port

L'application écoute sur **0.0.0.0:8080** dans le conteneur, mappé sur le port **8080** de votre machine.

## Configuration

L'application utilise PostgreSQL par défaut dans Docker. Les variables d'environnement sont définies dans [docker-compose.yml](docker-compose.yml) :

```yaml
environment:
  - ERP_STORAGE_BACKEND=postgres
  - POSTGRES_HOST=postgres
  - POSTGRES_PORT=5432
  - POSTGRES_DB=client_erpbtp_victoire
  - POSTGRES_USER=fred
  - POSTGRES_PASSWORD=victoire
```

## Notes

- Les conteneurs redémarrent automatiquement (`restart: unless-stopped`)
- PostgreSQL écoute sur le port **5433** en externe pour éviter les conflits
- L'application attend que PostgreSQL soit "healthy" avant de démarrer
- Pour changer les ports, modifiez les mappings dans [docker-compose.yml](docker-compose.yml)

## Migration des données JSON vers PostgreSQL

Si vous avez des données JSON existantes dans le dossier `data/`, vous devez les importer dans PostgreSQL lors de la première utilisation.

### Méthode automatique (Recommandé)

```powershell
.\docker-import-data.bat
```

### Méthode manuelle

```powershell
# Copier le script dans le conteneur
docker cp import_from_json.py erp-btp:/app/import_from_json.py

# Exécuter l'importation
docker exec erp-btp python import_from_json.py
```

Ce script importe :
- ✓ Utilisateurs (avec mots de passe hashés)
- ✓ Clients
- ✓ Projets
- ✓ Autres données (devis, articles, etc.)
