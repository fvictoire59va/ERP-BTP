"""
Tests pour l'intégration Stripe dans ERP BTP
Ce module teste les fonctionnalités de paiement en ligne.

Pour exécuter ces tests:
1. Le fichier .env à la racine du projet sera chargé automatiquement
2. Exécuter: python -m pytest tests/test_stripe_payment.py -v
   Ou: python tests/test_stripe_payment.py --interactive

Variables d'environnement requises (dans .env):
- STRIPE_SECRET_KEY: Clé secrète Stripe (mode test: sk_test_...)
- STRIPE_PUBLISHABLE_KEY: Clé publique Stripe (mode test: pk_test_...)
- STRIPE_WEBHOOK_SECRET: Secret webhook Stripe (optionnel pour les tests)
"""
import os
import sys
import unittest
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


class TestStripeServiceConfiguration(unittest.TestCase):
    """Tests pour la configuration du service Stripe"""
    
    def test_service_initialization_without_keys(self):
        """Test que le service s'initialise même sans clés configurées"""
        # Sauvegarder les valeurs originales
        original_secret = os.environ.get('STRIPE_SECRET_KEY')
        original_pub = os.environ.get('STRIPE_PUBLISHABLE_KEY')
        
        try:
            # Supprimer les clés
            os.environ.pop('STRIPE_SECRET_KEY', None)
            os.environ.pop('STRIPE_PUBLISHABLE_KEY', None)
            
            # Réinitialiser le singleton
            import erp.services.stripe_service as stripe_module
            stripe_module._stripe_service = None
            
            from erp.services.stripe_service import get_stripe_service
            service = get_stripe_service()
            
            self.assertIsNotNone(service)
            self.assertFalse(service.is_configured())
            
        finally:
            # Restaurer les valeurs originales
            if original_secret:
                os.environ['STRIPE_SECRET_KEY'] = original_secret
            if original_pub:
                os.environ['STRIPE_PUBLISHABLE_KEY'] = original_pub
    
    def test_service_initialization_with_keys(self):
        """Test que le service se configure correctement avec les clés"""
        # Sauvegarder les valeurs originales
        original_secret = os.environ.get('STRIPE_SECRET_KEY')
        original_pub = os.environ.get('STRIPE_PUBLISHABLE_KEY')
        
        try:
            # Définir des clés de test
            os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
            os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
            
            # Réinitialiser le singleton
            import erp.services.stripe_service as stripe_module
            stripe_module._stripe_service = None
            
            from erp.services.stripe_service import get_stripe_service
            service = get_stripe_service()
            
            self.assertIsNotNone(service)
            self.assertTrue(service.is_configured())
            self.assertEqual(service.get_publishable_key(), 'pk_test_fake_key_12345')
            
        finally:
            # Restaurer les valeurs originales
            if original_secret:
                os.environ['STRIPE_SECRET_KEY'] = original_secret
            else:
                os.environ.pop('STRIPE_SECRET_KEY', None)
            if original_pub:
                os.environ['STRIPE_PUBLISHABLE_KEY'] = original_pub
            else:
                os.environ.pop('STRIPE_PUBLISHABLE_KEY', None)


class TestStripePlans(unittest.TestCase):
    """Tests pour les plans d'abonnement"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        # Configurer les clés pour les tests
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        
        # Réinitialiser le singleton
        import erp.services.stripe_service as stripe_module
        stripe_module._stripe_service = None
        
        from erp.services.stripe_service import get_stripe_service
        self.service = get_stripe_service()
    
    def test_plans_available(self):
        """Test que les plans sont disponibles"""
        plans = self.service.get_plans()
        
        self.assertIn('mensuel', plans)
        self.assertIn('annuel', plans)
    
    def test_plan_mensuel_price(self):
        """Test le prix du plan mensuel"""
        plans = self.service.get_plans()
        
        self.assertEqual(plans['mensuel']['price'], 49.0)  # 49€
        self.assertEqual(plans['mensuel']['duration_days'], 30)
    
    def test_plan_annuel_price(self):
        """Test le prix du plan annuel"""
        plans = self.service.get_plans()
        
        self.assertEqual(plans['annuel']['price'], 499.0)  # 499€
        self.assertEqual(plans['annuel']['duration_days'], 365)
    
    def test_plan_features(self):
        """Test que les plans ont des fonctionnalités"""
        plans = self.service.get_plans()
        
        for plan_id, plan_info in plans.items():
            self.assertIn('features', plan_info)
            self.assertTrue(len(plan_info['features']) > 0)


class TestStripeCheckoutSession(unittest.TestCase):
    """Tests pour la création de sessions Checkout"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        
        import erp.services.stripe_service as stripe_module
        stripe_module._stripe_service = None
        
        from erp.services.stripe_service import get_stripe_service
        self.service = get_stripe_service()
    
    def test_create_checkout_invalid_plan(self):
        """Test la création d'une session avec un plan invalide"""
        url, error = self.service.create_checkout_session(
            plan='invalid_plan',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        self.assertIsNone(url)
        self.assertIsNotNone(error)
        self.assertIn('invalide', error.lower())
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_success(self, mock_create):
        """Test la création réussie d'une session Checkout"""
        # Configurer le mock
        mock_session = MagicMock()
        mock_session.id = 'cs_test_12345'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_12345'
        mock_create.return_value = mock_session
        
        url, error = self.service.create_checkout_session(
            plan='mensuel',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        self.assertIsNotNone(url)
        self.assertIsNone(error)
        self.assertIn('checkout.stripe.com', url)
        
        # Vérifier les arguments passés à Stripe
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        self.assertEqual(call_args.kwargs['customer_email'], 'test@example.com')
        self.assertEqual(call_args.kwargs['metadata']['client_id'], 'test_client_123')
        self.assertEqual(call_args.kwargs['metadata']['plan'], 'mensuel')
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_stripe_error(self, mock_create):
        """Test la gestion des erreurs Stripe"""
        import stripe
        mock_create.side_effect = stripe.error.StripeError("Erreur de test")
        
        url, error = self.service.create_checkout_session(
            plan='annuel',
            client_id='test_client_123',
            client_email='test@example.com'
        )
        
        self.assertIsNone(url)
        self.assertIsNotNone(error)


class TestStripeWebhook(unittest.TestCase):
    """Tests pour les webhooks Stripe"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        os.environ.pop('STRIPE_WEBHOOK_SECRET', None)  # Pas de webhook secret pour les tests
        
        import erp.services.stripe_service as stripe_module
        stripe_module._stripe_service = None
        
        from erp.services.stripe_service import get_stripe_service
        self.service = get_stripe_service()
    
    def test_verify_webhook_without_secret(self):
        """Test la vérification webhook sans secret configuré"""
        payload = b'{"type": "checkout.session.completed", "data": {}}'
        
        event, error = self.service.verify_webhook_signature(payload, 'sig_test')
        
        # Sans secret configuré, le payload devrait être parsé directement
        self.assertIsNotNone(event)
        self.assertEqual(event['type'], 'checkout.session.completed')
    
    def test_handle_checkout_completed_missing_client_id(self):
        """Test le traitement d'un checkout sans client_id"""
        session = {
            'id': 'cs_test_12345',
            'metadata': {}  # Pas de client_id
        }
        
        success, error = self.service.handle_checkout_completed(session)
        
        self.assertFalse(success)
        self.assertIn('client', error.lower())


class TestStripeIntegrationFlow(unittest.TestCase):
    """Tests d'intégration du flux complet de paiement"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_fake_key_12345'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_fake_key_12345'
        os.environ['APP_URL'] = 'http://localhost:8080'
        
        import erp.services.stripe_service as stripe_module
        stripe_module._stripe_service = None
        
        from erp.services.stripe_service import get_stripe_service
        self.service = get_stripe_service()
    
    @patch('stripe.checkout.Session.create')
    @patch('stripe.checkout.Session.retrieve')
    def test_full_payment_flow(self, mock_retrieve, mock_create):
        """Test le flux complet: création session -> récupération détails"""
        # 1. Créer la session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_flow_12345'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_flow_12345'
        mock_create.return_value = mock_session
        
        url, error = self.service.create_checkout_session(
            plan='mensuel',
            client_id='flow_test_client',
            client_email='flow@test.com'
        )
        
        self.assertIsNotNone(url)
        
        # 2. Simuler la récupération des détails
        mock_retrieved = MagicMock()
        mock_retrieved.id = 'cs_test_flow_12345'
        mock_retrieved.payment_status = 'paid'
        mock_retrieved.customer_email = 'flow@test.com'
        mock_retrieved.amount_total = 4900
        mock_retrieved.currency = 'eur'
        mock_retrieved.metadata = {'client_id': 'flow_test_client', 'plan': 'mensuel'}
        mock_retrieve.return_value = mock_retrieved
        
        details = self.service.get_session_details('cs_test_flow_12345')
        
        self.assertIsNotNone(details)
        self.assertEqual(details['status'], 'paid')
        self.assertEqual(details['amount_total'], 4900)


class TestPaymentAmounts(unittest.TestCase):
    """Tests pour vérifier les montants de paiement"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        from erp.services.stripe_service import StripeService
        self.service = StripeService()
    
    def test_monthly_amount_in_cents(self):
        """Test que le montant mensuel est en centimes"""
        plan = self.service.PLANS['mensuel']
        
        # 49€ = 4900 centimes
        self.assertEqual(plan['price'], 4900)
        self.assertEqual(plan['currency'], 'eur')
    
    def test_annual_amount_in_cents(self):
        """Test que le montant annuel est en centimes"""
        plan = self.service.PLANS['annuel']
        
        # 499€ = 49900 centimes (2 mois offerts par rapport à 12 x 49€ = 588€)
        self.assertEqual(plan['price'], 49900)
        self.assertEqual(plan['currency'], 'eur')
    
    def test_annual_savings(self):
        """Test que le plan annuel offre bien des économies"""
        monthly_price = self.service.PLANS['mensuel']['price']
        annual_price = self.service.PLANS['annuel']['price']
        
        # 12 mois au prix mensuel
        monthly_total = monthly_price * 12
        
        # L'annuel doit être moins cher
        self.assertLess(annual_price, monthly_total)
        
        # Calculer l'économie (doit être au moins 2 mois)
        savings = monthly_total - annual_price
        two_months = monthly_price * 2
        
        self.assertGreaterEqual(savings, two_months - 100)  # Tolérance de 1€


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
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbeux')
    
    args = parser.parse_args()
    
    if args.interactive:
        run_payment_test_interactive()
    else:
        # Exécuter les tests unitaires
        verbosity = 2 if args.verbose else 1
        unittest.main(argv=[''], verbosity=verbosity, exit=False)
