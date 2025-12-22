"""
Panel d'authentification pour la connexion et l'inscription des utilisateurs
"""
from nicegui import ui
from typing import Callable

from erp.core.auth import AuthManager
from erp.core.storage_config import get_data_manager
from erp.utils.logger import get_logger

logger = get_logger(__name__)


class AuthPanel:
    """Gestion de l'interface d'authentification"""
    
    def __init__(self, on_login_success: Callable[[str, str], None]):
        """
        Args:
            on_login_success: Callback appelé lors d'une connexion réussie avec (session_id, username)
        """
        self.data_manager = get_data_manager()
        self.auth_manager = AuthManager(self.data_manager)
        self.on_login_success = on_login_success
        
        # UI elements
        self.login_container = None
        self.register_container = None
        self.reset_password_container = None
        self.error_label = None
        
    def render(self, login_container_ref=None) -> ui.column:
        """Affiche le panel d'authentification"""
        self.login_container_ref = login_container_ref
        with ui.column().classes('w-full h-full items-center justify-center bg-gray-100') as container:
            with ui.card().classes('w-96 p-6'):
                ui.label('Connexion').classes('text-2xl font-bold mb-4')
                
                # Login form
                with ui.column().classes('w-full gap-4') as self.login_container:
                    username_input = ui.input('Nom d\'utilisateur').classes('w-full')
                    password_input = ui.input('Mot de passe', password=True, password_toggle_button=True).classes('w-full')
                    
                    self.error_label = ui.label('').classes('text-red-500 text-sm')
                    self.error_label.visible = False
                    
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Se connecter', on_click=lambda: self._handle_login(
                            username_input.value, password_input.value
                        )).classes('flex-1')
                        
                        ui.button('S\'inscrire', on_click=self._show_register, color='secondary').classes('flex-1')
                    
                    # Lien mot de passe oublié (utiliser un label cliquable plutôt qu'un lien pour éviter la navigation)
                    with ui.row().classes('w-full justify-center mt-2'):
                        ui.label('Mot de passe oublié ?').classes('text-sm text-blue-600 cursor-pointer hover:underline').on('click', self._show_reset_password)
                
                # Register form (hidden by default)
                with ui.column().classes('w-full gap-4') as self.register_container:
                    self.register_container.visible = False
                    
                    reg_username = ui.input('Nom d\'utilisateur').classes('w-full')
                    reg_email = ui.input('Email').classes('w-full')
                    reg_nom = ui.input('Nom').classes('w-full')
                    reg_prenom = ui.input('Prénom').classes('w-full')
                    reg_password = ui.input('Mot de passe', password=True, password_toggle_button=True).classes('w-full')
                    reg_password_confirm = ui.input('Confirmer le mot de passe', password=True, password_toggle_button=True).classes('w-full')
                    
                    self.register_error_label = ui.label('').classes('text-red-500 text-sm')
                    self.register_error_label.visible = False
                    
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Créer le compte', on_click=lambda: self._handle_register(
                            reg_username.value,
                            reg_email.value,
                            reg_nom.value,
                            reg_prenom.value,
                            reg_password.value,
                            reg_password_confirm.value
                        )).classes('flex-1')
                        
                        ui.button('Retour', on_click=self._show_login, color='secondary').classes('flex-1')
                
                # Reset password form (hidden by default)
                with ui.column().classes('w-full gap-4') as self.reset_password_container:
                    self.reset_password_container.visible = False
                    
                    ui.label('Réinitialisation du mot de passe').classes('text-lg font-semibold')
                    ui.label('Entrez votre adresse email pour recevoir un lien de réinitialisation.').classes('text-sm text-gray-600')
                    
                    reset_email = ui.input('Email').classes('w-full')
                    
                    self.reset_error_label = ui.label('').classes('text-red-500 text-sm')
                    self.reset_error_label.visible = False
                    
                    self.reset_success_label = ui.label('').classes('text-green-600 text-sm')
                    self.reset_success_label.visible = False
                    
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Envoyer', on_click=lambda: self._handle_reset_request(
                            reset_email.value
                        )).classes('flex-1')
                        
                        ui.button('Retour', on_click=self._show_login, color='secondary').classes('flex-1')
        
        return container
    
    def _show_register(self):
        """Affiche le formulaire d'inscription"""
        self.login_container.visible = False
        self.register_container.visible = True
        self.reset_password_container.visible = False
        self.error_label.visible = False
    
    def _show_login(self):
        """Affiche le formulaire de connexion"""
        self.register_container.visible = False
        self.login_container.visible = True
        self.reset_password_container.visible = False
        if hasattr(self, 'register_error_label'):
            self.register_error_label.visible = False
        if hasattr(self, 'reset_error_label'):
            self.reset_error_label.visible = False
            self.reset_success_label.visible = False
    
    def _show_reset_password(self):
        """Affiche le formulaire de réinitialisation de mot de passe"""
        self.login_container.visible = False
        self.register_container.visible = False
        self.reset_password_container.visible = True
        self.error_label.visible = False
        self.reset_error_label.visible = False
        self.reset_success_label.visible = False
    
    def _handle_login(self, username: str, password: str):
        """Gère la tentative de connexion"""
        try:
            # Validation
            if not username or not password:
                self.error_label.text = 'Veuillez remplir tous les champs'
                self.error_label.visible = True
                return
            
            # Authentification
            result = self.auth_manager.authenticate(username, password)
            
            if result:
                user, session_id = result
                logger.info(f"User logged in: {username}")
                self.on_login_success(session_id, username)
            else:
                self.error_label.text = 'Nom d\'utilisateur ou mot de passe incorrect'
                self.error_label.visible = True
                
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            self.error_label.text = f'Erreur lors de la connexion: {str(e)}'
            self.error_label.visible = True
    
    def _handle_register(self, username: str, email: str, nom: str, prenom: str, 
                        password: str, password_confirm: str):
        """Gère la tentative d'inscription"""
        try:
            # Validation
            if not all([username, email, nom, prenom, password, password_confirm]):
                self.register_error_label.text = 'Veuillez remplir tous les champs'
                self.register_error_label.visible = True
                return
            
            if password != password_confirm:
                self.register_error_label.text = 'Les mots de passe ne correspondent pas'
                self.register_error_label.visible = True
                return
            
            if len(password) < 6:
                self.register_error_label.text = 'Le mot de passe doit contenir au moins 6 caractères'
                self.register_error_label.visible = True
                return
            
            # Vérifier si l'email est valide (simple check)
            if '@' not in email or '.' not in email.split('@')[1]:
                self.register_error_label.text = 'Adresse email invalide'
                self.register_error_label.visible = True
                return
            
            # Inscription
            result = self.auth_manager.register(
                username=username,
                email=email,
                password=password,
                nom=nom,
                prenom=prenom
            )
            
            if result:
                user, session_id = result
                logger.info(f"User registered: {username}")
                self.on_login_success(session_id, username)
            else:
                self.register_error_label.text = 'Erreur lors de la création du compte'
                self.register_error_label.visible = True
                
        except ValueError as e:
            # Username or email already exists
            self.register_error_label.text = str(e)
            self.register_error_label.visible = True
        except Exception as e:
            logger.error(f"Registration error: {e}", exc_info=True)
            self.register_error_label.text = f'Erreur lors de l\'inscription: {str(e)}'
            self.register_error_label.visible = True
    
    def _handle_reset_request(self, email: str):
        """Gère la demande de réinitialisation de mot de passe"""
        try:
            # Validation
            if not email:
                self.reset_error_label.text = 'Veuillez entrer votre adresse email'
                self.reset_error_label.visible = True
                return
            
            if '@' not in email or '.' not in email.split('@')[1]:
                self.reset_error_label.text = 'Adresse email invalide'
                self.reset_error_label.visible = True
                return
            
            # Demande de réinitialisation
            reset_token = self.auth_manager.request_password_reset(email)
            
            # Pour des raisons de sécurité, on affiche toujours un message de succès
            # même si l'email n'existe pas (pour ne pas révéler quels emails sont enregistrés)
            self.reset_error_label.visible = False
            
            if reset_token:
                # Récupérer l'utilisateur pour obtenir son nom
                user = self.data_manager.get_user_by_email(email)
                if user:
                    # Envoyer l'email de réinitialisation
                    from erp.services.email_service import get_email_service
                    email_service = get_email_service()
                    email_sent = email_service.send_password_reset_email(email, reset_token, user.username)
                    
                    if email_sent:
                        logger.info(f"Email de réinitialisation envoyé à {email}")
                        self.reset_success_label.text = 'Un email de réinitialisation a été envoyé. Vérifiez votre boîte de réception.'
                    else:
                        logger.warning(f"Échec de l'envoi de l'email à {email}, affichage du token pour développement")
                        # En développement, si l'email ne peut pas être envoyé, afficher le lien
                        import os
                        app_url = os.getenv('APP_URL', 'http://localhost:8080')
                        reset_link = f"{app_url}/reset-password?token={reset_token}"
                        self.reset_success_label.text = f'Email non configuré. Lien de réinitialisation : {reset_link}'
                    
                    self.reset_success_label.visible = True
                    
                    # Retour au formulaire de connexion après 5 secondes
                    ui.timer(5.0, lambda: self._show_login(), once=True)
            else:
                # Même si le token n'est pas créé, on affiche un message générique
                self.reset_success_label.text = 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.'
                self.reset_success_label.visible = True
                
                # Retour au formulaire de connexion après 5 secondes
                ui.timer(5.0, lambda: self._show_login(), once=True)
                
        except Exception as e:
            logger.error(f"Reset request error: {e}", exc_info=True)
            self.reset_error_label.text = f'Erreur lors de la demande: {str(e)}'
            self.reset_error_label.visible = True
    
def login_panel(on_login_success: Callable[[str, str], None], login_container_ref=None) -> ui.column:
    """
    Crée et affiche le panel de connexion
    
    Args:
        on_login_success: Callback appelé lors d'une connexion réussie avec (session_id, username)
        login_container_ref: Référence au container de login pour le cacher après connexion
    
    Returns:
        Le conteneur du panel d'authentification
    """
    panel = AuthPanel(on_login_success)
    return panel.render(login_container_ref)
