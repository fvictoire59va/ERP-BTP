# Intégration Stripe - ERP BTP

Ce document décrit l'intégration du système de paiement Stripe dans l'application ERP BTP.

## Vue d'ensemble

L'intégration Stripe permet de :
- Proposer des plans d'abonnement (mensuel et annuel)
- Gérer les paiements en ligne de manière sécurisée
- Renouveler automatiquement les abonnements expirés
- Recevoir des notifications webhook pour les événements de paiement

## Plans disponibles

| Plan | Prix | Durée | Caractéristiques |
|------|------|-------|------------------|
| Mensuel | 49€/mois | 30 jours | Accès complet, Support prioritaire |
| Annuel | 499€/an | 365 jours | Accès complet, Support prioritaire, 2 mois offerts |

## Configuration

### Variables d'environnement requises

```bash
# Clés API Stripe
STRIPE_SECRET_KEY=sk_test_xxx      # Clé secrète (sk_live_ en production)
STRIPE_PUBLISHABLE_KEY=pk_test_xxx # Clé publique (pk_live_ en production)
STRIPE_WEBHOOK_SECRET=whsec_xxx    # Secret pour valider les webhooks

# URL de l'application
APP_URL=https://votre-domaine.com
```

### Configuration dans Portainer

1. Accédez à votre stack ERP BTP dans Portainer
2. Ajoutez les variables d'environnement ci-dessus
3. Redéployez le conteneur

## Architecture

### Fichiers principaux

```
erp/
├── services/
│   └── stripe_service.py    # Service Stripe (création sessions, webhooks)
├── ...
main.py                       # Endpoints API et pages de paiement
tests/
└── test_stripe_payment.py   # Tests du système de paiement
```

### Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/stripe/create-checkout-session` | Crée une session de paiement |
| GET | `/api/stripe/plans` | Retourne les plans disponibles |
| GET | `/api/stripe/config` | Retourne la configuration Stripe |
| POST | `/api/stripe/webhook` | Reçoit les événements Stripe |

### Pages

| URL | Description |
|-----|-------------|
| `/renew-subscription` | Page de choix du plan et paiement |
| `/payment-success` | Page de confirmation après paiement réussi |
| `/payment-cancelled` | Page affichée si paiement annulé |
| `/pricing` | Page publique des tarifs |

## Flux de paiement

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐     ┌─────────────┐
│ Utilisateur │────►│ Choix du    │────►│ Checkout  │────►│ Paiement    │
│ (login)     │     │ plan        │     │ Stripe    │     │ réussi      │
└─────────────┘     └──────────────┘     └───────────┘     └─────────────┘
                          │                    │                  │
                          │                    │                  ▼
                          │                    │          ┌─────────────┐
                          │                    └─────────►│ Webhook     │
                          │                               │ (update DB) │
                          │                               └─────────────┘
                          ▼
                    ┌──────────────┐
                    │ Annulation   │
                    └──────────────┘
```

## Webhooks

### Configuration sur Stripe Dashboard

1. Allez sur [Stripe Dashboard > Developers > Webhooks](https://dashboard.stripe.com/webhooks)
2. Cliquez sur "Add endpoint"
3. URL: `https://votre-domaine.com/api/stripe/webhook`
4. Événements à écouter:
   - `checkout.session.completed`
5. Copiez le "Signing secret" dans `STRIPE_WEBHOOK_SECRET`

### Événements traités

| Événement | Action |
|-----------|--------|
| `checkout.session.completed` | Met à jour l'abonnement dans la DB |

## Sécurité

- Les paiements sont traités entièrement par Stripe
- Aucune donnée de carte n'est stockée sur nos serveurs
- Les webhooks sont vérifiés via signature cryptographique
- Communication HTTPS obligatoire en production

## Tests

### Exécuter les tests unitaires

```bash
cd "d:\PROJETS\ERP BTP"
python -m pytest tests/test_stripe_payment.py -v
```

### Test interactif

```bash
python tests/test_stripe_payment.py --interactive
```

### Cartes de test

| Numéro | Résultat |
|--------|----------|
| 4242 4242 4242 4242 | Paiement réussi |
| 4000 0000 0000 0002 | Carte déclinée |
| 4000 0025 0000 3155 | 3D Secure requis |

## Dépannage

### Le paiement échoue

1. Vérifiez que `STRIPE_SECRET_KEY` est correct
2. Vérifiez les logs dans Stripe Dashboard > Developers > Logs
3. En mode test, utilisez les cartes de test ci-dessus

### Les webhooks ne fonctionnent pas

1. Vérifiez que l'URL du webhook est accessible depuis Internet
2. Vérifiez que `STRIPE_WEBHOOK_SECRET` correspond au secret affiché sur Stripe
3. Consultez les logs webhook dans Stripe Dashboard

### L'abonnement n'est pas mis à jour

1. Vérifiez la connexion à la base de données des abonnements
2. Consultez les logs de l'application
3. Vérifiez que le `client_id` est correct dans les metadata

## Monitoring

### Dashboard Stripe

- [Paiements](https://dashboard.stripe.com/payments) - Historique des transactions
- [Webhooks](https://dashboard.stripe.com/webhooks) - État des webhooks
- [Logs](https://dashboard.stripe.com/developers/logs) - Logs API détaillés

### Logs application

Les événements Stripe sont loggés avec le préfixe `stripe_service`:

```
INFO: Checkout session created: cs_test_xxx for client 39, plan mensuel
INFO: Webhook received: checkout.session.completed
INFO: Abonnement mis à jour pour 39: plan=mensuel, expire=2026-02-21
```

## Migration en production

1. Créez un compte Stripe en mode Live
2. Remplacez les clés de test par les clés de production
3. Configurez un nouveau webhook avec l'URL de production
4. Testez avec un petit montant réel
5. Activez le monitoring des paiements

⚠️ **IMPORTANT**: Ne jamais utiliser les clés de production (`sk_live_`) en environnement de développement !
