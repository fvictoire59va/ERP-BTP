# Déploiement Docker sur VM Google Cloud (Compute Engine)

## Vue d'ensemble

Ce guide vous aide à déployer l'application ERP BTP sur une VM Google Cloud avec connexion à Cloud SQL.

## Prérequis

- ✅ Base de données importée dans Cloud SQL
- ✅ Compte Google Cloud avec projet actif
- ✅ Fichiers de l'application prêts

## Étape 1 : Créer la VM Compute Engine

### Via la Console Google Cloud

1. **Accédez à Compute Engine** : https://console.cloud.google.com/compute/instances
2. **Créez une instance** :
   - Nom : `erp-btp-vm`
   - Région : Même région que Cloud SQL (pour réduire latence)
   - Type de machine : `e2-micro` (gratuit) ou `e2-small` (recommandé)
   - Image : `Ubuntu 22.04 LTS` ou `Container-Optimized OS`
   - Disque de démarrage : 20 GB SSD
   - Pare-feu : ✅ Autoriser le trafic HTTP et HTTPS

3. **Configuration réseau** :
   - Sous "Réseau" → "Interfaces réseau"
   - IP externe : Éphémère (ou Statique si besoin)

### Via gcloud CLI

```bash
gcloud compute instances create erp-btp-vm \
  --zone=europe-west1-b \
  --machine-type=e2-small \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server \
  --metadata=enable-oslogin=TRUE
```

## Étape 2 : Configurer le pare-feu

### Autoriser le port 8080

```bash
gcloud compute firewall-rules create allow-erp-btp \
  --allow=tcp:8080 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server \
  --description="Allow ERP BTP on port 8080"
```

### Autoriser la connexion à Cloud SQL

Si vous utilisez l'IP publique de Cloud SQL :

1. Dans Cloud SQL → Connexions → Réseaux autorisés
2. Ajoutez l'IP externe de votre VM

**OU** utilisez Cloud SQL Proxy (recommandé, plus sécurisé)

## Étape 3 : Se connecter à la VM

```bash
# Via gcloud
gcloud compute ssh erp-btp-vm --zone=europe-west1-b

# Via la console : cliquez sur "SSH" dans la liste des instances
```

## Étape 4 : Installer Docker sur la VM

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Installer Docker Compose
sudo apt install docker-compose -y

# Vérifier l'installation
docker --version
docker-compose --version

# Déconnexion/reconnexion pour appliquer les permissions
exit
```

Reconnectez-vous à la VM après cette étape.

## Étape 5 : Transférer les fichiers de l'application

### Option A : Via gcloud (depuis votre PC)

```bash
# Créer une archive (depuis D:\PROJETS\ERP BTP)
tar -czf erp-btp.tar.gz --exclude=__pycache__ --exclude=*.pyc --exclude=logs --exclude=data/pdf erp/ main.py requirements.txt Dockerfile docker-compose.yml .env

# Transférer vers la VM
gcloud compute scp erp-btp.tar.gz erp-btp-vm:~ --zone=europe-west1-b

# Sur la VM, extraire
ssh erp-btp-vm
mkdir -p ~/erp-btp
cd ~/erp-btp
tar -xzf ~/erp-btp.tar.gz
```

### Option B : Via Git (recommandé)

Sur la VM :

```bash
# Installer git
sudo apt install git -y

# Cloner le repository
git clone https://github.com/fvictoire59va/ERP-BTP.git erp-btp
cd erp-btp
```

## Étape 6 : Configurer les variables d'environnement

Sur la VM, créez/modifiez le fichier `.env` :

```bash
cd ~/erp-btp
nano .env
```

Contenu du fichier `.env` :

```bash
# Configuration Cloud SQL
POSTGRES_HOST=CLOUD_SQL_PRIVATE_IP  # ou PUBLIC_IP
POSTGRES_PORT=5432
POSTGRES_DB=votre_base
POSTGRES_USER=votre_user
POSTGRES_PASSWORD=votre_password

# Storage backend
ERP_STORAGE_BACKEND=postgres

# Configuration SMTP (optionnel)
APP_URL=http://VOTRE_VM_IP:8080
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe
SMTP_FROM=votre-email@gmail.com
```

**Important** : Récupérez l'IP de Cloud SQL :
```bash
# Via gcloud
gcloud sql instances describe VOTRE_INSTANCE --format="value(ipAddresses[0].ipAddress)"
```

## Étape 7 : Modifier docker-compose.yml

Sur la VM :

```bash
nano docker-compose.yml
```

**Supprimez** la section `extra_hosts` car vous êtes dans le cloud :

```yaml
services:
  erp-btp:
    build: .
    container_name: erp-btp
    ports:
      - "8080:8080"
    # SUPPRIMER extra_hosts:
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - ERP_STORAGE_BACKEND=postgres
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - APP_URL=${APP_URL}
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM=${SMTP_FROM}
    restart: unless-stopped
```

## Étape 8 : Démarrer l'application

```bash
cd ~/erp-btp

# Créer les dossiers nécessaires
mkdir -p data/pdf logs static

# Build et démarrage
docker-compose up --build -d

# Vérifier les logs
docker-compose logs -f
```

## Étape 9 : Accéder à l'application

Récupérez l'IP externe de votre VM :

```bash
# Sur votre PC
gcloud compute instances describe erp-btp-vm --zone=europe-west1-b --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
```

Accédez à : `http://VOTRE_VM_IP:8080`

## Étape 10 : Configuration automatique au démarrage

Sur la VM, créez un service systemd :

```bash
sudo nano /etc/systemd/system/erp-btp.service
```

Contenu :

```ini
[Unit]
Description=ERP BTP Docker Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/VOTRE_USER/erp-btp
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Remplacez `VOTRE_USER` par votre nom d'utilisateur.

Activez le service :

```bash
sudo systemctl daemon-reload
sudo systemctl enable erp-btp.service
sudo systemctl start erp-btp.service
sudo systemctl status erp-btp.service
```

## Option avancée : Utiliser Cloud SQL Proxy (Plus sécurisé)

Au lieu de se connecter directement à Cloud SQL, utilisez le proxy :

### Modifier docker-compose.yml

```yaml
services:
  cloud-sql-proxy:
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest
    command:
      - "--port=5432"
      - "PROJECT:REGION:INSTANCE"
    ports:
      - "5432:5432"
    restart: unless-stopped

  erp-btp:
    depends_on:
      - cloud-sql-proxy
    # ... reste de la config ...
    environment:
      - POSTGRES_HOST=cloud-sql-proxy
```

### Authentification pour Cloud SQL Proxy

```bash
# Sur la VM, installer gcloud et s'authentifier
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
gcloud auth application-default login
```

## Sécurité et bonnes pratiques

### 1. Utiliser HTTPS avec un certificat SSL

```bash
# Installer Nginx comme reverse proxy
sudo apt install nginx certbot python3-certbot-nginx -y

# Configurer Nginx
sudo nano /etc/nginx/sites-available/erp-btp
```

Configuration Nginx :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activer et obtenir le certificat :

```bash
sudo ln -s /etc/nginx/sites-available/erp-btp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d votre-domaine.com
```

### 2. Utiliser une IP statique

```bash
gcloud compute addresses create erp-btp-ip --region=europe-west1
gcloud compute instances delete-access-config erp-btp-vm --access-config-name="external-nat" --zone=europe-west1-b
gcloud compute instances add-access-config erp-btp-vm --access-config-name="external-nat" --address=ERP_BTP_IP --zone=europe-west1-b
```

### 3. Activer les sauvegardes

```bash
# Sauvegarder les données périodiquement
sudo crontab -e
```

Ajouter :

```cron
# Sauvegarde quotidienne à 2h du matin
0 2 * * * cd /home/VOTRE_USER/erp-btp && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/ logs/ && gsutil cp backup-*.tar.gz gs://votre-bucket-backup/
```

## Monitoring et logs

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Statistiques Docker
docker stats

# Logs système
sudo journalctl -u erp-btp.service -f
```

## Mise à jour de l'application

```bash
cd ~/erp-btp

# Arrêter l'application
docker-compose down

# Mettre à jour le code (si Git)
git pull

# Rebuild et redémarrer
docker-compose up --build -d
```

## Troubleshooting

### Impossible de se connecter à Cloud SQL

```bash
# Tester la connexion
docker run --rm postgres:15 psql -h CLOUD_SQL_IP -p 5432 -U USER -d DATABASE -c "SELECT 1;"
```

### Port 8080 non accessible

```bash
# Vérifier le firewall
gcloud compute firewall-rules list | grep 8080

# Vérifier que Docker écoute
sudo netstat -tulpn | grep 8080
```

### Mémoire insuffisante

Augmentez la taille de la VM ou ajoutez du swap :

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Coûts estimés

- VM e2-micro : Gratuit (730h/mois)
- VM e2-small : ~15€/mois
- Cloud SQL db-f1-micro : Gratuit (limité)
- Cloud SQL db-g1-small : ~25€/mois
- Transfert réseau : Variable selon utilisation
- IP statique : ~5€/mois
