#!/bin/bash
# Script de déploiement ULTRA-RAPIDE pour le développement
# Redémarre juste le conteneur sans rebuild

set -e

cd ~/erp-btp

echo "⚡ Déploiement ultra-rapide..."

# Pull les modifications
git pull origin main

# Redémarrage simple (2-3 secondes)
docker-compose restart

echo "✅ Fait! Application redémarrée en quelques secondes"
echo "🌐 Test: curl http://localhost:8080"
