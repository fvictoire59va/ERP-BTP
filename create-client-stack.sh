#!/bin/bash
# Script de création automatique d'une stack client dans Portainer
# Usage: ./create-client-stack.sh -c "dupont" -p "motdepasse123" -s "cle-secrete-32-chars"

set -e

# Valeurs par défaut
PORTAINER_URL="https://localhost:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno\$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
INITIAL_PASSWORD=""

# Fonction d'aide
usage() {
    echo "Usage: $0 -c CLIENT_NAME -p POSTGRES_PASSWORD -s SECRET_KEY [OPTIONS]"
    echo ""
    echo "Options requises:"
    echo "  -c CLIENT_NAME         Nom du client"
    echo "  -p POSTGRES_PASSWORD   Mot de passe PostgreSQL"
    echo "  -s SECRET_KEY          Clé secrète (32 caractères)"
    echo ""
    echo "Options:"
    echo "  -i INITIAL_PASSWORD    Mot de passe initial (généré si omis)"
    echo "  -u PORTAINER_URL       URL Portainer (défaut: https://localhost:9443)"
    echo "  -U PORTAINER_USER      Utilisateur Portainer (défaut: fred)"
    echo "  -P PORTAINER_PASSWORD  Mot de passe Portainer"
    echo "  -e ENVIRONMENT_ID      ID environnement (défaut: 2)"
    echo "  -b BASE_PORT           Port de base (défaut: 8080)"
    echo "  -h                     Afficher cette aide"
    exit 1
}

# Parser les arguments
while getopts "c:p:s:i:u:U:P:e:b:h" opt; do
    case $opt in
        c) CLIENT_NAME="$OPTARG" ;;
        p) POSTGRES_PASSWORD="$OPTARG" ;;
        s) SECRET_KEY="$OPTARG" ;;
        i) INITIAL_PASSWORD="$OPTARG" ;;
        u) PORTAINER_URL="$OPTARG" ;;
        U) PORTAINER_USER="$OPTARG" ;;
        P) PORTAINER_PASSWORD="$OPTARG" ;;
        e) ENVIRONMENT_ID="$OPTARG" ;;
        b) BASE_PORT="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Vérifier les paramètres requis
if [ -z "$CLIENT_NAME" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "Erreur: Paramètres CLIENT_NAME, POSTGRES_PASSWORD et SECRET_KEY requis"
    usage
fi

echo "========================================"
echo "Creation d'une stack client Portainer"
echo "========================================"
echo ""

# Générer un mot de passe initial si non fourni
if [ -z "$INITIAL_PASSWORD" ]; then
    INITIAL_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    echo "Mot de passe temporaire genere automatiquement"
fi

# 1. Authentification à Portainer
echo "[1/4] Authentification a Portainer..."
AUTH_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/auth" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$PORTAINER_USER\",\"password\":\"$PORTAINER_PASSWORD\"}")

TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"jwt":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Erreur: Impossible de s'authentifier a Portainer"
    echo "$AUTH_RESPONSE"
    exit 1
fi

echo "Authentification reussie"

# 2. Récupérer la liste des stacks existantes
echo "[2/4] Recuperation des stacks existantes..."
STACKS=$(curl -k -s -X GET "$PORTAINER_URL/api/stacks" \
    -H "X-API-Key: $TOKEN")

# Compter les stacks qui commencent par "client-"
CLIENT_COUNT=$(echo "$STACKS" | grep -o '"Name":"client-[^"]*"' | wc -l)

# Calculer le prochain port disponible
NEXT_PORT=$((BASE_PORT + CLIENT_COUNT))
POSTGRES_PORT=$((5432 + CLIENT_COUNT))

echo "Nombre de clients existants: $CLIENT_COUNT"
echo "Port attribue: $NEXT_PORT"

# 3. Vérifier si la stack existe déjà
EXISTING=$(echo "$STACKS" | grep -o "\"Name\":\"client-$CLIENT_NAME\"" || true)
if [ -n "$EXISTING" ]; then
    echo "Erreur: Une stack pour le client '$CLIENT_NAME' existe deja!"
    exit 1
fi

# 4. Créer la nouvelle stack
echo "[3/4] Creation de la stack client-$CLIENT_NAME..."

STACK_JSON=$(cat <<EOF
{
  "name": "client-$CLIENT_NAME",
  "repositoryURL": "https://github.com/fvictoire59va/ERP-BTP",
  "repositoryReferenceName": "refs/heads/main",
  "composeFile": "docker-compose.portainer.yml",
  "repositoryAuthentication": false,
  "env": [
    {"name": "CLIENT_NAME", "value": "$CLIENT_NAME"},
    {"name": "POSTGRES_PASSWORD", "value": "$POSTGRES_PASSWORD"},
    {"name": "SECRET_KEY", "value": "$SECRET_KEY"},
    {"name": "APP_PORT", "value": "$NEXT_PORT"},
    {"name": "POSTGRES_DB", "value": "erp_btp"},
    {"name": "POSTGRES_USER", "value": "erp_user"},
    {"name": "POSTGRES_PORT", "value": "$POSTGRES_PORT"},
    {"name": "INITIAL_USERNAME", "value": "$CLIENT_NAME"},
    {"name": "INITIAL_PASSWORD", "value": "$INITIAL_PASSWORD"}
  ]
}
EOF
)

CREATE_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/stacks?type=2&method=repository&endpointId=$ENVIRONMENT_ID" \
    -H "X-API-Key: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STACK_JSON")

STACK_ID=$(echo "$CREATE_RESPONSE" | grep -o '"Id":[0-9]*' | cut -d':' -f2)

if [ -z "$STACK_ID" ]; then
    echo "Erreur: Impossible de creer la stack"
    echo "$CREATE_RESPONSE"
    exit 1
fi

echo "Stack creee avec succes (ID: $STACK_ID)"

# 5. Attendre que PostgreSQL soit prêt
echo "[4/6] Attente du demarrage de PostgreSQL..."
CONTAINER_NAME="$CLIENT_NAME-postgres"
MAX_RETRIES=30
RETRY_COUNT=0
POSTGRES_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$POSTGRES_READY" != "true" ]; do
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if docker exec "$CONTAINER_NAME" pg_isready -U erp_user -d erp_btp 2>&1 | grep -q "accepting connections"; then
        POSTGRES_READY=true
        echo "PostgreSQL est pret"
    fi
done

if [ "$POSTGRES_READY" != "true" ]; then
    echo "Timeout: PostgreSQL n'est pas pret apres $MAX_RETRIES tentatives"
    echo "  L'utilisateur devra etre cree manuellement"
fi

# 6. Créer l'utilisateur dans la base de données
if [ "$POSTGRES_READY" = "true" ]; then
    echo "[5/6] Verification de la structure de la base de donnees..."
    
    TABLE_EXISTS=false
    TABLE_RETRIES=0
    MAX_TABLE_RETRIES=20
    
    while [ $TABLE_RETRIES -lt $MAX_TABLE_RETRIES ] && [ "$TABLE_EXISTS" != "true" ]; do
        sleep 3
        TABLE_RETRIES=$((TABLE_RETRIES + 1))
        
        CHECK_TABLE=$(docker exec "$CONTAINER_NAME" psql -U erp_user -d erp_btp -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');" 2>&1 || true)
        
        if echo "$CHECK_TABLE" | grep -q "t"; then
            TABLE_EXISTS=true
            echo "Table 'users' detectee"
        else
            echo "  Attente de la creation de la table 'users' ($TABLE_RETRIES/$MAX_TABLE_RETRIES)..."
        fi
    done
    
    if [ "$TABLE_EXISTS" != "true" ]; then
        echo "La table 'users' n'existe pas encore"
        echo "  L'utilisateur sera cree automatiquement au demarrage de l'application"
    else
        echo "[5/6] Creation de l'utilisateur initial dans la base de donnees..."
        
        SQL_INSERT="INSERT INTO users (username, password, email, nom_complet, role, organisation, actif, created_at, updated_at) VALUES ('$CLIENT_NAME', '$INITIAL_PASSWORD', '$CLIENT_NAME@temp.local', '$CLIENT_NAME', 'admin', '$CLIENT_NAME', true, NOW(), NOW()) ON CONFLICT (username) DO NOTHING;"
        
        if docker exec "$CONTAINER_NAME" psql -U erp_user -d erp_btp -c "$SQL_INSERT" >/dev/null 2>&1; then
            echo "Utilisateur initial cree dans la base de donnees"
            echo "  (Le mot de passe sera hashe au premier login)"
        else
            echo "Avertissement: Impossible de creer l'utilisateur automatiquement"
            echo "  L'utilisateur sera cree au premier demarrage de l'application"
        fi
    fi
fi

# 7. Afficher le résumé
echo ""
echo "[6/6] Resume de la configuration:"
echo "================================="
echo "Nom du client    : $CLIENT_NAME"
echo "Nom de la stack  : client-$CLIENT_NAME"
echo "Port application : $NEXT_PORT"
echo "Port PostgreSQL  : $POSTGRES_PORT"
echo "URL acces        : http://votre-serveur:$NEXT_PORT"
echo "Base de donnees  : erp_btp"
echo "Utilisateur DB   : erp_user"
echo ""
echo "Identifiants de connexion temporaires:"
echo "  Nom d'utilisateur : $CLIENT_NAME"
echo "  Mot de passe      : $INITIAL_PASSWORD"
echo "  (A changer lors de la premiere connexion)"
echo "================================="
echo ""
echo "Stack deployee avec succes!"
echo "  Accedez a Portainer pour surveiller le deploiement."
