# Flux de Paiement d'Abonnement Expiré

## 📋 Vue d'ensemble

Ce document décrit le flux complet lorsqu'un utilisateur tente de se connecter avec un abonnement expiré.

## 🔄 Flux d'exécution

### 1. Tentative de connexion
L'utilisateur clique sur "Se connecter" avec son identifiant et mot de passe.

**Fichier concerné:** `erp/ui/panels/auth.py` - Méthode `_handle_login()`

```python
# L'utilisateur remplit le formulaire de login
# - Nom d'utilisateur
# - Mot de passe
```

### 2. Authentification et vérification d'abonnement
L'authentificateur valide les identifiants puis vérifie l'état de l'abonnement.

**Fichier concerné:** `erp/core/auth.py` - Méthode `authenticate()`

```
Étapes:
1. Vérifier les identifiants (username/password)
2. Vérifier si l'utilisateur est actif
3. Appeler le service d'abonnement pour vérifier l'état
   - Récupérer l'abonnement depuis la BD externe
   - Vérifier la date d'expiration
   - Vérifier le statut (actif/suspendu)
4. Retourner un tuple (User, session_id, error_message)
   - Si abonnement OK: error_message = None
   - Si abonnement expiré: error_message = "Votre abonnement a expiré..."
```

**Fichier concerné:** `erp/services/subscription_service.py` - Méthode `check_subscription()`

### 3. Redirection vers la page de paiement
Si l'abonnement est expiré, l'utilisateur est redirigé vers la page de renouvellement.

**Fichier concerné:** `erp/ui/panels/auth.py` - Méthode `_handle_login()`

```python
if error_message:
    # Récupérer l'email ou le username
    client_id = user.email if user.email else username
    
    # Rediriger vers la page de renouvellement
    ui.navigate.to(f'/renew-subscription?client_id={client_id}')
    return
```

### 4. Page de sélection du plan
L'utilisateur arrive sur la page `/renew-subscription` et sélectionne un plan.

**Fichier concerné:** `main.py` - Route `/renew-subscription`

**Plans disponibles:**
- **Mensuel:** 49€/mois (30 jours)
- **Annuel:** 499€/an (365 jours) - Meilleur rapport qualité/prix

### 5. Création de la session de paiement Stripe
L'utilisateur clique sur "Procéder au paiement".

**Fichier concerné:** `erp/services/stripe_service.py` - Méthode `create_checkout_session()`

```
Étapes:
1. Valider la sélection du plan
2. Appeler l'API Stripe pour créer une session de checkout
3. Recevoir l'URL de redirection
4. Rediriger l'utilisateur vers Stripe Checkout
```

### 6. Paiement Stripe
L'utilisateur complète le paiement sur la plateforme Stripe.

**Flux Stripe Checkout:**
1. L'utilisateur entre ses informations de carte
2. Stripe valide le paiement
3. Stripe envoie un webhook de confirmation

### 7. Webhook de confirmation
Stripe envoie un événement `checkout.session.completed` à votre serveur.

**Fichier concerné:** `main.py` - Route `/api/stripe/webhook`

```
Étapes:
1. Vérifier la signature du webhook
2. Récupérer les informations de la session Stripe
3. Mettre à jour la date d'expiration dans la BD des abonnements
4. Mettre à jour le statut à "actif"
```

### 8. Page de succès
L'utilisateur est redirigé vers la page de confirmation de paiement.

**Fichier concerné:** `main.py` - Route `/payment-success`

```
Affichage:
- Message de confirmation
- Informations sur l'abonnement
- Bouton pour accéder à l'application
```

---

## 🗂️ Fichiers impliqués

| Fichier | Rôle | Méthode clé |
|---------|------|-------------|
| `erp/ui/panels/auth.py` | Interface de login | `_handle_login()` |
| `erp/core/auth.py` | Authentification | `authenticate()` |
| `erp/services/subscription_service.py` | Vérification d'abonnement | `check_subscription()` |
| `erp/services/stripe_service.py` | Paiement Stripe | `create_checkout_session()` |
| `main.py` | Pages et webhooks | `/renew-subscription`, `/payment-success`, `/api/stripe/webhook` |

---

## 🧪 Test du flux complet

### Prérequis
1. Configurer les variables d'environnement Stripe:
   ```env
   STRIPE_SECRET_KEY=sk_test_xxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   ```

2. Configurer les variables d'environnement de la BD d'abonnements:
   ```env
   SUBSCRIPTION_DB_HOST=176.131.66.167
   SUBSCRIPTION_DB_PORT=5433
   SUBSCRIPTION_DB_NAME=erpbtp_clients
   SUBSCRIPTION_DB_USER=postgres
   SUBSCRIPTION_DB_PASSWORD=xxx
   ```

### Étapes de test
1. **Login avec abonnement expiré:**
   - Accéder à la page de login
   - Entrer un user avec abonnement expiré
   - Vérifier la redirection vers `/renew-subscription`

2. **Sélection du plan:**
   - Sélectionner un plan (mensuel ou annuel)
   - Vérifier que le plan est bien sélectionné (couleur du card change)
   - Cliquer sur "Procéder au paiement"

3. **Paiement Stripe:**
   - Être redirigé vers Stripe Checkout
   - Utiliser une carte de test Stripe
   - Compléter le paiement

4. **Redirection et mise à jour:**
   - Être redirigé vers `/payment-success`
   - Vérifier que la BD est mise à jour (nouvelle date d'expiration)
   - Vérifier que le statut est "actif"

5. **Nouvelle connexion:**
   - Se déconnecter
   - Se reconnecter avec les mêmes identifiants
   - Vérifier que la connexion est réussie

---

## 📊 Diagramme de flux

```
┌─────────────────────────────────────────────────────────────────┐
│ PAGE LOGIN                                                       │
│ - Saisir username/password                                       │
│ - Cliquer "Se connecter"                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AUTHENTIFICATION (erp/core/auth.py)                              │
│ - Vérifier identifiants ✓                                        │
│ - Vérifier statut utilisateur ✓                                  │
│ - Appeler check_subscription() du service                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
            Abonnement OK      Abonnement expiré
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ REDIRECTION                           │
                    │    │ → /renew-subscription?client_id=xxx   │
                    │    └──────────────────────────────────────┘
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ PAGE SÉLECTION PLAN                   │
                    │    │ - Afficher plans (mensuel/annuel)     │
                    │    │ - Utilisateur sélectionne un plan     │
                    │    │ - Cliquer "Procéder au paiement"     │
                    │    └──────────────────────────────────────┘
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ CRÉATION SESSION STRIPE               │
                    │    │ - Appeler create_checkout_session()   │
                    │    │ - Recevoir checkout URL               │
                    │    │ - Rediriger vers Stripe               │
                    │    └──────────────────────────────────────┘
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ PAIEMENT STRIPE                       │
                    │    │ - Utilisateur entre infos carte       │
                    │    │ - Stripe traite le paiement           │
                    │    │ - Envoie webhook de confirmation      │
                    │    └──────────────────────────────────────┘
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ WEBHOOK /api/stripe/webhook           │
                    │    │ - Vérifier signature                  │
                    │    │ - Mettre à jour BD abonnements        │
                    │    │ - Changer statut → "actif"            │
                    │    └──────────────────────────────────────┘
                    │                 │
                    │                 ▼
                    │    ┌──────────────────────────────────────┐
                    │    │ PAGE SUCCÈS                           │
                    │    │ → /payment-success                    │
                    │    │ - Afficher confirmation               │
                    │    │ - Bouton accès application            │
                    │    └──────────────────────────────────────┘
                    │
                    └───────────────┬─────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────────┐
                    │ ACCÈS À L'APPLICATION                 │
                    │ Utilisateur connecté avec             │
                    │ abonnement valide                     │
                    └──────────────────────────────────────┘
```

---

## 🔍 Détails techniques

### Variables d'environnement nécessaires

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_xxx          # Clé secrète Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_xxx     # Clé publique Stripe
STRIPE_WEBHOOK_SECRET=whsec_xxx        # Secret webhook Stripe
APP_URL=https://votre-domaine.com      # URL de votre application

# Base de données des abonnements
SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=xxx
```

### Structure de la table abonnements

```sql
CREATE TABLE abonnements (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    date_fin_essai DATE,
    statut VARCHAR(50) DEFAULT 'actif',  -- 'actif' ou 'suspendu'
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Codes de statut possibles
- `'actif'`: Abonnement valide
- `'suspendu'`: Abonnement expiré ou révoqué

---

## 🚨 Gestion d'erreurs

### Erreurs possibles et résolutions

| Erreur | Cause | Solution |
|--------|-------|----------|
| "STRIPE_SECRET_KEY non configuré" | Variable d'environnement manquante | Configurer la variable dans `.env` |
| "Aucun abonnement trouvé" | Client_id n'existe pas en BD | Vérifier l'email utilisateur |
| "Erreur de connexion à la BD" | Paramètres de connexion incorrects | Vérifier SUBSCRIPTION_DB_* |
| "Session Stripe non créée" | Clés Stripe invalides | Vérifier les clés API Stripe |

---

## ✅ Checklist de déploiement

- [ ] Configurer STRIPE_SECRET_KEY
- [ ] Configurer STRIPE_PUBLISHABLE_KEY
- [ ] Configurer STRIPE_WEBHOOK_SECRET
- [ ] Configurer APP_URL
- [ ] Configurer SUBSCRIPTION_DB_*
- [ ] Configurer webhooks Stripe (URL: `{APP_URL}/api/stripe/webhook`)
- [ ] Tester avec un utilisateur ayant abonnement expiré
- [ ] Tester un paiement avec une carte de test Stripe
- [ ] Vérifier la mise à jour de la BD après paiement
- [ ] Vérifier que la reconnexion fonctionne après paiement
