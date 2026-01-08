"""
Gestionnaire d'authentification et de sessions
"""
from typing import Optional
import uuid
from datetime import datetime, timedelta
from erp.core.models import User


class SessionManager:
    """Gestion des sessions utilisateur"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> {'user_id': str, 'expires_at': datetime}
        self.session_duration = timedelta(hours=24)  # Durée de session par défaut
        self.reset_tokens = {}  # reset_token -> {'user_id': str, 'expires_at': datetime}
        self.reset_token_duration = timedelta(hours=1)  # Durée de validité du token de réinitialisation
    
    def create_session(self, user_id: str) -> str:
        """Crée une nouvelle session pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + self.session_duration
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'expires_at': expires_at
        }
        
        return session_id
    
    def get_user_id(self, session_id: str) -> Optional[str]:
        """Récupère l'user_id depuis un session_id
        
        Args:
            session_id: ID de session
            
        Returns:
            Optional[str]: user_id si la session est valide, None sinon
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Vérifier si la session n'a pas expiré
        if datetime.now() > session['expires_at']:
            del self.sessions[session_id]
            return None
        
        return session['user_id']
    
    def delete_session(self, session_id: str):
        """Supprime une session (logout)"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Nettoie les sessions expirées"""
        now = datetime.now()
        expired = [sid for sid, session in self.sessions.items() 
                   if now > session['expires_at']]
        
        for sid in expired:
            del self.sessions[sid]
    
    def create_reset_token(self, user_id: str) -> str:
        """Crée un token de réinitialisation de mot de passe
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            str: Token de réinitialisation
        """
        reset_token = str(uuid.uuid4())
        expires_at = datetime.now() + self.reset_token_duration
        
        self.reset_tokens[reset_token] = {
            'user_id': user_id,
            'expires_at': expires_at
        }
        
        return reset_token
    
    def get_user_id_from_reset_token(self, reset_token: str) -> Optional[str]:
        """Récupère l'user_id depuis un token de réinitialisation
        
        Args:
            reset_token: Token de réinitialisation
            
        Returns:
            Optional[str]: user_id si le token est valide, None sinon
        """
        if reset_token not in self.reset_tokens:
            return None
        
        token_data = self.reset_tokens[reset_token]
        
        # Vérifier si le token n'a pas expiré
        if datetime.now() > token_data['expires_at']:
            del self.reset_tokens[reset_token]
            return None
        
        return token_data['user_id']
    
    def delete_reset_token(self, reset_token: str):
        """Supprime un token de réinitialisation après utilisation"""
        if reset_token in self.reset_tokens:
            del self.reset_tokens[reset_token]


class AuthManager:
    """Gestion de l'authentification"""
    
    def __init__(self, data_manager):
        self.dm = data_manager
        self.session_manager = SessionManager()
    
    def authenticate(self, username: str, password: str) -> Optional[tuple[User, str, Optional[str]]]:
        """Authentifie un utilisateur
        
        Args:
            username: Nom d'utilisateur ou email
            password: Mot de passe
            
        Returns:
            Optional[tuple[User, str, Optional[str]]]: (User, session_id, error_message) si succès, 
                                                        None si échec d'authentification
                                                        error_message contient le message d'erreur si abonnement expiré
        """
        from erp.utils.logger import get_logger
        logger = get_logger(__name__)
        
        user = self.dm.get_user_by_username(username)
        if user is None:
            user = self.dm.get_user_by_email(username)
        
        if user is None:
            logger.warning(f"Authentification échouée: utilisateur '{username}' non trouvé")
            return None
        
        if not user.active:
            logger.warning(f"Authentification échouée: utilisateur '{username}' inactif")
            return None
        
        # Test du mot de passe avec logs
        logger.info(f"Tentative de connexion pour: {username}")
        logger.debug(f"Salt: {user.salt[:10]}...")
        logger.debug(f"Hash stocké: {user.password_hash[:10]}...")
        
        pwd_hash, _ = User.hash_password(password, user.salt)
        logger.debug(f"Hash calculé: {pwd_hash[:10]}...")
        
        if pwd_hash != user.password_hash:
            logger.warning(f"Authentification échouée: mot de passe incorrect pour '{username}'")
            return None
        
        # Vérification de l'abonnement
        from erp.services.subscription_service import get_subscription_service
        subscription_service = get_subscription_service()
        
        # Vérifier l'abonnement si le client_id est défini
        if user.client_id:
            is_active, error_message = subscription_service.check_subscription(user.client_id)
            
            if not is_active:
                logger.warning(f"Authentification refusée: abonnement inactif pour '{username}' (client_id: {user.client_id})")
                # Retourner l'utilisateur, un session_id vide et le message d'erreur
                return user, "", error_message
        else:
            logger.info(f"Aucun client_id pour '{username}', vérification d'abonnement ignorée")
        
        # Mise à jour de la dernière connexion
        user.update_last_login()
        self.dm.update_user(user)
        
        # Créer une session
        session_id = self.session_manager.create_session(user.id)
        
        return user, session_id, None
    
    def register(self, username: str, email: str, password: str, 
                 nom: str = "", prenom: str = "") -> Optional[tuple[User, str, Optional[str]]]:
        """Inscrit un nouvel utilisateur
        
        Args:
            username: Nom d'utilisateur
            email: Email
            password: Mot de passe
            nom: Nom de famille
            prenom: Prénom
            
        Returns:
            Optional[tuple[User, str, Optional[str]]]: (User, session_id, error_message) si succès, None sinon
        """
        # Vérifier si l'utilisateur existe déjà
        if self.dm.get_user_by_username(username) is not None:
            return None
        
        if self.dm.get_user_by_email(email) is not None:
            return None
        
        # Créer l'utilisateur
        user_id = str(uuid.uuid4())
        pwd_hash, salt = User.hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=pwd_hash,
            salt=salt,
            nom=nom,
            prenom=prenom
        )
        
        self.dm.add_user(user)
        
        # Vérification de l'abonnement (pour les nouveaux comptes aussi)
        from erp.services.subscription_service import get_subscription_service
        subscription_service = get_subscription_service()
        
        # Vérifier l'abonnement si le client_id est défini
        if user.client_id:
            is_active, error_message = subscription_service.check_subscription(user.client_id)
            
            if not is_active:
                from erp.utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Registration: abonnement inactif pour '{username}' (client_id: {user.client_id})")
                return user, "", error_message
        else:
            from erp.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info(f"Aucun client_id pour '{username}', vérification d'abonnement ignorée")
        
        # Créer une session
        session_id = self.session_manager.create_session(user.id)
        
        return user, session_id, None
    
    def get_current_user(self, session_id: str) -> Optional[User]:
        """Récupère l'utilisateur courant depuis le session_id
        
        Args:
            session_id: ID de session
            
        Returns:
            Optional[User]: User si session valide, None sinon
        """
        user_id = self.session_manager.get_user_id(session_id)
        if user_id is None:
            return None
        
        return self.dm.get_user_by_id(user_id)
    
    def logout(self, session_id: str):
        """Déconnecte un utilisateur"""
        self.session_manager.delete_session(session_id)
    
    def request_password_reset(self, email: str) -> Optional[str]:
        """Demande une réinitialisation de mot de passe
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            Optional[str]: Token de réinitialisation si l'utilisateur existe, None sinon
        """
        from erp.utils.logger import get_logger
        logger = get_logger(__name__)
        
        user = self.dm.get_user_by_email(email)
        if user is None:
            logger.warning(f"Demande de réinitialisation pour email inexistant: {email}")
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
            return None
        
        if not user.active:
            logger.warning(f"Demande de réinitialisation pour utilisateur inactif: {email}")
            return None
        
        # Créer un token de réinitialisation
        reset_token = self.session_manager.create_reset_token(user.id)
        logger.info(f"Token de réinitialisation créé pour: {email}")
        
        return reset_token
    
    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Réinitialise le mot de passe avec un token
        
        Args:
            reset_token: Token de réinitialisation
            new_password: Nouveau mot de passe
            
        Returns:
            bool: True si succès, False sinon
        """
        from erp.utils.logger import get_logger
        logger = get_logger(__name__)
        
        user_id = self.session_manager.get_user_id_from_reset_token(reset_token)
        if user_id is None:
            logger.warning("Token de réinitialisation invalide ou expiré")
            return False
        
        user = self.dm.get_user_by_id(user_id)
        if user is None:
            logger.error(f"Utilisateur introuvable pour id: {user_id}")
            return False
        
        # Mettre à jour le mot de passe
        pwd_hash, salt = User.hash_password(new_password)
        user.password_hash = pwd_hash
        user.salt = salt
        
        self.dm.update_user(user)
        
        # Supprimer le token après utilisation
        self.session_manager.delete_reset_token(reset_token)
        
        logger.info(f"Mot de passe réinitialisé pour utilisateur: {user.username}")
        return True
