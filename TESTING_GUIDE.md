# Guide de Test - Redirection Abonnement Expiré

## 🧪 Test Complet du Flux de Paiement

Ce guide vous permettra de tester le flux complet de redirection vers le paiement Stripe lorsqu'un abonnement est expiré.

---

## ✅ Prérequis

### 1. Environment de Test

```bash
# Vérifier que les variables d'environnement sont configurées
# Dans votre fichier .env:

STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
APP_URL=http://localhost:8080

SUBSCRIPTION_DB_HOST=176.131.66.167
SUBSCRIPTION_DB_PORT=5433
SUBSCRIPTION_DB_NAME=erpbtp_clients
SUBSCRIPTION_DB_USER=postgres
SUBSCRIPTION_DB_PASSWORD=xxx
```

### 2. Données de Test

Vous devez avoir:
- Un utilisateur créé dans la base locale avec credentials connus
- Cet utilisateur doit exister dans la table `abonnements` de la BD externe
- L'abonnement de cet utilisateur doit avoir:
  - `date_fin_essai` < aujourd'hui (expiré)
  - `statut` = 'actif' ou 'suspendu'

#### Créer un utilisateur de test

```sql
-- Dans votre base locale (base ERP BTP)
-- Créer un utilisateur de test si nécessaire
-- Via l'interface d'inscription de l'app
```

#### Configurer l'abonnement expiré en BD externe

```sql
-- Dans la BD d'abonnements (176.131.66.167:5433)
-- Vérifier/créer un abonnement expiré

INSERT INTO abonnements (client_id, date_fin_essai, statut)
VALUES ('test@example.com', '2025-01-01', 'actif')
ON CONFLICT (client_id) DO UPDATE
SET date_fin_essai = '2025-01-01';

-- Vérifier
SELECT * FROM abonnements WHERE client_id = 'test@example.com';
```

---

## 🧪 Scénarios de Test

### Scénario 1: Login → Redirection Abonnement Expiré

#### Étape 1: Accéder à la page de login
```
1. Ouvrir: http://localhost:8080/login
2. Vérifier que le formulaire de login est visible
```

#### Étape 2: Entrer les identifiants expirés
```
1. Nom d'utilisateur: test (ou username du compte expiré)
2. Mot de passe: xxx (le mot de passe du compte)
3. Cliquer "Se connecter"
```

#### Étape 3: Vérifier la redirection
```
ATTENDU:
- URL devient: /renew-subscription?client_id=test@example.com
- Page avec titre: "⚠️ Votre abonnement a expiré"
- Deux plans visibles: Mensuel (49€/mois) et Annuel (499€/an)

VÉRIFICATION:
- Pas d'erreur dans la console du navigateur
- Pas d'erreur dans les logs serveur
```

#### Étape 4: Vérifier les logs
```bash
# Dans les logs serveur (sortie stdout ou logs/...)
# Chercher:

"Login blocked for test: Votre abonnement a expiré..."
```

---

### Scénario 2: Sélection du Plan

#### Étape 1: Sélectionner le plan Mensuel
```
1. Sur la page /renew-subscription
2. Cliquer sur la card "Mensuel"
3. VÉRIFICATION:
   - Card Mensuel: border-blue-500, background-blue-50
   - Card Annuel: border-transparent, bg-white
```

#### Étape 2: Changer vers le plan Annuel
```
1. Cliquer sur la card "Annuel"
2. VÉRIFICATION:
   - Card Annuel: border-blue-500, background-blue-50
   - Card Mensuel: border-transparent, bg-white
```

#### Étape 3: Cliquer "Procéder au paiement"
```
1. Avec un plan sélectionné, cliquer le bouton vert
2. VÉRIFICATION:
   - Redirection vers: https://checkout.stripe.com/pay/...
   - Page Stripe Checkout visible
   - Email pré-rempli: client_id@example.com
```

---

### Scénario 3: Paiement Stripe

#### Étape 1: Remplir le formulaire Stripe
```
Sur la page Stripe Checkout:

Email: (déjà pré-rempli)
Numéro de carte: 4242 4242 4242 4242 (carte de test Stripe)
Exp: 12/26 (date future)
CVC: 123 (n'importe quel 3 chiffres)
Nom: Test User
Pays: France
Code postal: 75000
```

#### Étape 2: Compléter le paiement
```
1. Cliquer "Payer" ou le bouton de soumission
2. Attendre 1-2 secondes pour traitement
3. ATTENDU:
   - Page de succès Stripe temporaire
   - Redirection automatique vers /payment-success (5-10 secondes)
```

#### Étape 3: Vérifier la page de succès
```
ATTENDU:
- URL: /payment-success?session_id=cs_xxx
- Titre: "🎉 Paiement réussi !"
- Message: "Merci pour votre achat"
- Détails du plan (Annuel, 365 jours, montant)
- Bouton: "Accéder à l'application"

VÉRIFICATION:
- Pas d'erreur dans la console
- Logs serveur: "Webhook received: checkout.session.completed"
```

---

### Scénario 4: Vérification de la BD

#### Étape 1: Vérifier la mise à jour en BD

```sql
-- Dans la BD d'abonnements (176.131.66.167:5433)

SELECT id, client_id, date_fin_essai, statut, date_modification 
FROM abonnements 
WHERE client_id = 'test@example.com';

-- RÉSULTAT ATTENDU:
-- id: (même id)
-- client_id: test@example.com
-- date_fin_essai: 2026-01-21 (aujourd'hui + 365 jours si annuel)
--                ou 2026-02-20 (aujourd'hui + 30 jours si mensuel)
-- statut: actif
-- date_modification: timestamp récent
```

#### Étape 2: Vérifier que la date a changé
```sql
-- Comparer avec la date précédente
-- Elle doit être aujourd'hui + 30 jours (mensuel) ou + 365 jours (annuel)

SELECT CURRENT_DATE + INTERVAL '30 days' as date_fin_mensuel;
SELECT CURRENT_DATE + INTERVAL '365 days' as date_fin_annuel;
```

---

### Scénario 5: Reconnexion Après Paiement

#### Étape 1: Se déconnecter
```
1. Aller sur /login
2. Fermer la session (log out) si nécessaire
```

#### Étape 2: Se reconnecter avec les mêmes identifiants
```
1. Ouvrir: http://localhost:8080/login
2. Entrer:
   - Nom d'utilisateur: test
   - Mot de passe: xxx
3. Cliquer "Se connecter"
```

#### Étape 3: Vérifier la connexion réussie
```
ATTENDU:
- PAS de redirection vers /renew-subscription
- Connexion réussie
- Accès à l'application (dashboard, etc.)

VÉRIFICATION:
- Pas d'erreur dans la console
- Logs serveur: "User logged in: test"
```

---

## 🚨 Dépannage

### Problème: Pas de redirection vers /renew-subscription

**Cause possible 1:** Abonnement pas expiré en BD
```sql
-- Vérifier en BD
SELECT * FROM abonnements WHERE client_id = 'test@example.com';

-- Si date_fin_essai >= aujourd'hui, ce n'est pas expiré
-- Modifier:
UPDATE abonnements 
SET date_fin_essai = '2025-01-01' 
WHERE client_id = 'test@example.com';
```

**Cause possible 2:** BD d'abonnements non accessible
```
- Vérifier les variables d'environnement SUBSCRIPTION_DB_*
- Vérifier la connexion à 176.131.66.167:5433
- Vérifier les credentials PostgreSQL
- Logs serveur: "Erreur de connexion à la base des abonnements"
```

**Cause possible 3:** CLIENT_ID non configuré
```
- Vérifier que CLIENT_ID est défini dans .env
- Ou que user.email est configuré
```

### Problème: Redirection Stripe ne fonctionne pas

**Cause possible 1:** Clés Stripe invalides
```
- Vérifier STRIPE_SECRET_KEY commence par sk_test_ ou sk_live_
- Vérifier STRIPE_PUBLISHABLE_KEY commence par pk_test_ ou pk_live_
- Logs serveur: "Stripe n'est pas configuré"
```

**Cause possible 2:** APP_URL non défini
```
- Vérifier que APP_URL est dans .env
- Exemples: http://localhost:8080 ou https://votre-domaine.com
```

**Cause possible 3:** Session Stripe invalide
```
- Vérifier que client_id est un email valide
- Vérifier que le plan sélectionné est 'mensuel' ou 'annuel'
- Logs serveur: "create_checkout_session() error"
```

### Problème: Webhook non reçu / BD non mise à jour

**Cause possible 1:** STRIPE_WEBHOOK_SECRET non configuré
```
- Vérifier dans .env
- Récupérer depuis Stripe Dashboard > Developers > Webhooks
```

**Cause possible 2:** Endpoint webhook non configuré
```
- Aller sur https://dashboard.stripe.com/webhooks
- Vérifier que l'endpoint existe
- URL: https://votre-domaine.com/api/stripe/webhook
- Événement: checkout.session.completed
```

**Cause possible 3:** Webhook URL incorrecte
```
- APP_URL doit être publiquement accessible
- Pas localhost ni 127.0.0.1 en production
- Vérifier dans Stripe Dashboard que l'endpoint est "Enabled"
```

### Problème: Page de succès ne s'affiche pas

**Cause possible:** Redirection ne fonctionne pas
```
1. Vérifier que la page /payment-success existe
2. Vérifier l'URL dans les logs: "redirect_url"
3. Ouvrir manuellement: /payment-success?session_id=xxx
```

---

## 📊 Checklist de Test Complète

### ✅ Avant de Tester
- [ ] Variables d'environnement Stripe configurées
- [ ] Variables d'environnement BD configurées
- [ ] Utilisateur de test créé
- [ ] Abonnement expiré en BD externe
- [ ] Application démarrée sans erreurs

### ✅ Test du Flux
- [ ] Login redirige vers /renew-subscription
- [ ] Plans affichés correctement
- [ ] Sélection de plan fonctionne (couleur change)
- [ ] Clic "Procéder" redirige vers Stripe
- [ ] Formulaire Stripe pré-rempli
- [ ] Paiement accepté par Stripe
- [ ] Redirection vers /payment-success
- [ ] Page de succès affichée

### ✅ Vérifications BD
- [ ] Abonnement mis à jour en BD
- [ ] date_fin_essai correcte (30 ou 365 jours plus tard)
- [ ] statut = 'actif'
- [ ] date_modification = timestamp récent

### ✅ Test de Reconnexion
- [ ] Reconnexion sans redirection vers /renew-subscription
- [ ] Accès à l'application réussi
- [ ] Aucune erreur d'authentification

---

## 🎯 Résultats Attendus

| Test | Résultat Attendu | Status |
|------|------------------|--------|
| Login abonnement expiré | Redirection `/renew-subscription` | ✅ |
| Sélection plan | Card change couleur | ✅ |
| Clic paiement | Redirection Stripe | ✅ |
| Paiement réussi | Page `/payment-success` | ✅ |
| BD mise à jour | `date_fin_essai` et `statut` corrects | ✅ |
| Reconnexion | Connexion réussie, pas de redirection | ✅ |

---

## 📝 Notes importantes

1. **Les logs sont essentiels:** Consultez la sortie serveur pour voir le flux complet
2. **Cartes de test Stripe:** Utilisez toujours `4242 4242 4242 4242` pour les tests
3. **Dates:** Elles doivent être au format DATE (YYYY-MM-DD), pas DATETIME
4. **Webhook:** Peut prendre quelques secondes, ne pas fermer la page trop vite
5. **Tests multiples:** Vous pouvez tester plusieurs fois avec le même user en changeant la date d'expiration

---

## 📞 Support Technique

Si vous rencontrez des problèmes:

1. **Consulter les logs:**
   ```bash
   tail -f logs/*.log
   ```

2. **Vérifier la BD:**
   ```sql
   SELECT * FROM abonnements WHERE client_id = 'test@example.com';
   ```

3. **Tester l'API Stripe:**
   ```bash
   curl -X POST https://api.stripe.com/v1/checkout/sessions \
     -H "Authorization: Bearer sk_test_xxx" \
     -d "payment_method_types[]=card" \
     -d "line_items[0][price_data][currency]=eur" \
     -d "line_items[0][price_data][unit_amount]=4900" \
     -d "line_items[0][price_data][product_data][name]=Abonnement" \
     -d "line_items[0][quantity]=1" \
     -d "mode=payment" \
     -d "success_url=http://localhost:8080/payment-success" \
     -d "cancel_url=http://localhost:8080/renew-subscription"
   ```

4. **Consulter la documentation:**
   - `SUBSCRIPTION_PAYMENT_FLOW.md` - Flux complet
   - `IMPLEMENTATION_SUMMARY.md` - Changements effectués
   - `STRIPE_INTEGRATION.md` - Configuration Stripe
   - `SUBSCRIPTION_MANAGEMENT.md` - Gestion des abonnements
