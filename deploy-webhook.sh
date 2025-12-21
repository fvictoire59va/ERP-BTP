#!/bin/bash
# Script d'auto-déploiement RAPIDE sur la VM

set -e

cd ~/erp-btp

echo "$(date): 🚀 Déploiement rapide déclenché" | tee -a ~/deploy.log

# Pull les modifications
echo "📥 Pull des modifications..."
git pull origin main

# Déterminer si un rebuild est nécessaire
NEED_REBUILD=false

# Vérifier si requirements.txt ou Dockerfile ont changé
if git diff HEAD@{1} HEAD --name-only | grep -E '(requirements.txt|Dockerfile)' > /dev/null 2>&1; then
    NEED_REBUILD=true
    echo "⚠️  Détection de changements dans requirements.txt ou Dockerfile"
fi

if [ "$NEED_REBUILD" = true ]; then
    echo "🔨 Rebuild complet nécessaire..."
    docker-compose down
    docker-compose build
    docker-compose up -d
else
    echo "⚡ Redémarrage rapide (pas de rebuild)..."
    # Simplement redémarrer le conteneur pour recharger le code
    docker-compose restart
fi

# Attendre que l'application soit prête
echo "⏳ Vérification du démarrage..."
sleep 3

# Vérifier que le conteneur tourne
if docker ps | grep -q erp-btp; then
    echo "✅ Application redémarrée avec succès!"
    docker logs erp-btp --tail 5
else
    echo "❌ Erreur: Le conteneur n'a pas démarré"
    docker logs erp-btp --tail 20
    exit 1
fi

echo "$(date): ✅ Déploiement terminé" | tee -a ~/deploy.log
