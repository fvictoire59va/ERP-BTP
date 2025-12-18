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
        
        return container
    
    def _show_register(self):
        """Affiche le formulaire d'inscription"""
        self.login_container.visible = False
        self.register_container.visible = True
        self.error_label.visible = False
    
    def _show_login(self):
        """Affiche le formulaire de connexion"""
        self.register_container.visible = False
        self.login_container.visible = True
        self.register_error_label.visible = False
    
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
