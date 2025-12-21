#!/bin/bash
# Script d'auto-déploiement sur la VM
# À placer dans ~/deploy-webhook.sh sur la VM

set -e

echo "$(date): Déploiement déclenché" >> ~/deploy.log

cd ~/erp-btp

# Pull les modifications
git pull origin main

# Rebuild et restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "$(date): Déploiement terminé" >> ~/deploy.log
