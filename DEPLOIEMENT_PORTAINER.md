# 🐳 Déploiement avec Portainer

Ce guide explique comment déployer l'ERP BTP avec Portainer pour une gestion multi-clients avec mise à jour automatique depuis GitHub.

## 📋 Vue d'ensemble

L'architecture permet de déployer plusieurs instances isolées de l'ERP BTP, chacune avec sa propre base de données PostgreSQL, le tout géré via Portainer avec des mises à jour automatiques depuis GitHub.

```
┌─────────────────────────────────────────┐
│         Serveur Portainer               │
├─────────────────────────────────────────┤
│  Stack Client 1                         │
│  ├─ PostgreSQL (DB Client 1)            │
│  └─ ERP BTP (Instance Client 1)         │
├─────────────────────────────────────────┤
│  Stack Client 2                         │
│  ├─ PostgreSQL (DB Client 2)            │
│  └─ ERP BTP (Instance Client 2)         │
├─────────────────────────────────────────┤
│  Stack Client N...                      │
└─────────────────────────────────────────┘
```

## 🚀 Étape 1 : Installation de Portainer

### Installation sur serveur Linux/VM

```bash
# Créer le volume Portainer
docker volume create portainer_data

# Lancer Portainer
docker run -d \
  -p 8000:8000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

Accédez à Portainer : `https://votre-serveur:9443`

## 🔐 Étape 2 : Configuration GitHub Container Registry

### 2.1 Rendre le repository public (optionnel)

Si votre dépôt est privé, vous avez deux options :

**Option A : Repository public**
- Allez dans Settings > General > Danger Zone
- Cliquez sur "Change visibility" > "Make public"

**Option B : Token d'accès pour repository privé**
```bash
# Créer un Personal Access Token sur GitHub
# Settings > Developer settings > Personal access tokens > Tokens (classic)
# Permissions : read:packages
```

### 2.2 Activer GitHub Actions

Le workflow `.github/workflows/docker-build.yml` est déjà configuré dans votre projet. Voici comment vérifier et activer GitHub Actions :

#### Étape 1 : Vérifier que GitHub Actions est activé

1. Allez sur votre repository : `https://github.com/fvictoire59va/ERP-BTP`
2. Cliquez sur l'onglet **Actions** (en haut)
3. Si c'est la première fois :
   - GitHub vous demandera d'activer les workflows
   - Cliquez sur **"I understand my workflows, go ahead and enable them"**

#### Étape 2 : Vérifier les permissions du GITHUB_TOKEN

1. Allez dans **Settings** (de votre repository)
2. Dans le menu de gauche : **Actions** > **General**
3. Descendez à la section **"Workflow permissions"**
4. Sélectionnez **"Read and write permissions"** (important pour push les images)
5. Cochez **"Allow GitHub Actions to create and approve pull requests"**
6. Cliquez sur **Save**

#### Étape 3 : Déclencher le premier build

**Option A : Push automatique** (recommandé si vous avez des modifications)
```bash
git add .
git commit -m "Configuration Portainer Stack"
git push origin main'
```

**Option B : Déclencher manuellement**
1. Allez dans l'onglet **Actions**
2. Sélectionnez le workflow **"Build and Push Docker Image"**
3. Cliquez sur **"Run workflow"** (bouton à droite)
4. Sélectionnez la branche `main`
5. Cliquez sur **"Run workflow"**

#### Étape 4 : Surveiller le build

1. Dans l'onglet **Actions**, vous verrez le workflow en cours
2. Cliquez dessus pour voir les détails
3. Le build prend environ 2-5 minutes
4. Vous verrez :
   - ✅ Checkout repository
   - ✅ Log in to GitHub Container Registry
   - ✅ Extract metadata for Docker
   - ✅ Build and push Docker image

#### Étape 5 : Vérifier que l'image est créée

1. Allez sur votre profil GitHub ou la page du repository
2. Cliquez sur **Packages** (ou allez directement à `https://github.com/fvictoire59va?tab=packages`)
3. Vous devriez voir le package **erp-btp**
4. Cliquez dessus pour voir les détails

**Ce que fait le workflow à chaque push sur `main` :**
1. ✅ Build l'image Docker depuis votre Dockerfile
2. ✅ Tag l'image avec `latest` et le SHA du commit
3. ✅ Push vers GitHub Container Registry (`ghcr.io/fvictoire59va/erp-btp:latest`)
4. ✅ Déclenche le webhook Portainer (si configuré)

### 2.3 Rendre l'image publique

1. Allez sur GitHub : `https://github.com/fvictoire59va/ERP-BTP/packages`
2. Sélectionnez le package `erp-btp`
3. Package settings > Change visibility > Public

## 📦 Étape 3 : Créer une Stack dans Portainer

### 3.1 Créer la stack

1. Connectez-vous à Portainer
2. Sélectionnez votre environnement (local)
3. Cliquez sur **Stacks** > **Add stack**

### 3.2 Configuration de la stack

**Nom de la stack** : `client-nomduclient` (exemple : `client-dupont`)

**Build method** : Sélectionnez **Repository**

**Repository URL** :
```
https://github.com/fvictoire59va/ERP-BTP
```

**Reference** : `refs/heads/main`

**Compose path** : `docker-compose.portainer.yml`

### 3.3 Variables d'environnement

Ajoutez ces variables dans la section **Environment variables** :

```env
# ⚠️ OBLIGATOIRES
CLIENT_NAME=nomduclient
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
SECRET_KEY=votre-cle-secrete-aleatoire-32-caracteres

# Optionnel - Configuration réseau
APP_PORT=8080
APP_URL=https://nomduclient.votre-domaine.com

# Optionnel - Base de données
POSTGRES_DB=erp_btp
POSTGRES_USER=erp_user

# Optionnel - Email (pour reset password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-app
SMTP_FROM=noreply@erp-btp.com

# Optionnel - GitHub (si repository privé)
GITHUB_OWNER=fvictoire59va
```

### 3.4 Activer la mise à jour automatique

1. Cochez **Enable webhook**
2. Portainer génère une URL webhook (ex: `http://portainer:9443/api/webhooks/xxx`)
3. Copiez cette URL

## 🔄 Étape 4 : Configuration du Webhook GitHub

### 4.1 Ajouter le webhook URL dans GitHub Secrets

1. Allez dans votre dépôt GitHub
2. Settings > Secrets and variables > Actions
3. Cliquez sur **New repository secret**
4. Nom : `PORTAINER_WEBHOOK_URL`
5. Valeur : L'URL webhook copiée de Portainer

### 4.2 Vérification

Le workflow GitHub Actions `.github/workflows/docker-build.yml` déclenchera automatiquement Portainer après chaque build réussi.

## 🎯 Étape 5 : Déployer la stack

1. Cliquez sur **Deploy the stack**
2. Portainer va :
   - Cloner le repository GitHub
   - Télécharger l'image depuis `ghcr.io/fvictoire59va/erp-btp:latest`
   - Créer le réseau et les volumes
   - Démarrer PostgreSQL
   - Démarrer l'application ERP

3. Attendez 30-60 secondes pour le démarrage complet

## ✅ Étape 6 : Vérification

### Vérifier les conteneurs

Dans Portainer, allez dans **Containers**. Vous devriez voir :
- ✅ `nomduclient-postgres` (healthy)
- ✅ `nomduclient-erp` (healthy)

### Accéder à l'application

Ouvrez : `http://votre-serveur:8080` (ou le port configuré)

### Vérifier les logs

Dans Portainer :
1. Cliquez sur le conteneur `nomduclient-erp`
2. Onglet **Logs**
3. Vous devriez voir : `NiceGUI ready to go on http://localhost:8080`

## 🔄 Workflow de mise à jour automatique

```
1. Developer push code to GitHub (main branch)
   ↓
2. GitHub Actions triggered
   ↓
3. Build Docker image
   ↓
4. Push to GitHub Container Registry
   ↓
5. Trigger Portainer webhook
   ↓
6. Portainer pulls new image
   ↓
7. Portainer redeploys stack
   ↓
8. Application updated (0 downtime*)
```

*Si configuré avec rolling updates

## 🏢 Déployer plusieurs clients

Pour ajouter un nouveau client, créez une nouvelle stack :

1. **Add stack** > Nom : `client-nouveauclient`
2. Même configuration repository
3. Variables d'environnement :
   ```env
   CLIENT_NAME=nouveauclient
   APP_PORT=8081  # ⚠️ Port différent pour chaque client
   POSTGRES_PASSWORD=AutreMotDePasse123!
   SECRET_KEY=autre-cle-secrete-unique
   ```
4. Deploy

Chaque client est complètement isolé avec :
- Son propre réseau Docker
- Sa propre base de données
- Ses propres volumes
- Son propre port

## 🔧 Commandes utiles

### Voir les logs d'un client
```bash
docker logs client-nomduclient-erp -f
```

### Accéder à la base de données d'un client
```bash
docker exec -it client-nomduclient-postgres psql -U erp_user -d erp_btp
```

### Sauvegarder la base de données d'un client
```bash
docker exec client-nomduclient-postgres pg_dump -U erp_user erp_btp > backup_nomduclient.sql
```

### Restaurer une sauvegarde
```bash
cat backup_nomduclient.sql | docker exec -i client-nomduclient-postgres psql -U erp_user -d erp_btp
```

## 📊 Monitoring

### Healthchecks

Les conteneurs ont des healthchecks intégrés :
- **PostgreSQL** : Vérifie que la DB est prête
- **ERP BTP** : Vérifie que l'app répond sur le port 8080

### Alertes Portainer

Configurez des alertes dans Portainer :
1. Settings > Notifications
2. Ajoutez un webhook Slack/Discord/Email
3. Créez des alertes pour :
   - Conteneur down
   - Healthcheck failed
   - Stack deployment failed

## 🔐 Sécurité

### Recommandations

1. **Mots de passe forts** : Utilisez un générateur
   ```bash
   openssl rand -base64 32
   ```

2. **HTTPS** : Utilisez un reverse proxy (Nginx/Traefik)
   ```yaml
   # Ajoutez des labels Traefik dans docker-compose.portainer.yml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.${CLIENT_NAME}.rule=Host(`${CLIENT_NAME}.domain.com`)"
     - "traefik.http.routers.${CLIENT_NAME}.tls.certresolver=letsencrypt"
   ```

3. **Backup automatique** : Configurez des sauvegardes régulières
4. **Isolation réseau** : Chaque stack a son propre réseau
5. **Secrets** : Utilisez Docker secrets pour les mots de passe sensibles

## 🆘 Dépannage

### L'image ne se télécharge pas
- Vérifiez que l'image est publique sur GitHub Packages
- Ou ajoutez les credentials dans Portainer (Registries)

### Le webhook ne fonctionne pas
- Vérifiez que `PORTAINER_WEBHOOK_URL` est bien configuré dans GitHub Secrets
- Vérifiez les logs GitHub Actions

### Le conteneur redémarre en boucle
- Vérifiez les logs : `docker logs client-nomduclient-erp`
- Vérifiez les variables d'environnement
- Vérifiez que PostgreSQL est bien démarré

### Erreur de connexion à la base de données
- Vérifiez le healthcheck de PostgreSQL
- Vérifiez le mot de passe `POSTGRES_PASSWORD`
- Attendez que PostgreSQL soit complètement démarré (30s)

## 📚 Ressources

- [Documentation Portainer](https://docs.portainer.io/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Compose](https://docs.docker.com/compose/)

## 🎉 Avantages de cette architecture

✅ **Isolation totale** : Chaque client est complètement isolé  
✅ **Mises à jour automatiques** : Push to main = déploiement automatique  
✅ **Interface graphique** : Gestion facile via Portainer  
✅ **Scalabilité** : Ajoutez autant de clients que nécessaire  
✅ **Sauvegardes faciles** : Un volume par client  
✅ **Monitoring intégré** : Healthchecks et alertes  
✅ **Zero downtime** : Rolling updates possibles  
