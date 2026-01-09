#!/bin/bash
# Script de création automatique d'une stack client dans Portainer
# Supporte les abonnements via base de données externe
# Usage: ./create-client-stack.sh -c "dupont" -p "motdepasse123" -s "cle-secrete-32-chars" --sub-pass "password-abonnements"

#set -e

# Valeurs par défaut
PORTAINER_URL="https://host.docker.internal:9443"
PORTAINER_USER="fred"
PORTAINER_PASSWORD="7b5KDg@z@Sno\$NtC"
ENVIRONMENT_ID="2"
BASE_PORT=8080
INITIAL_PASSWORD=""
CLIENT_ID=""

# Valeurs par défaut pour les abonnements
SUBSCRIPTION_DB_HOST="176.131.66.167"
SUBSCRIPTION_DB_PORT="5433"
SUBSCRIPTION_DB_NAME="erpbtp_clients"
SUBSCRIPTION_DB_USER="fred"
SUBSCRIPTION_DB_PASSWORD=""

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
    echo "  -d CLIENT_ID           ID du client (évite l'appel API)"
    echo "  -i INITIAL_PASSWORD    Mot de passe initial (généré si omis)"
    echo "  -u PORTAINER_URL       URL Portainer (défaut: https://localhost:9443)"
    echo "  -U PORTAINER_USER      Utilisateur Portainer (défaut: fred)"
    echo "  -P PORTAINER_PASSWORD  Mot de passe Portainer"
    echo "  -e ENVIRONMENT_ID      ID environnement (défaut: 2)"
    echo "  -b BASE_PORT           Port de base (défaut: 8080)"
    echo ""
    echo "Options abonnements:"
    echo "  --sub-host HOST        Hôte DB abonnements (défaut: 176.131.66.167)"
    echo "  --sub-port PORT        Port DB abonnements (défaut: 5433)"
    echo "  --sub-db DB            Base données abonnements (défaut: erpbtp_clients)"
    echo "  --sub-user USER        Utilisateur DB abonnements (défaut: fred)"
    echo "  --sub-pass PASSWORD    Mot de passe DB abonnements (OBLIGATOIRE)"
    echo ""
    echo "  -h                     Afficher cette aide"
    exit 1
}

# Parser les arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c) CLIENT_NAME="$2"; shift 2 ;;
        -d) CLIENT_ID="$2"; shift 2 ;;
        -p) POSTGRES_PASSWORD="$2"; shift 2 ;;
        -s) SECRET_KEY="$2"; shift 2 ;;
        -i) INITIAL_PASSWORD="$2"; shift 2 ;;
        -u) PORTAINER_URL="$2"; shift 2 ;;
        -U) PORTAINER_USER="$2"; shift 2 ;;
        -P) PORTAINER_PASSWORD="$2"; shift 2 ;;
        -e) ENVIRONMENT_ID="$2"; shift 2 ;;
        -b) BASE_PORT="$2"; shift 2 ;;
        --sub-host) SUBSCRIPTION_DB_HOST="$2"; shift 2 ;;
        --sub-port) SUBSCRIPTION_DB_PORT="$2"; shift 2 ;;
        --sub-db) SUBSCRIPTION_DB_NAME="$2"; shift 2 ;;
        --sub-user) SUBSCRIPTION_DB_USER="$2"; shift 2 ;;
        --sub-pass) SUBSCRIPTION_DB_PASSWORD="$2"; shift 2 ;;
        -h) usage ;;
        *) echo "Option inconnue: $1"; usage ;;
    esac
done

# Vérifier les paramètres requis
if [ -z "$CLIENT_NAME" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$SECRET_KEY" ]; then
    echo "Erreur: Paramètres CLIENT_NAME, POSTGRES_PASSWORD et SECRET_KEY requis"
    usage
fi

# Vérifier que le mot de passe d'abonnement est fourni
if [ -z "$SUBSCRIPTION_DB_PASSWORD" ]; then
    echo "⚠️  ATTENTION: SUBSCRIPTION_DB_PASSWORD non configuré!"
    echo "Les vérifications d'abonnement ne fonctionneront pas."
    echo ""
    read -p "Entrez le mot de passe pour la base d'abonnements (ou Ctrl+C pour annuler): " SUBSCRIPTION_DB_PASSWORD
    if [ -z "$SUBSCRIPTION_DB_PASSWORD" ]; then
        echo "Erreur: Mot de passe d'abonnement requis"
        exit 1
    fi
fi

echo "========================================"
echo "Creation d'une stack client Portainer"
echo "========================================"
echo ""

# Fonction pour échapper les caractères spéciaux pour JSON
json_escape() {
    local string="$1"
    # Utiliser Python pour échapper correctement les caractères spéciaux JSON
    # ensure_ascii=True échappe tous les caractères non-ASCII et spéciaux
    printf '%s' "$string" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read(), ensure_ascii=True)[1:-1])'
}

# Générer un mot de passe initial si non fourni
if [ -z "$INITIAL_PASSWORD" ]; then
    # Vérifier si openssl est disponible, sinon utiliser /dev/urandom
    if command -v openssl >/dev/null 2>&1; then
        INITIAL_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
    else
        INITIAL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)
    fi
    printf "Mot de passe temporaire genere automatiquement: %s\n" "$INITIAL_PASSWORD"
fi

# 0. Utiliser l'ID du client fourni ou le récupérer via API
if [ -n "$CLIENT_ID" ]; then
    echo "[0/4] Utilisation de l'ID client fourni: $CLIENT_ID"
else
    echo "[0/4] Recuperation/creation de l'ID du client via l'API..."
    # Utiliser le nom du service Docker au lieu de localhost
    API_HOST=${API_HOST:-api_client}
    API_RESPONSE=$(curl -s -X POST http://${API_HOST}:8000/client-id/ \
        -H "Content-Type: application/json" \
        -d '{"nom":"'$CLIENT_NAME'","entreprise":"'$CLIENT_NAME'"}')

    echo "Reponse API: $API_RESPONSE"

    # Utiliser sed au lieu de grep -o pour compatibilité Debian
    CLIENT_ID=$(echo "$API_RESPONSE" | sed -n 's/.*"id":\([0-9]*\).*/\1/p' | head -n1)

    if [ -z "$CLIENT_ID" ]; then
        echo "Erreur: Impossible de récupérer ou créer l'ID du client via l'API."
        echo "Verifiez que:"
        echo "  - L'API est lancee sur http://${API_HOST}:8000"
        echo "  - La base de donnees erpbtp_clients est accessible"
        exit 1
    fi

    echo "ID du client: $CLIENT_ID"
fi

# 1. Authentification à Portainer
echo "[1/4] Authentification a Portainer..."
AUTH_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/auth" \
    -H "Content-Type: application/json" \
    -d '{"username":"'$PORTAINER_USER'","password":"'$PORTAINER_PASSWORD'"}')

# Utiliser sed au lieu de grep -o pour compatibilité Debian
TOKEN=$(echo "$AUTH_RESPONSE" | sed -n 's/.*"jwt":"\([^"]*\)".*/\1/p' | head -n1)

if [ -z "$TOKEN" ]; then
    echo "Erreur: Impossible de s'authentifier a Portainer"
    echo "$AUTH_RESPONSE"
    exit 1
fi

echo "Authentification reussie"

# 2. Récupérer la liste des stacks existantes
echo "[2/4] Recuperation des stacks existantes..."
STACKS=$(curl -k -s -X GET "$PORTAINER_URL/api/stacks" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

# Utiliser grep -E pour compatibilité Debian
CLIENT_COUNT=$(echo "$STACKS" | grep -o '"Name":"client-'"$CLIENT_NAME"'_[0-9]\+' | wc -l)

# Récupérer tous les ports utilisés par les stacks existantes
echo "Recuperation des ports utilises..."
USED_PORTS=""
for stack_id in $(echo "$STACKS" | sed -n 's/.*"Id":\([0-9]*\).*/\1/p'); do
    STACK_DETAIL=$(curl -k -s -X GET "$PORTAINER_URL/api/stacks/$stack_id" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json")
    
    PORT=$(echo "$STACK_DETAIL" | sed -n 's/.*"APP_PORT"[^}]*"value":"\([0-9]*\)".*/\1/p' | head -n1)
    if [ -n "$PORT" ]; then
        USED_PORTS="$USED_PORTS $PORT"
    fi
done

# Récupérer aussi les ports utilisés directement par Docker
DOCKER_PORTS=$(docker ps --format "{{.Ports}}" | grep -o '0.0.0.0:[0-9]*' | cut -d':' -f2 | sort -u)
for docker_port in $DOCKER_PORTS; do
    USED_PORTS="$USED_PORTS $docker_port"
done

# Retirer les doublons et trier
USED_PORTS=$(echo $USED_PORTS | tr ' ' '\n' | sort -u | tr '\n' ' ')

# Trouver le premier port disponible
NEXT_PORT=$BASE_PORT
while true; do
    PORT_IN_USE=false
    for used_port in $USED_PORTS; do
        if [ "$NEXT_PORT" = "$used_port" ]; then
            PORT_IN_USE=true
            break
        fi
    done
    
    if [ "$PORT_IN_USE" = false ]; then
        break
    fi
    NEXT_PORT=$((NEXT_PORT + 1))
done

echo "Nombre de clients existants avec ce nom: $CLIENT_COUNT"
echo "Ports actuellement utilises:$USED_PORTS"
echo "Client ID pour ce client: $CLIENT_ID"
echo "Port application attribue: $NEXT_PORT"

# 3. Vérifier si la stack existe déjà (vérification améliorée)
# Vérifier si la stack avec cet ID existe déjà
STACK_EXISTS=$(echo "$STACKS" | grep -o '"Name":"client_'"$CLIENT_ID"'"')
if [ -n "$STACK_EXISTS" ]; then
    echo "Erreur: Une stack pour le client ID $CLIENT_ID existe deja!"
    exit 1
fi

# 4. Créer la nouvelle stack
STACK_NAME="client_$CLIENT_ID"
echo "[3/4] Creation de la stack $STACK_NAME..."

# Échapper les valeurs sensibles pour JSON
# Utiliser printf et stdin pour éviter les problèmes d'échappement shell avec les caractères spéciaux (#, &, $, etc.)
# json.dumps() ajoute des guillemets, donc on les enlève avec [1:-1]
# strip() pour retirer les newlines ajoutés par stdin et .strip('\'"') pour retirer les guillemets ajoutés par l'utilisateur
POSTGRES_PASSWORD_ESCAPED=$(printf '%s' "$POSTGRES_PASSWORD" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().strip().strip('\\'\"'), ensure_ascii=True)[1:-1])")
SECRET_KEY_ESCAPED=$(printf '%s' "$SECRET_KEY" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().strip().strip('\\'\"'), ensure_ascii=True)[1:-1])")
INITIAL_PASSWORD_ESCAPED=$(printf '%s' "$INITIAL_PASSWORD" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().strip().strip('\\'\"'), ensure_ascii=True)[1:-1])")
CLIENT_NAME_ESCAPED=$(printf '%s' "$CLIENT_NAME" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().strip().strip('\\'\"'), ensure_ascii=True)[1:-1])")
SUBSCRIPTION_DB_PASSWORD_ESCAPED=$(printf '%s' "$SUBSCRIPTION_DB_PASSWORD" | python3 -c "import json, sys; print(json.dumps(sys.stdin.read().strip().strip('\\'\"'), ensure_ascii=True)[1:-1])")

# Debug: Afficher les valeurs échappées (attention en production!)
echo "DEBUG: Mot de passe original: $INITIAL_PASSWORD (longueur: ${#INITIAL_PASSWORD})"
echo "DEBUG: Mot de passe échappé pour JSON: $INITIAL_PASSWORD_ESCAPED"
echo "⚠️  ATTENTION: Les caractères spéciaux (#, ?, &) dans les mots de passe peuvent être mal traités par Portainer"

# Créer le JSON de la stack avec Git repository
STACK_JSON=$(cat <<EOF
{
    "name": "$STACK_NAME",
    "repositoryURL": "https://github.com/fvictoire59va/ERP-BTP",
    "repositoryReferenceName": "refs/heads/main",
    "composeFile": "docker-compose.portainer.yml",
    "env": [
        {"name": "POSTGRES_PASSWORD", "value": "$POSTGRES_PASSWORD_ESCAPED"},
        {"name": "SECRET_KEY", "value": "$SECRET_KEY_ESCAPED"},
        {"name": "INITIAL_USERNAME", "value": "$CLIENT_NAME_ESCAPED"},
        {"name": "INITIAL_PASSWORD", "value": "$INITIAL_PASSWORD_ESCAPED"},
        {"name": "CLIENT_ID", "value": "$CLIENT_ID"},
        {"name": "CLIENT_NAME", "value": "$CLIENT_NAME_ESCAPED"},
        {"name": "APP_PORT", "value": "$NEXT_PORT"},
        {"name": "SUBSCRIPTION_DB_HOST", "value": "$SUBSCRIPTION_DB_HOST"},
        {"name": "SUBSCRIPTION_DB_PORT", "value": "$SUBSCRIPTION_DB_PORT"},
        {"name": "SUBSCRIPTION_DB_NAME", "value": "$SUBSCRIPTION_DB_NAME"},
        {"name": "SUBSCRIPTION_DB_USER", "value": "$SUBSCRIPTION_DB_USER"},
        {"name": "SUBSCRIPTION_DB_PASSWORD", "value": "$SUBSCRIPTION_DB_PASSWORD_ESCAPED"}
    ]
}
EOF
)

CREATE_RESPONSE=$(curl -k -s -X POST "$PORTAINER_URL/api/stacks?type=2&method=repository&endpointId=$ENVIRONMENT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$STACK_JSON")

STACK_ID=$(echo "$CREATE_RESPONSE" | sed -n 's/.*"Id":\([0-9]*\).*/\1/p' | head -n1)

if [ -z "$STACK_ID" ]; then
    echo "Erreur: Impossible de creer la stack"
    echo "$CREATE_RESPONSE"
    exit 1
fi

echo "Stack creee avec succes (ID: $STACK_ID)"

# 5. Afficher le résumé
echo ""
echo "[4/4] Resume de la configuration:"
echo "================================="
echo "Nom du client              : $CLIENT_NAME"
echo "Client ID                  : $CLIENT_ID"
echo "Nom de la stack            : $STACK_NAME"
echo "Port application           : $NEXT_PORT"
echo "URL acces                  : http://votre-serveur:$NEXT_PORT"
echo ""
echo "Base de donnees ERP:"
echo "  Base                     : erp_btp"
echo "  Utilisateur              : erp_user"
echo ""
echo "Base de donnees Abonnements:"
echo "  Hôte                     : $SUBSCRIPTION_DB_HOST"
echo "  Port                     : $SUBSCRIPTION_DB_PORT"
echo "  Base                     : $SUBSCRIPTION_DB_NAME"
echo "  Utilisateur              : $SUBSCRIPTION_DB_USER"
echo ""
echo "Identifiants de connexion temporaires:"
echo "  Nom d'utilisateur        : $CLIENT_NAME"
printf "  Mot de passe             : %s\n" "$INITIAL_PASSWORD"
echo "  (A changer lors de la premiere connexion)"
echo "================================="
echo ""
echo "Stack deployee avec succes!"
echo "  Accedez a Portainer pour surveiller le deploiement."
