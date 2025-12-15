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


class AuthManager:
    """Gestion de l'authentification"""
    
    def __init__(self, data_manager):
        self.dm = data_manager
        self.session_manager = SessionManager()
    
    def authenticate(self, username: str, password: str) -> Optional[tuple[User, str]]:
        """Authentifie un utilisateur
        
        Args:
            username: Nom d'utilisateur ou email
            password: Mot de passe
            
        Returns:
            Optional[tuple[User, str]]: (User, session_id) si succès, None sinon
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
        
        # Mise à jour de la dernière connexion
        user.update_last_login()
        self.dm.save_data()
        
        # Créer une session
        session_id = self.session_manager.create_session(user.id)
        
        return user, session_id
    
    def register(self, username: str, email: str, password: str, 
                 nom: str = "", prenom: str = "") -> Optional[tuple[User, str]]:
        """Inscrit un nouvel utilisateur
        
        Args:
            username: Nom d'utilisateur
            email: Email
            password: Mot de passe
            nom: Nom de famille
            prenom: Prénom
            
        Returns:
            Optional[tuple[User, str]]: (User, session_id) si succès, None sinon
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
        self.dm.save_data()
        
        # Créer une session
        session_id = self.session_manager.create_session(user.id)
        
        return user, session_id
    
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
