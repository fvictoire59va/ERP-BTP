"""
Service d'intégration Stripe pour les paiements d'abonnements
"""
import os
import stripe
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from erp.utils.logger import get_logger

logger = get_logger(__name__)


class StripeService:
    """Service pour gérer les paiements via Stripe"""
    
    # Plans d'abonnement disponibles
    PLANS = {
        'essai': {
            'name': 'Période d\'essai',
            'price': 0,
            'duration_days': 30,
            'features': ['Accès complet pendant 30 jours', 'Support par email']
        },
        'mensuel': {
            'name': 'Abonnement Mensuel',
            'price': 4900,  # 49€ en centimes
            'currency': 'eur',
            'duration_days': 30,
            'features': ['Accès complet', 'Support prioritaire', 'Mises à jour incluses']
        },
        'annuel': {
            'name': 'Abonnement Annuel',
            'price': 49900,  # 499€ en centimes (2 mois offerts)
            'currency': 'eur',
            'duration_days': 365,
            'features': ['Accès complet', 'Support prioritaire', 'Mises à jour incluses', '2 mois offerts']
        }
    }
    
    def __init__(self):
        """Initialise le service Stripe avec les clés API"""
        self.api_key = os.getenv('STRIPE_SECRET_KEY', '')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        self.app_url = os.getenv('APP_URL', 'http://localhost:8080')
        
        if self.api_key:
            stripe.api_key = self.api_key
            logger.info("Stripe API configuré avec succès")
        else:
            logger.warning(
                "⚠️ STRIPE_SECRET_KEY non configuré! "
                "Les paiements ne fonctionneront pas. "
                "Configurez STRIPE_SECRET_KEY dans les variables d'environnement."
            )
        
        if not self.publishable_key:
            logger.warning("⚠️ STRIPE_PUBLISHABLE_KEY non configuré!")
        
        if not self.webhook_secret:
            logger.warning("⚠️ STRIPE_WEBHOOK_SECRET non configuré! Les webhooks ne seront pas vérifiés.")
    
    def is_configured(self) -> bool:
        """Vérifie si Stripe est correctement configuré"""
        return bool(self.api_key and self.publishable_key)
    
    def get_publishable_key(self) -> str:
        """Retourne la clé publique Stripe pour le frontend"""
        return self.publishable_key
    
    def create_checkout_session(
        self, 
        plan: str, 
        client_id: str, 
        client_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Crée une session de paiement Stripe Checkout
        
        Args:
            plan: Type de plan ('mensuel' ou 'annuel')
            client_id: Identifiant du client
            client_email: Email du client
            success_url: URL de redirection après succès
            cancel_url: URL de redirection après annulation
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (checkout_url, error_message)
        """
        if not self.is_configured():
            return None, "Stripe n'est pas configuré. Contactez l'administrateur."
        
        if plan not in ['mensuel', 'annuel']:
            return None, f"Plan invalide: {plan}. Choisissez 'mensuel' ou 'annuel'."
        
        plan_info = self.PLANS[plan]
        
        try:
            # URLs par défaut
            if not success_url:
                success_url = f"{self.app_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{self.app_url}/payment-cancelled"
            
            # Créer la session Checkout
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan_info['currency'],
                        'product_data': {
                            'name': f"ERP BTP - {plan_info['name']}",
                            'description': ', '.join(plan_info['features']),
                        },
                        'unit_amount': plan_info['price'],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=client_email,
                metadata={
                    'client_id': client_id,
                    'plan': plan,
                    'duration_days': str(plan_info['duration_days'])
                },
                locale='fr'
            )
            
            logger.info(f"Session Checkout créée: {session.id} pour client {client_id}, plan {plan}")
            return session.url, None
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe lors de la création de la session: {e}", exc_info=True)
            return None, f"Erreur de paiement: {str(e)}"
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de la session: {e}", exc_info=True)
            return None, "Erreur interne. Veuillez réessayer."
    
    def create_subscription(
        self,
        plan: str,
        client_id: str,
        client_email: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Crée un abonnement récurrent Stripe
        
        Args:
            plan: Type de plan ('mensuel' ou 'annuel')
            client_id: Identifiant du client
            client_email: Email du client
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (checkout_url, error_message)
        """
        if not self.is_configured():
            return None, "Stripe n'est pas configuré. Contactez l'administrateur."
        
        if plan not in ['mensuel', 'annuel']:
            return None, f"Plan invalide: {plan}"
        
        plan_info = self.PLANS[plan]
        interval = 'month' if plan == 'mensuel' else 'year'
        
        try:
            # Créer la session Checkout pour abonnement
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan_info['currency'],
                        'product_data': {
                            'name': f"ERP BTP - {plan_info['name']}",
                            'description': ', '.join(plan_info['features']),
                        },
                        'unit_amount': plan_info['price'],
                        'recurring': {
                            'interval': interval,
                            'interval_count': 1
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{self.app_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.app_url}/payment-cancelled",
                customer_email=client_email,
                metadata={
                    'client_id': client_id,
                    'plan': plan
                },
                locale='fr'
            )
            
            logger.info(f"Session d'abonnement créée: {session.id} pour client {client_id}")
            return session.url, None
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}", exc_info=True)
            return None, f"Erreur de paiement: {str(e)}"
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}", exc_info=True)
            return None, "Erreur interne. Veuillez réessayer."
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Vérifie la signature d'un webhook Stripe
        
        Args:
            payload: Corps de la requête (bytes)
            signature: Signature Stripe (header Stripe-Signature)
            
        Returns:
            Tuple[Optional[Dict], Optional[str]]: (event_data, error_message)
        """
        if not self.webhook_secret:
            logger.warning("Webhook reçu mais STRIPE_WEBHOOK_SECRET non configuré")
            # Retourner l'événement sans vérification en dev
            try:
                import json
                return json.loads(payload), None
            except:
                return None, "Payload invalide"
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event, None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Signature webhook invalide: {e}")
            return None, "Signature invalide"
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du webhook: {e}")
            return None, str(e)
    
    def handle_checkout_completed(self, session: Dict) -> Tuple[bool, Optional[str]]:
        """
        Traite un événement checkout.session.completed
        Met à jour l'abonnement du client dans la base de données
        
        Args:
            session: Données de la session Stripe
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            metadata = session.get('metadata', {})
            client_id = metadata.get('client_id')
            plan = metadata.get('plan')
            duration_days = int(metadata.get('duration_days', 30))
            
            if not client_id:
                logger.error("client_id manquant dans les metadata de la session")
                return False, "Identifiant client manquant"
            
            # Calculer la nouvelle date de fin
            from datetime import datetime, timedelta
            new_expiry = (datetime.now() + timedelta(days=duration_days)).date()
            
            # Mettre à jour l'abonnement dans la base de données
            from erp.services.subscription_service import get_subscription_service
            subscription_service = get_subscription_service()
            
            success = self._update_subscription_in_db(
                client_id=client_id,
                new_expiry=new_expiry,
                plan=plan,
                stripe_session_id=session.get('id')
            )
            
            if success:
                logger.info(f"Abonnement mis à jour pour {client_id}: plan={plan}, expire={new_expiry}")
                return True, None
            else:
                return False, "Erreur lors de la mise à jour de l'abonnement"
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du checkout: {e}", exc_info=True)
            return False, str(e)
    
    def _update_subscription_in_db(
        self,
        client_id: str,
        new_expiry,
        plan: str,
        stripe_session_id: str
    ) -> bool:
        """
        Met à jour l'abonnement dans la base de données
        
        Args:
            client_id: Identifiant du client
            new_expiry: Nouvelle date d'expiration
            plan: Plan choisi
            stripe_session_id: ID de la session Stripe
            
        Returns:
            bool: True si succès
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = None
        cursor = None
        
        try:
            # Connexion à la base de données des abonnements
            from erp.services.subscription_service import get_subscription_service
            subscription_service = get_subscription_service()
            
            conn = psycopg2.connect(
                host=subscription_service.host,
                port=subscription_service.port,
                database=subscription_service.database,
                user=subscription_service.user,
                password=subscription_service.password,
                connect_timeout=5
            )
            cursor = conn.cursor()
            
            # Mettre à jour l'abonnement
            query = """
                UPDATE abonnements
                SET date_fin_essai = %s,
                    statut = 'actif'
                WHERE client_id = %s
            """
            
            cursor.execute(query, (new_expiry, client_id))
            
            # Enregistrer le paiement dans une table de logs (si elle existe)
            try:
                log_query = """
                    INSERT INTO paiements_logs (client_id, stripe_session_id, plan, montant, date_paiement)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                plan_info = self.PLANS.get(plan, {})
                montant = plan_info.get('price', 0) / 100  # Convertir centimes en euros
                cursor.execute(log_query, (client_id, stripe_session_id, plan, montant))
            except psycopg2.Error:
                # La table de logs n'existe peut-être pas, ce n'est pas grave
                pass
            
            conn.commit()
            logger.info(f"Base de données mise à jour pour client {client_id}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Erreur DB lors de la mise à jour de l'abonnement: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_session_details(self, session_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'une session Checkout
        
        Args:
            session_id: ID de la session Stripe
            
        Returns:
            Optional[Dict]: Détails de la session ou None
        """
        if not self.is_configured():
            return None
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'id': session.id,
                'status': session.payment_status,
                'customer_email': session.customer_email,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'metadata': session.metadata
            }
        except stripe.error.StripeError as e:
            logger.error(f"Erreur lors de la récupération de la session: {e}")
            return None
    
    def get_plans(self) -> Dict[str, Dict]:
        """Retourne les plans disponibles avec leurs informations"""
        return {
            plan_id: {
                'id': plan_id,
                'name': plan_info['name'],
                'price': plan_info['price'] / 100 if plan_info['price'] > 0 else 0,  # En euros
                'price_display': f"{plan_info['price'] / 100:.2f}€" if plan_info['price'] > 0 else "Gratuit",
                'duration_days': plan_info['duration_days'],
                'features': plan_info['features']
            }
            for plan_id, plan_info in self.PLANS.items()
            if plan_id != 'essai'  # Ne pas afficher l'essai comme plan payant
        }


# Instance singleton
_stripe_service = None


def get_stripe_service() -> StripeService:
    """Retourne l'instance singleton du service Stripe"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
