"""
Tests pour l'intégration Stripe dans ERP BTP
Ce module teste les fonctionnalités de paiement en ligne avec pytest.

Pour exécuter ces tests:
1. Le fichier .env à la racine du projet sera chargé automatiquement
2. Exécuter: pytest tests/test_stripe_payment.py -v
   Ou: pytest tests/test_stripe_payment.py --interactive

Variables d'environnement requises (dans .env):
- STRIPE_SECRET_KEY: Clé secrète Stripe (mode test: sk_test_...)
- STRIPE_PUBLISHABLE_KEY: Clé publique Stripe (mode test: pk_test_...)
- STRIPE_WEBHOOK_SECRET: Secret webhook Stripe (optionnel pour les tests)
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ajouter le chemin racine du projet pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Variables d'environnement chargées depuis {env_path}")
else:
    print(f"⚠ Fichier .env non trouvé: {env_path}")


@pytest.fixture
def reset_stripe_service():
    """Fixture pour réinitialiser le singleton Stripe après chaque test"""
    yield
    import erp.services.stripe_service as stripe_module
    stripe_module._stripe_service = None


@pytest.fixture
def stripe_service_with_keys(reset_stripe_service):
    """Fixture qui configure un service Stripe avec des clés de test"""
    os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
    os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
    
    from erp.services.stripe_service import get_stripe_service
    return get_stripe_service()


@pytest.fixture
def stripe_service_without_keys(reset_stripe_service):
    """Fixture qui crée un service Stripe sans clés configurées"""
    os.environ.pop('STRIPE_SECRET_KEY', None)
    os.environ.pop('STRIPE_PUBLISHABLE_KEY', None)
    
    from erp.services.stripe_service import get_stripe_service
    return get_stripe_service()


# ==================== Tests de Configuration ====================

class TestStripeServiceConfiguration:
    """Tests pour la configuration du service Stripe"""
    
    def test_service_initialization_without_keys(self, stripe_service_without_keys):
        """Test que le service s'initialise même sans clés configurées"""
        service = stripe_service_without_keys
        
        assert service is not None
        assert not service.is_configured()
    
    def test_service_initialization_with_keys(self, stripe_service_with_keys):
        """Test que le service se configure correctement avec les clés"""
        service = stripe_service_with_keys
        
        assert service is not None
        assert service.is_configured()
        assert service.get_publishable_key() == 'pk_test_fake_key_12345'


# ==================== Tests des Plans ====================

class TestStripePlans:
    """Tests pour les plans d'abonnement"""
    
    def test_plans_available(self, stripe_service_with_keys):
        """Test que les plans sont disponibles"""
        plans = stripe_service_with_keys.get_plans()
        
        assert 'mensuel' in plans
        assert 'annuel' in plans
    
    def test_plan_mensuel_price(self, stripe_service_with_keys):
        """Test le prix du plan mensuel"""
        plans = stripe_service_with_keys.get_plans()
        
        assert plans['mensuel']['price'] == 49.0  # 49€
        assert plans['mensuel']['duration_days'] == 30
    
    def test_plan_annuel_price(self, stripe_service_with_keys):
        """Test le prix du plan annuel"""
        plans = stripe_service_with_keys.get_plans()
        
        assert plans['annuel']['price'] == 499.0  # 499€
        assert plans['annuel']['duration_days'] == 365
    
    def test_plan_features(self, stripe_service_with_keys):
        """Test que les plans ont des fonctionnalités"""
        plans = stripe_service_with_keys.get_plans()
        
        for plan_id, plan_info in plans.items():
            assert 'features' in plan_info
            assert len(plan_info['features']) > 0


# ==================== Tests des Sessions Checkout ====================

class TestStripeCheckoutSession:
    """Tests pour la création de sessions Checkout"""
    
    def test_create_checkout_invalid_plan(self, stripe_service_with_keys):
        """Test la création d'une session avec un plan invalide"""
        url, error = stripe_service_with_keys.create_checkout_session(
            plan='invalid_plan',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        assert url is None
        assert error is not None
        assert 'invalide' in error.lower()
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_success(self, mock_create, stripe_service_with_keys):
        """Test la création réussie d'une session Checkout"""
        # Configurer le mock
        mock_session = MagicMock()
        mock_session.id = 'cs_test_12345'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_12345'
        mock_create.return_value = mock_session
        
        url, error = stripe_service_with_keys.create_checkout_session(
            plan='mensuel',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        assert url is not None
        assert error is None
        assert 'checkout.stripe.com' in url
        
        # Vérifier les arguments passés à Stripe
        assert mock_create.called
        call_args = mock_create.call_args
        assert call_args.kwargs['customer_email'] == 'test@example.com'
        assert call_args.kwargs['metadata']['client_id'] == 'test_client_123'
        assert call_args.kwargs['metadata']['plan'] == 'mensuel'
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_stripe_error(self, mock_create, stripe_service_with_keys):
        """Test la gestion des erreurs Stripe"""
        import stripe
        mock_create.side_effect = stripe.error.StripeError("Erreur de test")
        
        url, error = stripe_service_with_keys.create_checkout_session(
            plan='annuel',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        assert url is None
        assert error is not None


# ==================== Tests des Webhooks ====================

class TestStripeWebhook:
    """Tests pour les webhooks Stripe"""
    
    def test_verify_webhook_without_secret(self, reset_stripe_service):
        """Test la vérification webhook sans secret configuré"""
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        os.environ.pop('STRIPE_WEBHOOK_SECRET', None)
        
        from erp.services.stripe_service import get_stripe_service
        service = get_stripe_service()
        
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        event, error = service.verify_webhook_signature(payload, 'sig_test')
        
        # Sans secret configuré, le payload devrait être parsé directement
        assert event is not None
        assert event['type'] == 'checkout.session.completed'
    
    def test_handle_checkout_completed_missing_client_id(self, stripe_service_with_keys):
        """Test le traitement d'un checkout sans client_id"""
        session = {
            'id': 'cs_test_12345',
            'metadata': {}  # Pas de client_id
        }
        
        success, error = stripe_service_with_keys.handle_checkout_completed(session)
        
        assert not success
        assert 'client' in error.lower()


# ==================== Tests d'Intégration ====================

class TestStripeIntegrationFlow:
    """Tests d'intégration du flux complet de paiement"""
    
    @patch('stripe.checkout.Session.create')
    @patch('stripe.checkout.Session.retrieve')
    def test_full_payment_flow(self, mock_retrieve, mock_create, reset_stripe_service):
        """Test le flux complet: création session -> récupération détails"""
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        os.environ['APP_URL'] = 'http://localhost:8080'
        
        from erp.services.stripe_service import get_stripe_service
        service = get_stripe_service()
        
        # 1. Créer la session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_flow_12345'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_flow_12345'
        mock_create.return_value = mock_session
        
        url, error = service.create_checkout_session(
            plan='mensuel',
            client_id='flow_test_client',
            client_email='flow@test.com'
        )
        
        assert url is not None
        
        # 2. Simuler la récupération des détails
        mock_retrieved = MagicMock()
        mock_retrieved.id = 'cs_test_flow_12345'
        mock_retrieved.payment_status = 'paid'
        mock_retrieved.customer_email = 'flow@test.com'
        mock_retrieved.amount_total = 4900
        mock_retrieved.currency = 'eur'
        mock_retrieved.metadata = {'client_id': 'flow_test_client', 'plan': 'mensuel'}
        mock_retrieve.return_value = mock_retrieved
        
        details = service.get_session_details('cs_test_flow_12345')
        
        assert details is not None
        assert details['status'] == 'paid'
        assert details['amount_total'] == 4900


# ==================== Tests des Montants ====================

class TestPaymentAmounts:
    """Tests pour vérifier les montants de paiement"""
    
    def test_monthly_amount_in_cents(self):
        """Test que le montant mensuel est en centimes"""
        from erp.services.stripe_service import StripeService
        service = StripeService()
        plan = service.PLANS['mensuel']
        
        # 49€ = 4900 centimes
        assert plan['price'] == 4900
        assert plan['currency'] == 'eur'
    
    def test_annual_amount_in_cents(self):
        """Test que le montant annuel est en centimes"""
        from erp.services.stripe_service import StripeService
        service = StripeService()
        plan = service.PLANS['annuel']
        
        # 499€ = 49900 centimes
        assert plan['price'] == 49900
        assert plan['currency'] == 'eur'
    
    def test_annual_savings(self):
        """Test que le plan annuel offre bien des économies"""
        from erp.services.stripe_service import StripeService
        service = StripeService()
        
        monthly_price = service.PLANS['mensuel']['price']
        annual_price = service.PLANS['annuel']['price']
        
        # 12 mois au prix mensuel
        monthly_total = monthly_price * 12
        
        # L'annuel doit être moins cher
        assert annual_price < monthly_total
        
        # Calculer l'économie
        savings = monthly_total - annual_price
        
        # L'économie doit être positive (plus que 0)
        assert savings > 0


# ==================== Tests Interactifs ====================

def run_payment_test_interactive():
    """
    Test interactif de paiement Stripe (mode test)
    
    Ce test nécessite des clés Stripe en mode test valides.
    Il crée une vraie session de paiement (sans débiter).
    """
    print("\n" + "="*60)
    print("TEST INTERACTIF DE PAIEMENT STRIPE")
    print("="*60)
    
    # Vérifier la configuration
    secret_key = os.getenv('STRIPE_SECRET_KEY', '')
    pub_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    
    if not secret_key.startswith('sk_test_'):
        print("\n⚠️  ATTENTION: Ce test nécessite des clés Stripe en mode TEST")
        print("   Configurez STRIPE_SECRET_KEY avec une clé sk_test_...")
        print("   Les clés de production (sk_live_) ne doivent PAS être utilisées pour les tests!\n")
        return
    
    if not pub_key.startswith('pk_test_'):
        print("\n⚠️  STRIPE_PUBLISHABLE_KEY devrait être une clé pk_test_...")
        return
    
    print(f"\n✓ Clé secrète configurée: {secret_key[:12]}...")
    print(f"✓ Clé publique configurée: {pub_key[:12]}...")
    
    from erp.services.stripe_service import get_stripe_service
    service = get_stripe_service()
    
    if not service.is_configured():
        print("\n❌ Service Stripe non configuré correctement")
        return
    
    print("\n📋 Plans disponibles:")
    for plan_id, plan_info in service.get_plans().items():
        print(f"   - {plan_id}: {plan_info['name']} - {plan_info['price_display']}")
    
    print("\n🔄 Création d'une session de paiement test...")
    
    url, error = service.create_checkout_session(
        plan='mensuel',
        client_id='test_interactive_client',
        client_email='test@example.com'
    )
    
    if error:
        print(f"\n❌ Erreur: {error}")
        return
    
    print(f"\n✅ Session créée avec succès!")
    print(f"\n🔗 URL de paiement (mode test):")
    print(f"   {url}")
    print(f"\n💡 Pour tester le paiement:")
    print(f"   - Utilisez le numéro de carte: 4242 4242 4242 4242")
    print(f"   - Date d'expiration: n'importe quelle date future")
    print(f"   - CVC: n'importe quel chiffre à 3 chiffres")
    print(f"\n   (Aucun paiement réel ne sera effectué en mode test)")
    print("="*60 + "\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Tests de paiement Stripe pour ERP BTP')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Exécuter le test interactif (crée une vraie session de test)')
    
    args = parser.parse_args()
    
    if args.interactive:
        run_payment_test_interactive()
    else:
        # Exécuter pytest si appelé directement
        pytest.main([__file__, '-v'])
