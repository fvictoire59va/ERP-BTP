# Tests ERP BTP

Ce répertoire contient les tests automatisés pour l'application ERP BTP.

## Structure des tests

```
tests/
├── __init__.py
├── test_stripe_payment.py    # Tests de paiement Stripe (pytest)
└── README.md                 # Ce fichier
```

## Installation des dépendances de test

```bash
pip install pytest
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

### Avec pytest (recommandé)

```bash
# Tous les tests
pytest tests/ -v

# Tests de paiement uniquement
pytest tests/test_stripe_payment.py -v

# Avec couverture de code
pytest tests/ --cov=erp --cov-report=html
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

## Structure des tests Stripe

### Fixtures pytest

- `reset_stripe_service`: Réinitialise le singleton après chaque test
- `stripe_service_with_keys`: Service Stripe avec clés de test
- `stripe_service_without_keys`: Service Stripe sans clés

### Classes de test

#### `TestStripeServiceConfiguration`
- Teste l'initialisation avec/sans clés

#### `TestStripePlans`
- Vérifie les plans disponibles (mensuel, annuel)
- Vérifie les prix et les durées

#### `TestStripeCheckoutSession`
- Teste la création de sessions Checkout
- Teste la gestion des erreurs

#### `TestStripeWebhook`
- Teste la vérification des signatures webhook
- Teste le traitement des événements

#### `TestStripeIntegrationFlow`
- Teste le flux complet de paiement

#### `TestPaymentAmounts`
- Vérifie les montants en centimes
- Vérifie les économies du plan annuel

## Ajout de nouveaux tests

Pour ajouter de nouveaux tests avec pytest :

```python
import pytest

class TestNewFeature:
    """Description des tests"""
    
    def test_something(self, stripe_service_with_keys):
        """Test quelque chose"""
        # Arrange
        
        # Act
        result = stripe_service_with_keys.do_something()
        
        # Assert
        assert result is not None
```

## CI/CD

Les tests peuvent être intégrés dans un pipeline CI/CD :

```yaml
# Exemple pour GitHub Actions
- name: Run tests
  env:
    STRIPE_SECRET_KEY: ${{ secrets.STRIPE_TEST_SECRET_KEY }}
    STRIPE_PUBLISHABLE_KEY: ${{ secrets.STRIPE_TEST_PUBLISHABLE_KEY }}
  run: |
    pip install pytest
    pytest tests/ -v
```

## Notes

- Les tests utilisent des **fixtures pytest** pour la configuration
- Les assertions sont simples avec `assert` (pas besoin de `self.assertEqual`)
- Les tests sont **isolés** et peuvent s'exécuter dans n'importe quel ordre
- Les mocks et patches utilisent `unittest.mock`
