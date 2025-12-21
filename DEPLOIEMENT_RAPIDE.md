# Guide de Déploiement Rapide

## 🚀 Trois modes de déploiement

### 1. Mode ULTRA-RAPIDE (⚡ 2-3 secondes)
**Pour** : Modifications de code Python uniquement
**Commande** :
```bash
./deploy-fast.sh
```
**Ce qu'il fait** :
- Pull les modifications Git
- Redémarre le conteneur (pas de rebuild)
- ⏱️ Durée : 2-3 secondes

---

### 2. Mode INTELLIGENT (🧠 3-5 secondes ou 2 minutes)
**Pour** : Tous types de modifications
**Commande** :
```bash
./deploy-webhook.sh
```
**Ce qu'il fait** :
- Pull les modifications Git
- Détecte si `requirements.txt` ou `Dockerfile` a changé
- Si OUI → Rebuild complet (2 minutes)
- Si NON → Redémarrage simple (3-5 secondes)
- ⏱️ Durée : Variable selon les changements

---

### 3. Mode DÉVELOPPEMENT (🔥 Temps réel)
**Pour** : Développement actif avec rechargement automatique
**Commande** :
```bash
docker-compose -f docker-compose.dev.yml up -d
```
**Ce qu'il fait** :
- Monte le code Python en volume
- Recharge automatiquement à chaque modification de fichier
- Pas besoin de redémarrer !
- ⏱️ Durée : 0 seconde (automatique)

**Pour voir les logs en temps réel** :
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

**Pour revenir en mode production** :
```bash
docker-compose -f docker-compose.dev.yml down
docker-compose up -d
```

---

## 📊 Comparaison des modes

| Mode | Durée | Quand l'utiliser |
|------|-------|------------------|
| **Ultra-rapide** | 2-3s | Code Python modifié uniquement |
| **Intelligent** | 3s-2min | Toutes modifications (auto-détection) |
| **Développement** | Temps réel | Phase de développement active |

---

## 💡 Recommandations

### En développement actif :
1. Utilisez le **mode développement** avec rechargement auto
2. Modifiez votre code localement, il se met à jour instantanément

### Pour tester avant production :
1. Utilisez le **mode ultra-rapide** pour tester rapidement

### Pour déployer en production :
1. Utilisez le **mode intelligent** qui gère tout automatiquement

---

## 🔧 Workflow recommandé

```bash
# 1. Phase de développement
docker-compose -f docker-compose.dev.yml up -d
# Modifiez votre code, testez en temps réel

# 2. Test final
./deploy-fast.sh
# Testez avec la configuration de production

# 3. Push vers GitHub
git add .
git commit -m "Nouvelle fonctionnalité"
git push

# 4. GitHub Actions déploie automatiquement (si configuré)
# OU exécutez manuellement : ./deploy-webhook.sh
```

---

## 🐛 Debug

**Voir les logs** :
```bash
docker logs erp-btp -f
```

**Vérifier l'état** :
```bash
docker ps
curl http://localhost:8080
```

**Redémarrage complet forcé** :
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
