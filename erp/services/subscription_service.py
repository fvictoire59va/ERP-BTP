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
        
        # Log de configuration pour le débogage
        logger.debug(
            f"Configuration d'abonnement: host={self.host}, port={self.port}, "
            f"db={self.database}, user={self.user}, password={'*' * len(self.password) if self.password else '(vide)'}"
        )
        
        # Vérifier que le mot de passe est configuré
        if not self.password:
            logger.warning(
                "⚠️ SUBSCRIPTION_DB_PASSWORD non configuré ou vide! "
                "Vérifiez que la variable d'environnement SUBSCRIPTION_DB_PASSWORD est définie. "
                "Les vérifications d'abonnement échoueront."
            )
        
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
            logger.error(
                f"Erreur de connexion à la base des abonnements "
                f"({self.user}@{self.host}:{self.port}/{self.database}): {e}", 
                exc_info=True
            )
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
                    plan,
                    prix_mensuel,
                    date_debut,
                    date_fin,
                    statut,
                    periode_essai,
                    date_fin_essai
                FROM abonnements
                WHERE client_id = %s
            """
            
            cursor.execute(query, (client_id,))
            abonnement = cursor.fetchone()
            
            if not abonnement:
                logger.warning(f"Aucun abonnement trouvé pour le client: {client_id}")
                return False, "Aucun abonnement actif. Veuillez contacter le support."
            
            # Récupérer les informations d'abonnement
            statut_actuel = abonnement['statut']
            periode_essai = abonnement.get('periode_essai', False)
            date_fin_essai = abonnement.get('date_fin_essai')
            date_fin = abonnement.get('date_fin')
            
            date_maintenant = datetime.now()
            
            # Vérifier si en période d'essai
            if periode_essai and date_fin_essai:
                # Convertir la date en datetime si nécessaire
                if isinstance(date_fin_essai, str):
                    date_fin_essai = datetime.strptime(date_fin_essai, '%Y-%m-%d %H:%M:%S')
                
                if date_fin_essai < date_maintenant:
                    if statut_actuel != 'suspendu':
                        # Mettre à jour le statut à suspendu
                        self._update_subscription_status(cursor, abonnement['id'], 'suspendu')
                        conn.commit()
                        logger.warning(f"Période d'essai expirée pour {client_id}, statut mis à jour à 'suspendu'")
                    
                    return False, "Votre période d'essai a expiré. Veuillez souscrire à un abonnement."
            
            # Vérifier la date de fin d'abonnement
            if date_fin:
                # Convertir la date en datetime si nécessaire
                if isinstance(date_fin, str):
                    date_fin = datetime.strptime(date_fin, '%Y-%m-%d %H:%M:%S')
                
                if date_fin < date_maintenant:
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
            plan = abonnement.get('plan', 'N/A')
            logger.info(f"Abonnement actif pour le client {client_id} (Plan: {plan})")
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
                SET statut = %s
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
                    plan,
                    prix_mensuel,
                    date_debut,
                    date_fin,
                    statut,
                    periode_essai,
                    date_fin_essai
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
    
    def get_client_id_by_email(self, email: str) -> Optional[int]:
        """
        Récupère le client_id en fonction de l'email
        
        Args:
            email: Email du client
            
        Returns:
            Optional[int]: Le client_id si trouvé, None sinon
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Chercher le client par email
            query = """
                SELECT id
                FROM abonnements
                WHERE client_id IN (
                    SELECT id FROM clients WHERE email = %s
                )
                LIMIT 1
            """
            
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            
            if result:
                logger.debug(f"Client_id trouvé pour email '{email}': {result['id']}")
                return result['id']
            
            logger.debug(f"Aucun client_id trouvé pour email '{email}'")
            return None
            
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche du client par email: {e}")
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
