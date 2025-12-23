#!/bin/bash

# Script de création rapide d'une nouvelle stack client dans Portainer
# Usage: ./create-client-stack.sh nom-du-client port-app

CLIENT_NAME=${1:-client}
APP_PORT=${2:-8080}

echo "🚀 Création de la configuration pour le client: $CLIENT_NAME"
echo "📡 Port de l'application: $APP_PORT"

# Générer un mot de passe PostgreSQL aléatoire
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Générer une clé secrète aléatoire
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Créer le fichier de variables d'environnement
cat > ".env.${CLIENT_NAME}" <<EOF
# Configuration pour le client: ${CLIENT_NAME}
# Généré le: $(date)

CLIENT_NAME=${CLIENT_NAME}
APP_PORT=${APP_PORT}
APP_URL=http://localhost:${APP_PORT}

# Base de données
POSTGRES_DB=erp_btp
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Sécurité
SECRET_KEY=${SECRET_KEY}

# Email (à configurer)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=noreply@erp-btp.com

# GitHub
GITHUB_OWNER=fvictoire59va
EOF

echo ""
echo "✅ Fichier de configuration créé: .env.${CLIENT_NAME}"
echo ""
echo "📋 Instructions Portainer:"
echo "1. Créez une nouvelle stack dans Portainer nommée: client-${CLIENT_NAME}"
echo "2. Repository URL: https://github.com/fvictoire59va/ERP-BTP"
echo "3. Reference: refs/heads/main"
echo "4. Compose path: docker-compose.portainer.yml"
echo "5. Copiez les variables suivantes dans 'Environment variables':"
echo ""
cat ".env.${CLIENT_NAME}"
echo ""
echo "⚠️  IMPORTANT: Sauvegardez le mot de passe PostgreSQL dans un endroit sûr!"
echo "📝 Fichier sauvegardé: .env.${CLIENT_NAME}"
