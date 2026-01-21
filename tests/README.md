# Tests ERP BTP

Ce répertoire contient les tests automatisés pour l'application ERP BTP.

## Structure des tests

```
tests/
├── __init__.py
├── test_stripe_payment.py    # Tests de paiement Stripe
└── README.md                 # Ce fichier
```

## Installation des dépendances de test

```bash
pip install pytest pytest-cov unittest
```

## Configuration pour les tests Stripe

Pour exécuter les tests de paiement, vous devez configurer les clés Stripe en **mode test** :

```bash
# Variables d'environnement (mode test)
export STRIPE_SECRET_KEY=sk_test_votre_cle_secrete
export STRIPE_PUBLISHABLE_KEY=pk_test_votre_cle_publique
export STRIPE_WEBHOOK_SECRET=whsec_votre_secret_webhook  # Optionnel
```

⚠️ **IMPORTANT** : N'utilisez JAMAIS les clés de production (`sk_live_`, `pk_live_`) pour les tests !

## Exécution des tests

### Tests unitaires

```bash
# Tous les tests
python -m pytest tests/ -v

# Tests de paiement uniquement
python -m pytest tests/test_stripe_payment.py -v

# Avec couverture de code
python -m pytest tests/ --cov=erp --cov-report=html
```

### Test interactif de paiement

Le test interactif crée une vraie session de paiement Stripe (en mode test) :

```bash
python tests/test_stripe_payment.py --interactive
```

Ce test :
1. Vérifie que les clés Stripe sont configurées
2. Affiche les plans disponibles
3. Crée une session de paiement
4. Affiche l'URL pour tester le paiement

### Cartes de test Stripe

Pour tester les paiements, utilisez ces numéros de carte :

| Type | Numéro | Résultat |
|------|--------|----------|
| Visa | `4242 4242 4242 4242` | Paiement réussi |
| Visa (décliné) | `4000 0000 0000 0002` | Carte déclinée |
| Mastercard | `5555 5555 5555 4444` | Paiement réussi |
| 3D Secure | `4000 0025 0000 3155` | Authentification 3D Secure |

- **Date d'expiration** : N'importe quelle date future
- **CVC** : N'importe quel code à 3 chiffres
- **Code postal** : N'importe quel code

## Structure des tests de paiement

### `TestStripeServiceConfiguration`
- Teste l'initialisation du service avec/sans clés

### `TestStripePlans`
- Vérifie les plans disponibles (mensuel, annuel)
- Vérifie les prix et les durées

### `TestStripeCheckoutSession`
- Teste la création de sessions Checkout
- Teste la gestion des erreurs

### `TestStripeWebhook`
- Teste la vérification des signatures webhook
- Teste le traitement des événements

### `TestStripeIntegrationFlow`
- Teste le flux complet de paiement

### `TestPaymentAmounts`
- Vérifie les montants en centimes
- Vérifie les économies du plan annuel

## Ajout de nouveaux tests

Pour ajouter de nouveaux tests :

1. Créer un fichier `test_*.py` dans ce répertoire
2. Suivre la convention de nommage : `test_<fonctionnalité>.py`
3. Utiliser `unittest.TestCase` ou les fonctions pytest
4. Documenter les dépendances nécessaires

## CI/CD

Les tests peuvent être intégrés dans un pipeline CI/CD :

```yaml
# Exemple pour GitHub Actions
- name: Run tests
  env:
    STRIPE_SECRET_KEY: ${{ secrets.STRIPE_TEST_SECRET_KEY }}
    STRIPE_PUBLISHABLE_KEY: ${{ secrets.STRIPE_TEST_PUBLISHABLE_KEY }}
  run: |
    pip install pytest pytest-cov
    python -m pytest tests/ -v --cov=erp
```
