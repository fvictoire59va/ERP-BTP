"""
Service de gestion des abonnements avec base de données externe
"""
import os
from datetime import datetime
from typing import Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from erp.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    """Service pour gérer les abonnements des clients"""
    
    def __init__(self):
        """Initialise le service avec les paramètres de connexion à la BD externe"""
        self.host = os.getenv('SUBSCRIPTION_DB_HOST', '176.131.66.167')
        self.port = os.getenv('SUBSCRIPTION_DB_PORT', '5433')
        self.database = os.getenv('SUBSCRIPTION_DB_NAME', 'erpbtp_clients')
        self.user = os.getenv('SUBSCRIPTION_DB_USER', 'postgres')
        self.password = os.getenv('SUBSCRIPTION_DB_PASSWORD', '')
        
    def _get_connection(self):
        """Crée et retourne une connexion à la base de données des abonnements"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=5
            )
            return conn
        except psycopg2.Error as e:
            logger.error(f"Erreur de connexion à la base des abonnements: {e}", exc_info=True)
            raise
    
    def check_subscription(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si l'abonnement du client est actif
        
        Args:
            client_id: Identifiant du client (username ou email)
            
        Returns:
            Tuple[bool, Optional[str]]: (is_active, message)
                - is_active: True si l'abonnement est actif, False sinon
                - message: Message d'erreur ou None si actif
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations d'abonnement
            query = """
                SELECT 
                    id,
                    client_id,
                    date_fin_essai,
                    statut,
                    date_creation,
                    date_modification
                FROM abonnements
                WHERE client_id = %s
            """
            
            cursor.execute(query, (client_id,))
            abonnement = cursor.fetchone()
            
            if not abonnement:
                logger.warning(f"Aucun abonnement trouvé pour le client: {client_id}")
                return False, "Aucun abonnement actif. Veuillez contacter le support."
            
            # Vérifier la date de fin d'essai
            date_fin_essai = abonnement['date_fin_essai']
            statut_actuel = abonnement['statut']
            
            if date_fin_essai:
                # Convertir la date en datetime si nécessaire
                if isinstance(date_fin_essai, str):
                    date_fin_essai = datetime.strptime(date_fin_essai, '%Y-%m-%d').date()
                elif isinstance(date_fin_essai, datetime):
                    date_fin_essai = date_fin_essai.date()
                
                date_aujourd_hui = datetime.now().date()
                
                # Si la date est dépassée et le statut n'est pas déjà suspendu
                if date_fin_essai < date_aujourd_hui:
                    if statut_actuel != 'suspendu':
                        # Mettre à jour le statut à suspendu
                        self._update_subscription_status(cursor, abonnement['id'], 'suspendu')
                        conn.commit()
                        logger.warning(f"Abonnement expiré pour {client_id}, statut mis à jour à 'suspendu'")
                    
                    return False, "Votre abonnement a expiré. Veuillez renouveler votre abonnement."
            
            # Vérifier si le statut est suspendu
            if statut_actuel == 'suspendu':
                logger.warning(f"Tentative de connexion avec compte suspendu: {client_id}")
                return False, "Votre compte est suspendu. Veuillez renouveler votre abonnement."
            
            # L'abonnement est actif
            logger.info(f"Abonnement actif pour le client: {client_id}")
            return True, None
            
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la vérification de l'abonnement: {e}", exc_info=True)
            # En cas d'erreur de connexion à la DB des abonnements, on laisse passer
            # pour ne pas bloquer tous les utilisateurs
            logger.warning("Erreur DB abonnements - autorisation par défaut")
            return True, None
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification de l'abonnement: {e}", exc_info=True)
            return True, None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _update_subscription_status(self, cursor, abonnement_id: int, new_status: str):
        """
        Met à jour le statut d'un abonnement
        
        Args:
            cursor: Curseur de base de données
            abonnement_id: ID de l'abonnement
            new_status: Nouveau statut (actif, suspendu, etc.)
        """
        try:
            update_query = """
                UPDATE abonnements
                SET statut = %s,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(update_query, (new_status, abonnement_id))
            logger.info(f"Statut de l'abonnement {abonnement_id} mis à jour à '{new_status}'")
            
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}", exc_info=True)
            raise
    
    def get_subscription_info(self, client_id: str) -> Optional[dict]:
        """
        Récupère les informations d'abonnement d'un client
        
        Args:
            client_id: Identifiant du client
            
        Returns:
            Optional[dict]: Informations de l'abonnement ou None
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    id,
                    client_id,
                    date_fin_essai,
                    statut,
                    date_creation,
                    date_modification
                FROM abonnements
                WHERE client_id = %s
            """
            
            cursor.execute(query, (client_id,))
            abonnement = cursor.fetchone()
            
            if abonnement:
                return dict(abonnement)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations d'abonnement: {e}", exc_info=True)
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


# Instance singleton du service
_subscription_service = None


def get_subscription_service() -> SubscriptionService:
    """Retourne l'instance singleton du service d'abonnement"""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
