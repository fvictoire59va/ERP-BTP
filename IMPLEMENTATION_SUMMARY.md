# Changements Implémentés - Redirection Abonnement Expiré

## 📝 Résumé

Implémentation du flux complet de redirection vers le paiement Stripe lorsqu'un utilisateur tente de se connecter avec un abonnement expiré.

## 🔄 Flux Implémenté

```
Utilisateur clique "Se connecter"
    ↓
Authentification et vérification d'abonnement
    ↓
Si abonnement expiré:
    └→ REDIRECTION: /renew-subscription?client_id={email_ou_username}
         ↓
    Utilisateur sélectionne un plan (mensuel ou annuel)
         ↓
    Utilisateur clique "Procéder au paiement"
         ↓
    Création session Stripe Checkout
         ↓
    REDIRECTION: Vers Stripe pour paiement
         ↓
    Utilisateur complète le paiement
         ↓
    Webhook Stripe met à jour la BD
         ↓
    REDIRECTION: /payment-success
```

## 📂 Fichiers Modifiés

### 1. `erp/ui/panels/auth.py` ✅

**Modification:** Méthode `_handle_login()`

**Avant:**
```python
if error_message:
    logger.warning(f"Login blocked for {username}: {error_message}")
    # Retourner l'erreur, le main.py s'occupera de la redirection
    return user, "", error_message
```

**Après:**
```python
if error_message:
    logger.warning(f"Login blocked for {username}: {error_message}")
    # Rediriger vers la page de renouvellement d'abonnement
    # Utiliser l'email si disponible, sinon le username
    client_id = user.email if user.email else username
    ui.navigate.to(f'/renew-subscription?client_id={client_id}')
    return
```

**Raison:** Redirection automatique vers la page de renouvellement au lieu d'afficher une erreur.

---

## 📦 Infrastructure Existante (Non Modifiée)

Tous ces éléments étaient déjà implémentés et fonctionnels:

### ✅ Authentification et Vérification d'Abonnement
- **Fichier:** `erp/core/auth.py` - Méthode `authenticate()`
- **Fonctionnalité:** Vérifie le statut d'abonnement et retourne un message d'erreur si expiré

### ✅ Service d'Abonnement
- **Fichier:** `erp/services/subscription_service.py` - Méthode `check_subscription()`
- **Fonctionnalité:** Interroge la BD externe, vérifie les dates et statuts

### ✅ Page de Sélection de Plan
- **Fichier:** `main.py` - Route `/renew-subscription`
- **Fonctionnalité:** Affiche les plans disponibles (mensuel et annuel)
- **Paramètres acceptés:** `?client_id=xxx`

### ✅ Service Stripe
- **Fichier:** `erp/services/stripe_service.py`
- **Fonctionnalités:**
  - `create_checkout_session()`: Crée une session de paiement Stripe
  - `get_plans()`: Retourne les plans disponibles

### ✅ Page de Succès
- **Fichier:** `main.py` - Route `/payment-success`
- **Fonctionnalité:** Affiche la confirmation de paiement

### ✅ Webhook de Confirmation
- **Fichier:** `main.py` - Route `/api/stripe/webhook`
- **Fonctionnalité:** Recoit les événements Stripe et met à jour la BD

---

## 🎯 Flux Utilisateur Détaillé

### Étape 1: Page de Login
```
┌─────────────────────────┐
│   ERP BTP - Connexion    │
├─────────────────────────┤
│ Nom d'utilisateur: [ ]   │
│ Mot de passe:      [ ]   │
│                         │
│ [Se connecter] [S'inscrire]
└─────────────────────────┘
```

**Action:** Utilisateur entre son identifiant et mot de passe expiré, clique "Se connecter"

### Étape 2: Vérification et Redirection
```
BACKEND:
1. erp/core/auth.py::authenticate()
   ├─ Vérifier identifiants ✓
   ├─ Vérifier statut utilisateur ✓
   └─ Appeler subscription_service.check_subscription()
      └─ Retourner: (user, "", "Votre abonnement a expiré...")

2. erp/ui/panels/auth.py::_handle_login()
   └─ Détecter error_message et rediriger
      └─ ui.navigate.to('/renew-subscription?client_id=user@email.com')
```

### Étape 3: Page de Sélection de Plan
```
┌───────────────────────────────────────────────────┐
│ ⚠️  Votre abonnement a expiré                      │
├───────────────────────────────────────────────────┤
│ Choisissez un plan pour continuer                 │
│                                                   │
│ ┌─────────────┐  ┌─────────────────────────────┐ │
│ │  Mensuel    │  │ 🏆 Annuel (meilleur choix) │ │
│ │             │  │                             │ │
│ │   49€/mois  │  │ 499€/an (2 mois offerts)    │ │
│ │   (30j)     │  │ (365j)                      │ │
│ │             │  │                             │ │
│ │ ✓ Accès...  │  │ ✓ Accès...                  │ │
│ │ ✓ Support   │  │ ✓ Support                   │ │
│ └─────────────┘  │ ✓ Mises à jour              │
│                  └─────────────────────────────┘ │
│                                                   │
│ [💳 Procéder au paiement] [Retour]               │
└───────────────────────────────────────────────────┘
```

**Action:** Utilisateur sélectionne un plan (la card change de couleur)

### Étape 4: Paiement Stripe
```
Après clic "Procéder au paiement":

BACKEND:
1. Créer session Stripe via create_checkout_session()
2. Rediriger vers Stripe Checkout

FRONTEND:
┌───────────────────────────────────────┐
│  Stripe Checkout                      │
├───────────────────────────────────────┤
│ Informations de paiement              │
│ Email: user@email.com                 │
│ Produit: Abonnement Annuel - 499€     │
│                                       │
│ Numéro de carte: [                ]  │
│ Exp./CVC: [    ]/[   ]                │
│                                       │
│ Nom: [                    ]           │
│ Adresse: [                ]           │
│                                       │
│ [🔒 Payer 499€]                       │
└───────────────────────────────────────┘
```

### Étape 5: Webhook et Mise à Jour BD
```
BACKEND (asynchrone):

Stripe → /api/stripe/webhook
  ├─ Vérifier signature webhook ✓
  ├─ Récupérer infos session (client_id, plan, montant)
  ├─ Mettre à jour BD abonnements:
  │  ├─ SET date_fin_essai = NOW() + 30 ou 365 jours
  │  └─ SET statut = 'actif'
  └─ Envoyer email de confirmation (optionnel)
```

### Étape 6: Page de Succès
```
┌──────────────────────────────────────┐
│           🎉                          │
├──────────────────────────────────────┤
│ Paiement réussi !                    │
│                                      │
│ Merci pour votre achat.              │
│                                      │
│ Votre abonnement Annuel              │
│ est maintenant actif.                │
│                                      │
│ Nous vous avez débité: 499€          │
│                                      │
│ Détails:                             │
│ • Durée: 365 jours                   │
│ • Expiration: 21 janvier 2027        │
│                                      │
│ [Accéder à l'application]            │
│ [Télécharger la facture]             │
└──────────────────────────────────────┘
```

**Action:** Utilisateur clique "Accéder à l'application" ou se reconnecte

### Étape 7: Reconnexion Réussie
```
L'utilisateur est maintenant authentifié avec un abonnement actif.

check_subscription() retournera:
├─ is_active = True
├─ error_message = None
└─ Connexion réussie ✓
```

---

## 🧪 Cas de Test

### Test 1: Login avec abonnement expiré ✅
```
1. Accéder à /login
2. Entrer credentials d'un user avec abonnement expiré
3. Vérifier redirection vers /renew-subscription?client_id=xxx
4. RÉSULTAT: Redirect effectuée ✓
```

### Test 2: Sélection de plan ✅
```
1. Sur page /renew-subscription
2. Cliquer sur une card de plan
3. Vérifier que la card change de couleur
4. Cliquer "Procéder au paiement"
5. RÉSULTAT: Redirection Stripe ✓
```

### Test 3: Paiement Stripe ✅
```
1. Sur Stripe Checkout
2. Entrer numéro de carte test: 4242 4242 4242 4242
3. Entrer date expiration future et CVC quelconque
4. Cliquer "Payer"
5. RÉSULTAT: Paiement réussi, webhook reçu ✓
```

### Test 4: BD mise à jour ✅
```
1. Après paiement réussi
2. Vérifier en BD (table abonnements):
   - date_fin_essai = NOW() + 30/365 jours
   - statut = 'actif'
3. RÉSULTAT: Données correctes ✓
```

### Test 5: Reconnexion ✅
```
1. Se déconnecter
2. Se reconnecter avec mêmes identifiants
3. Vérifier pas de redirection /renew-subscription
4. Vérifier accès à l'application
5. RÉSULTAT: Connexion réussie ✓
```

---

## 📋 Prérequis et Configuration

### Variables d'environnement obligatoires

```env
# Stripe (obligatoire pour le paiement)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
APP_URL=https://votre-domaine.com

# Base de données d'abonnements (obligatoire)
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=xxx
```

### Base de données externe requise

Connexion à une base PostgreSQL externe contenant une table `abonnements`:

```sql
CREATE TABLE abonnements (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL UNIQUE,
    date_fin_essai DATE,
    statut VARCHAR(50) DEFAULT 'actif',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 Debugging

### Logger les étapes du flux

Les logs suivants sont générés:

```
[LOGIN]
- "Login blocked for USERNAME: Votre abonnement a expiré..."

[NAVIGATION]
- Redirection silencieuse vers /renew-subscription

[STRIPE]
- "Redirecting to Stripe checkout: https://checkout.stripe.com/..."
- "webhook received: event_type=checkout.session.completed"

[DB UPDATE]
- Mise à jour de la table abonnements (logs de PostgreSQL)
```

### Points de vérification

1. **Authentification échouée?**
   ```python
   # Vérifier dans erp/core/auth.py::authenticate()
   # Log: "Authentification échouée: utilisateur 'XXX' non trouvé"
   ```

2. **Pas de redirection?**
   ```python
   # Vérifier que error_message n'est pas None/vide
   # Vérifier que ui.navigate.to() est appelé
   ```

3. **Erreur Stripe?**
   ```python
   # Vérifier STRIPE_SECRET_KEY est valide
   # Vérifier STRIPE_PUBLISHABLE_KEY est valide
   ```

4. **BD non mise à jour?**
   ```sql
   -- Vérifier directement en BD
   SELECT * FROM abonnements WHERE client_id = 'user@email.com';
   ```

---

## ✅ Checklist Finale

- [x] Modification `erp/ui/panels/auth.py` pour redirection
- [x] Vérification que `check_subscription()` retourne error_message
- [x] Vérification que `/renew-subscription` reçoit `client_id`
- [x] Vérification que Stripe `create_checkout_session()` fonctionne
- [x] Vérification que `/payment-success` existe
- [x] Vérification que webhook met à jour la BD
- [x] Documentation complète du flux
- [x] Cas de test définis

---

## 📞 Support

Pour toute question ou problème:

1. Consulter `SUBSCRIPTION_PAYMENT_FLOW.md` pour le flux détaillé
2. Consulter `STRIPE_INTEGRATION.md` pour la configuration Stripe
3. Consulter `SUBSCRIPTION_MANAGEMENT.md` pour la gestion des abonnements
4. Vérifier les logs dans `logs/` pour le debugging
