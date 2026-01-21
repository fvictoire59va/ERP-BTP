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
    
    def check_subscription(self, client_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si l'abonnement du client est actif
        
        Args:
            client_id: Identifiant du client (optionnel, utilise CLIENT_ID de l'environnement par défaut)
            
        Returns:
            Tuple[bool, Optional[str]]: (is_active, message)
                - is_active: True si l'abonnement est actif, False sinon
                - message: Message d'erreur ou None si actif
        """
        # Utiliser CLIENT_ID depuis les variables d'environnement si client_id n'est pas fourni
        if client_id is None:
            client_id = os.getenv('CLIENT_ID')
            if not client_id:
                logger.error("CLIENT_ID non configuré dans les variables d'environnement")
                return False, "Configuration incorrecte: CLIENT_ID manquant. Veuillez contacter le support."
            logger.debug(f"Utilisation de CLIENT_ID depuis l'environnement: {client_id}")
        
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
                    statut
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
            date_fin_essai = abonnement.get('date_fin_essai')
            
            date_maintenant = datetime.now().date()  # Utiliser .date() pour comparer avec DATE
            
            # Vérifier si le statut est suspendu
            if statut_actuel == 'suspendu':
                logger.warning(f"Tentative de connexion avec compte suspendu: {client_id}")
                return False, "Votre compte est suspendu. Veuillez renouveler votre abonnement."
            
            # Vérifier la date de fin d'essai/abonnement
            if date_fin_essai:
                # Convertir la date en date si nécessaire
                if isinstance(date_fin_essai, str):
                    date_fin_essai = datetime.strptime(date_fin_essai, '%Y-%m-%d').date()
                elif hasattr(date_fin_essai, 'date'):  # Si c'est un datetime
                    date_fin_essai = date_fin_essai.date()
                
                # Comparer les dates
                if date_fin_essai < date_maintenant:
                    if statut_actuel != 'suspendu':
                        # Mettre à jour le statut à suspendu
                        self._update_subscription_status(cursor, abonnement['id'], 'suspendu')
                        conn.commit()
                        logger.warning(f"Abonnement expiré pour {client_id}, statut mis à jour à 'suspendu'")
                        
                        # Envoyer un email d'avertissement
                        self._send_subscription_expired_email(client_id, abonnement['id'])
                    
                    return False, "Votre abonnement a expiré. Veuillez renouveler votre abonnement."
            
            # L'abonnement est actif (statut != 'suspendu' et date_fin_essai >= aujourd'hui)
            logger.info(f"Abonnement actif pour le client {client_id} (Expire le: {date_fin_essai})")
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
    
    
    def add_user_log(self, user_id: str, username: str, action: str, client_id: str = None):
        """
        Enregistre un log de connexion/déconnexion dans la base externe
        
        Args:
            user_id: ID de l'utilisateur
            username: Nom d'utilisateur
            action: Action effectuée ('login' ou 'logout')
            client_id: ID du client (optionnel, utilise CLIENT_ID de l'environnement par défaut)
        """
        conn = None
        cursor = None
        
        try:
            # Utiliser le client_id fourni, sinon récupérer depuis l'environnement
            if not client_id:
                client_id = os.getenv('CLIENT_ID')
            
            if not client_id:
                logger.warning("CLIENT_ID non configuré et non fourni, impossible d'enregistrer le log de connexion")
                return
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Timestamp actuel
            timestamp = datetime.now()
            
            # Insérer le log dans la table connexions
            query = """
                INSERT INTO connexions (client_id, username, action, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (client_id, username, action, timestamp))
            conn.commit()
            
            logger.info(f"Log de connexion enregistré: {username} - {action} à {timestamp} (client: {client_id})")
            
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de l'enregistrement du log de connexion: {e}", exc_info=True)
            if conn:
                conn.rollback()
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'enregistrement du log: {e}", exc_info=True)
            if conn:
                conn.rollback()
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _send_subscription_expired_email(self, client_id: str, abonnement_id: int):
        """
        Envoie un email d'avertissement d'expiration d'abonnement
        
        Args:
            client_id: ID du client
            abonnement_id: ID de l'abonnement
        """
        try:
            # Récupérer l'adresse email du client
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Chercher les informations du client (email)
            # On assume que client_id pourrait être un email ou on doit chercher dans une table users
            # Pour l'instant, on envoie simplement à client_id s'il ressemble à un email
            email = None
            if '@' in str(client_id):
                email = client_id
            
            if not email:
                logger.warning(f"Impossible de déterminer l'email pour le client {client_id}")
                return
            
            # Générer un token de prolongation
            import uuid
            from datetime import datetime, timedelta
            
            renewal_token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(hours=24)
            
            # Sauvegarder le token pour validation ultérieure
            # (on peut le stocker en mémoire ou dans une table de tokens)
            self._renewal_tokens = getattr(self, '_renewal_tokens', {})
            self._renewal_tokens[renewal_token] = {
                'client_id': client_id,
                'abonnement_id': abonnement_id,
                'expiry': expiry
            }
            
            # Créer le lien de prolongation
            renewal_link = f"{os.getenv('APP_URL', 'http://localhost:8080')}/renew-subscription?token={renewal_token}"
            
            # Envoyer l'email
            from erp.services.email_service import get_email_service
            email_service = get_email_service()
            email_service.send_subscription_expired_email(
                to_email=email,
                username=client_id,
                client_id=client_id,
                renewal_link=renewal_link
            )
            
            logger.info(f"Email d'expiration d'abonnement envoyé à {email}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'expiration: {e}", exc_info=True)
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass
    
    def renew_subscription(self, renewal_token: str) -> Tuple[bool, Optional[str]]:
        """
        Prolonge un abonnement en utilisant un token de prolongation
        
        Args:
            renewal_token: Token de prolongation
            
        Returns:
            Tuple[bool, Optional[str]]: (succès, message_erreur)
        """
        try:
            # Vérifier le token
            self._renewal_tokens = getattr(self, '_renewal_tokens', {})
            if renewal_token not in self._renewal_tokens:
                logger.warning(f"Token de prolongation invalide: {renewal_token}")
                return False, "Lien de prolongation invalide ou expiré"
            
            token_data = self._renewal_tokens[renewal_token]
            
            # Vérifier l'expiration
            from datetime import datetime
            if datetime.now() > token_data['expiry']:
                logger.warning(f"Token de prolongation expiré: {renewal_token}")
                del self._renewal_tokens[renewal_token]
                return False, "Lien de prolongation expiré"
            
            # Prolonger l'abonnement de 30 jours
            client_id = token_data['client_id']
            abonnement_id = token_data['abonnement_id']
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            new_expiry = (datetime.now() + timedelta(days=30)).date()
            
            query = """
                UPDATE abonnements
                SET date_fin_essai = %s,
                    statut = 'actif'
                WHERE id = %s
            """
            
            cursor.execute(query, (new_expiry, abonnement_id))
            conn.commit()
            
            # Supprimer le token utilisé
            del self._renewal_tokens[renewal_token]
            
            logger.info(f"Abonnement prolongé pour {client_id} jusqu'au {new_expiry}")
            return True, None
            
        except Exception as e:
            logger.error(f"Erreur lors de la prolongation d'abonnement: {e}", exc_info=True)
            return False, "Erreur lors de la prolongation"
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass


# Instance singleton du service
_subscription_service = None


def get_subscription_service() -> SubscriptionService:
    """Retourne l'instance singleton du service d'abonnement"""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
