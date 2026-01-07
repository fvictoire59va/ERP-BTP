# Script de création de stack Portainer

Ce script automatise la création de stacks client dans Portainer avec toutes les variables d'environnement nécessaires, y compris les paramètres de connexion à la base de données des abonnements.

## Prérequis

- Bash (ou Git Bash sur Windows)
- Python 3
- curl
- Accès à Portainer
- Accès à l'API des clients (optionnel)

## Usage

```bash
./create-client-stack.sh -c "nom_client" -p "postgres_password" -s "secret_key" --sub-pass "subscription_db_password"
```

### Options requises

- `-c CLIENT_NAME` : Nom du client (ex: "dupont")
- `-p POSTGRES_PASSWORD` : Mot de passe PostgreSQL pour la base ERP
- `-s SECRET_KEY` : Clé secrète de l'application (32 caractères minimum)

### Options abonnements

- `--sub-pass PASSWORD` : **OBLIGATOIRE** - Mot de passe de la base des abonnements
- `--sub-host HOST` : Hôte DB abonnements (défaut: 176.131.66.167)
- `--sub-port PORT` : Port DB abonnements (défaut: 5433)
- `--sub-db DB` : Nom de la base abonnements (défaut: erpbtp_clients)
- `--sub-user USER` : Utilisateur DB abonnements (défaut: fred)

### Options facultatives

- `-d CLIENT_ID` : ID du client (évite l'appel API)
- `-i INITIAL_PASSWORD` : Mot de passe initial (généré automatiquement si omis)
- `-u PORTAINER_URL` : URL Portainer (défaut: https://host.docker.internal:9443)
- `-U PORTAINER_USER` : Utilisateur Portainer (défaut: fred)
- `-P PORTAINER_PASSWORD` : Mot de passe Portainer
- `-e ENVIRONMENT_ID` : ID environnement Docker (défaut: 2)
- `-b BASE_PORT` : Port de base pour attribution (défaut: 8080)

## Exemples

### Création basique avec mot de passe d'abonnement

```bash
./create-client-stack.sh \
  -c "dupont" \
  -p "MonMotDePasse123!" \
  -s "ma-cle-secrete-de-32-caracteres" \
  --sub-pass "MotDePasseAbonnements"
```

### Avec ID client spécifique

```bash
./create-client-stack.sh \
  -c "martin" \
  -d 42 \
  -p "Pass123!" \
  -s "ma-cle-secrete-32-chars" \
  --sub-pass "PassAbonnement"
```

### Configuration complète personnalisée

```bash
./create-client-stack.sh \
  -c "entreprise_test" \
  -p "PostgreSQL@2026" \
  -s "cle-secrete-super-longue-32chars" \
  -i "PassInitial2026" \
  --sub-host "192.168.1.100" \
  --sub-port "5433" \
  --sub-db "abonnements_db" \
  --sub-user "admin" \
  --sub-pass "PassAbonnement#2026"
```

## Caractères spéciaux dans les mots de passe

Le script gère correctement les caractères spéciaux dans les mots de passe grâce à l'utilisation de `printf` et `stdin` :

- `#` (commentaire bash)
- `&` (background process)
- `$` (variable)
- `!` (history expansion)
- `@`, `%`, `*`, etc.

**Important** : Toujours mettre les mots de passe entre guillemets simples ou doubles lors de l'appel du script.

## Fonctionnement

1. **Validation** : Vérifie que tous les paramètres requis sont fournis
2. **API Client** : Récupère ou crée l'ID client via l'API (si non fourni)
3. **Portainer** : S'authentifie auprès de Portainer
4. **Ports** : Détecte les ports utilisés et attribue le premier port disponible
5. **Stack** : Crée la stack avec toutes les variables d'environnement
6. **Résumé** : Affiche les informations de connexion

## Variables d'environnement créées

La stack créée contiendra les variables suivantes :

### Base de données ERP
- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `POSTGRES_DB=erp_btp`
- `POSTGRES_USER=erp_user`
- `POSTGRES_PASSWORD` (fourni via `-p`)

### Base de données Abonnements
- `SUBSCRIPTION_DB_HOST` (défaut: 176.131.66.167)
- `SUBSCRIPTION_DB_PORT` (défaut: 5433)
- `SUBSCRIPTION_DB_NAME` (défaut: erpbtp_clients)
- `SUBSCRIPTION_DB_USER` (défaut: fred)
- `SUBSCRIPTION_DB_PASSWORD` (fourni via `--sub-pass`)

### Application
- `APP_URL` : URL d'accès générée automatiquement
- `SECRET_KEY` : Clé secrète fournie
- `INITIAL_USERNAME` : Nom du client
- `INITIAL_PASSWORD` : Mot de passe temporaire
- `CLIENT_ID` : ID du client
- `APP_PORT` : Port attribué automatiquement

## Sortie du script

Le script affiche :

```
========================================
Creation d'une stack client Portainer
========================================

Mot de passe temporaire genere automatiquement
[0/4] Recuperation/creation de l'ID du client via l'API...
ID du client: 42
[1/4] Authentification a Portainer...
Authentification reussie
[2/4] Recuperation des stacks existantes...
Nombre de clients existants avec ce nom: 0
Ports actuellement utilises: 8080 8081 8082
Numero de la base pour ce client: 1
Port application attribue: 8083
[3/4] Creation de la stack client_42...
Stack creee avec succes (ID: 123)

[4/4] Resume de la configuration:
=================================
Nom du client              : dupont
Numero client              : 1
Nom de la stack            : client_42
Port application           : 8083
URL acces                  : http://votre-serveur:8083

Base de donnees ERP:
  Base                     : erp_btp
  Utilisateur              : erp_user

Base de donnees Abonnements:
  Hôte                     : 176.131.66.167
  Port                     : 5433
  Base                     : erpbtp_clients
  Utilisateur              : fred

Identifiants de connexion temporaires:
  Nom d'utilisateur        : dupont
  Mot de passe             : KJxrs8uOU0J
  (A changer lors de la premiere connexion)
=================================

Stack deployee avec succes!
  Accedez a Portainer pour surveiller le deploiement.
```

## Dépannage

### Erreur d'authentification Portainer
Vérifiez les identifiants Portainer avec les options `-U` et `-P`.

### Erreur API client
Si l'API n'est pas accessible, fournissez directement l'ID client avec `-d`.

### Port déjà utilisé
Le script détecte automatiquement les ports utilisés et attribue le suivant disponible.

### Mot de passe tronqué
Assurez-vous de mettre le mot de passe entre guillemets :
```bash
--sub-pass "MotDePasse#Avec$Caracteres@Speciaux"
```

## Sécurité

⚠️ **Attention** :
- Ne jamais committer ce script avec des mots de passe en dur
- Utiliser des variables d'environnement ou un gestionnaire de secrets en production
- Changer les mots de passe temporaires lors de la première connexion

## Support

Pour toute question ou problème, consultez la documentation du projet ou créez une issue sur GitHub.
