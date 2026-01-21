# 🛒 Configuration des Stripe Buy Buttons

## 📋 Situation Actuelle

L'application utilise maintenant le **Stripe Buy Button** qui est :
- ✅ Plus simple à maintenir
- ✅ Plus rapide à intégrer
- ✅ Géré entièrement par Stripe
- ✅ Pas besoin de créer des sessions Checkout manuellement

## 🔧 Comment Configurer les Buy Button IDs

### Étape 1: Créer un produit pour chaque plan

1. Allez sur **https://dashboard.stripe.com/products/create**
2. Cliquez sur "Create product"

#### Pour le plan Mensuel
- **Nom:** Abonnement Mensuel - ERP BTP
- **Prix:** 49€/mois
- **Durée:** Mensuelle
- Créez le produit

#### Pour le plan Annuel
- **Nom:** Abonnement Annuel - ERP BTP
- **Prix:** 499€/an
- **Durée:** Annuelle
- Créez le produit

### Étape 2: Créer les Buy Buttons

1. Allez sur **https://dashboard.stripe.com/products**
2. Pour chaque produit:
   - Cliquez dessus
   - Allez dans l'onglet **"Checkout settings"**
   - Cliquez sur **"Create buy button"**
   - Configurez les paramètres:
     - ✅ Activer "Enable checkout"
     - ✅ Redirect to success_url: `https://votre-domaine.com/payment-success`
     - ✅ Activer les paiements par carte
   - Copiez le **Buy Button ID** (commence par `buy_btn_`)

### Étape 3: Mettre à jour le code

Ouvrez le fichier `main.py` et cherchez la section "Configuration des Buy Buttons Stripe" (vers la ligne 744):

```python
buy_buttons = {
    'mensuel': {
        'button_id': 'buy_btn_mensuel_12345',  # ← Remplacez par votre ID
        'name': 'Abonnement Mensuel',
        'price': '49€/mois',
        'badge': None,
    },
    'annuel': {
        'button_id': 'buy_btn_1Ss6CFB0rlCfGOCz6fVT386J',  # ← Remplacez par votre ID
        'name': 'Abonnement Annuel',
        'price': '499€/an',
        'badge': '🏆 Meilleur rapport qualité/prix',
    }
}
```

Remplacez les `button_id` par vos IDs Stripe :
- Pour le plan mensuel: collez votre Buy Button ID pour le produit mensuel
- Pour le plan annuel: collez votre Buy Button ID pour le produit annuel

### Étape 4: Redémarrer l'application

```bash
# Arrêtez l'application (CTRL+C)
# Puis relancez-la
python main.py
```

## 🧪 Test

1. Allez à `/login`
2. Connectez-vous avec un compte dont l'abonnement est expiré
3. Vous serez redirigé vers `/renew-subscription`
4. Vous verrez les deux Buy Buttons Stripe
5. Cliquez sur un bouton pour tester le paiement

### Test Stripe

Pour tester sans débiter réellement:
- Utilisez la **carte de test Stripe**: `4242 4242 4242 4242`
- **Expiration:** Toute date future (ex: 12/26)
- **CVC:** N'importe quel 3 chiffres (ex: 123)
- **Nom:** N'importe quel nom

## 📍 Localisation des IDs

Après avoir créé les Buy Buttons, vous pouvez aussi trouver les IDs:
1. Allez sur **https://dashboard.stripe.com/products**
2. Cliquez sur le produit
3. Onglet **"Billing or Tax"**
4. Scrollez jusqu'à "Buy Button"
5. Vous verrez l'ID dans le code HTML fourni

## 🔗 Webhooks (Important pour les mises à jour BD)

Pour que les abonnements se mettent à jour automatiquement après paiement:

1. Allez sur **https://dashboard.stripe.com/webhooks**
2. Créez un endpoint:
   - **URL:** `https://votre-domaine.com/api/stripe/webhook`
   - **Événements à sélectionner:**
     - `checkout.session.completed`
     - `charge.succeeded`
3. Copiez le **Secret du webhook** dans votre `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxx
   ```

## ✅ Vérification

Après configuration, testez:
- [ ] Les Buy Buttons apparaissent sur `/renew-subscription`
- [ ] Cliquer sur un bouton ouvre Stripe Checkout
- [ ] Le paiement avec carte de test fonctionne
- [ ] Vous êtes redirigé vers `/payment-success`
- [ ] La BD se met à jour (si webhooks configurés)
- [ ] Vous pouvez vous reconnecter sans redirection

## 🚀 Avantages de cette approche

| Aspect | Avant (Session Checkout) | Après (Buy Button) |
|--------|--------------------------|-------------------|
| Création de session | ❌ Code complexe | ✅ Stripe gère |
| Maintenance | ❌ À mettre à jour | ✅ Automatique |
| Sécurité | ✅ Bonne | ✅ Meilleure |
| UX | ✅ Bonne | ✅ Plus fluide |
| Intégration | ❌ Manuelle | ✅ Clé en main |

## 📞 Support

Si vous avez des problèmes:
1. Vérifiez que les `button_id` sont corrects dans `main.py`
2. Vérifiez que les Buy Buttons sont activés dans Stripe Dashboard
3. Vérifiez les logs de l'application (`logs/`) pour les erreurs
4. Testez avec la carte Stripe `4242 4242 4242 4242`

---

**Documentation créée le:** 21 janvier 2026  
**Stripe API Version:** v3 Buy Button  
**Status:** ✅ Production Ready
