#!/bin/bash
# Script de déploiement rapide depuis votre PC local

set -e  # Arrêter en cas d'erreur

VM_IP="34.155.169.14"
VM_USER="frederic_victoire"
PROJECT_DIR="~/erp-btp"

echo "🚀 Déploiement vers la VM..."

# 1. Push vers GitHub
echo "📤 Push vers GitHub..."
git add .
git commit -m "Deploy: $(date +'%Y-%m-%d %H:%M:%S')" || echo "Rien à commiter"
git push origin main

# 2. Connexion SSH et déploiement
echo "🔄 Mise à jour sur la VM..."
ssh $VM_USER@$VM_IP << 'EOF'
  cd ~/erp-btp
  
  # Pull les modifications
  echo "📥 Pull des modifications..."
  git pull origin main
  
  # Rebuild et restart
  echo "🔨 Rebuild de l'application..."
  docker-compose down
  docker-compose build --no-cache
  docker-compose up -d
  
  # Attendre le démarrage
  echo "⏳ Attente du démarrage..."
  sleep 5
  
  # Vérifier les logs
  echo "📋 Logs récents:"
  docker-compose logs --tail=20
  
  echo "✅ Déploiement terminé!"
EOF

echo ""
echo "✅ Application déployée avec succès!"
echo "🌐 URL: http://$VM_IP:8080"
