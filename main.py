from nicegui import ui, app as nicegui_app
from erp.ui.app import DevisApp
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Charger les variables d'environnement depuis .env si le fichier existe
load_dotenv()

# Variable globale pour l'instance de l'app
_app_instance = None
_styles_initialized = False

def get_app():
    """Récupère ou crée l'instance singleton de l'application"""
    global _app_instance
    if _app_instance is None:
        _app_instance = DevisApp()
    return _app_instance


def init_styles():
    """Initialise les styles globaux - doit être appelé une seule fois"""
    global _styles_initialized
    if _styles_initialized:
        return
    _styles_initialized = True
    
    # Initialiser les styles du menu
    from erp.ui.menu import initialize_menu_styles
    initialize_menu_styles()
    
    ui.add_head_html('''
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
      :root {
        --todoist-accent: #c84c3c;
        --todoist-text: #2c3e50;
        --todoist-text-secondary: #7f8c8d;
        --todoist-border: #ecf0f1;
        --todoist-bg: #fafafa;
        --todoist-bg-hover: #f5f5f5;
        --todoist-card: #ffffff;
        --todoist-sidebar: #f8f8f8;
      }
      
      * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', 
                     system-ui, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji' !important;
      }
      
      body {
        background: var(--todoist-bg);
        color: var(--todoist-text);
      }
      
      /* Headers - Clean typography */
      h1, h2, h3, h4, h5, h6 {
        color: var(--todoist-text);
        font-weight: 600;
        letter-spacing: -0.5px;
      }
      
      h1 { font-size: 28px; margin: 0; }
      h2 { font-size: 24px; margin: 0; }
      h3 { font-size: 20px; margin: 0; }
      h4 { font-size: 16px; margin: 0; }
      
      /* Buttons - Todoist style */
      button {
        border-radius: 6px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
        font-size: 14px;
      }
      
      button:hover {
        opacity: 0.9;
      }
      
      /* Primary buttons */
      .btn-primary, button[style*="background-color: #c84c3c"] {
        background-color: var(--todoist-accent) !important;
        color: white !important;
      }
      
      /* Secondary buttons */
      .btn-secondary {
        background-color: var(--todoist-border);
        color: var(--todoist-text);
      }
      
      /* Cards */
      .card, .q-card {
        background-color: var(--todoist-card);
        border: 1px solid var(--todoist-border);
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }
      
      .card:hover, .q-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      }
      
      /* Inputs */
      input, textarea, select {
        background-color: var(--todoist-card);
        border: 1px solid var(--todoist-border);
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 14px;
        color: var(--todoist-text);
        transition: all 0.2s ease;
      }
      
      input:focus, textarea:focus, select:focus {
        outline: none;
        border-color: var(--todoist-accent);
        box-shadow: 0 0 0 3px rgba(200, 76, 60, 0.1);
      }
      
      /* Select dropdowns - Hide Material Icons text */
      .q-select__native, select, .q-field__control {
        background-image: none !important;
      }
      
      /* Material Icons - Fix display */
      .material-icons {
        font-family: 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 24px !important;
        display: inline-block !important;
        line-height: 1 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
      }
      
      /* Hide Material Icon text names in selects */
      .q-select .q-icon {
        font-size: 18px;
      }
      
      /* Sidebar */
      .sidebar {
        background-color: var(--todoist-sidebar);
        border-right: 1px solid var(--todoist-border);
      }
      
      .sidebar-item {
        padding: 12px 16px;
        cursor: pointer;
        transition: all 0.15s ease;
        color: var(--todoist-text-secondary);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 12px;
      }
      
      .sidebar-item:hover {
        background-color: var(--todoist-bg-hover);
        color: var(--todoist-text);
      }
      
      .sidebar-item.active {
        background-color: rgba(200, 76, 60, 0.1);
        color: var(--todoist-accent);
        border-left: 3px solid var(--todoist-accent);
        padding-left: 13px;
      }
      
      /* Tabs */
      .tabs {
        display: flex;
        border-bottom: 1px solid var(--todoist-border);
        gap: 24px;
      }
      
      .tab {
        padding: 12px 0;
        cursor: pointer;
        color: var(--todoist-text-secondary);
        font-weight: 500;
        border-bottom: 3px solid transparent;
        transition: all 0.2s ease;
      }
      
      .tab:hover {
        color: var(--todoist-text);
      }
      
      .tab.active {
        color: var(--todoist-accent);
        border-bottom-color: var(--todoist-accent);
      }
      
      /* Badges */
      .badge {
        display: inline-block;
        padding: 4px 8px;
        background-color: rgba(200, 76, 60, 0.1);
        color: var(--todoist-accent);
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
      }
      
      /* List items */
      .list-item {
        padding: 12px 16px;
        border-bottom: 1px solid var(--todoist-border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.15s ease;
      }
      
      .list-item:hover {
        background-color: var(--todoist-bg-hover);
      }
      
      .list-item.selected {
        background-color: rgba(200, 76, 60, 0.05);
        border-left: 3px solid var(--todoist-accent);
        padding-left: 13px;
      }
      
      /* Hide tab navigation arrows */
      .q-tabs__arrow,
      .q-tabs > button,
      .q-tabs [role="button"] {
        display: none !important;
      }
      
      /* Reduce row spacing in tables */
      .q-row {
        min-height: auto !important;
        margin: 0 !important;
      }
      
      /* Tighten table rows */
      .w-full.gap-2.p-1 {
        margin-bottom: -1px !important;
      }
      
      /* Hide spinners on number inputs - all states */
      .no-spinner input::-webkit-outer-spin-button,
      .no-spinner input::-webkit-inner-spin-button,
      .no-spinner .q-field__control input::-webkit-outer-spin-button,
      .no-spinner .q-field__control input::-webkit-inner-spin-button,
      .no-spinner .q-field input::-webkit-outer-spin-button,
      .no-spinner .q-field input::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
      }
      
      .no-spinner input[type=number],
      .no-spinner .q-field__control input[type=number],
      .no-spinner .q-field input[type=number] {
        -moz-appearance: textfield !important;
      }
      
      .no-spinner input[type=number]:hover::-webkit-outer-spin-button,
      .no-spinner input[type=number]:hover::-webkit-inner-spin-button,
      .no-spinner input[type=number]:focus::-webkit-outer-spin-button,
      .no-spinner input[type=number]:focus::-webkit-inner-spin-button,
      .no-spinner .q-field__control input[type=number]:hover::-webkit-outer-spin-button,
      .no-spinner .q-field__control input[type=number]:hover::-webkit-inner-spin-button,
      .no-spinner .q-field__control input[type=number]:focus::-webkit-outer-spin-button,
      .no-spinner .q-field__control input[type=number]:focus::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
      }
      
      /* Force hide all number spinners globally */
      input[type=number]::-webkit-outer-spin-button,
      input[type=number]::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
        display: none !important;
      }
      
      input[type=number] {
        -moz-appearance: textfield !important;
      }
    </style>
    <script>
      // Force remove spinners on all number inputs after page load
      document.addEventListener('DOMContentLoaded', function() {
        const style = document.createElement('style');
        style.textContent = `
          input[type=number]::-webkit-outer-spin-button,
          input[type=number]::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
            display: none !important;
          }
          input[type=number] {
            -moz-appearance: textfield !important;
          }
        `;
        document.head.appendChild(style);
      });
    </script>
    ''')


# Routes API qui n'ont pas besoin d'authentification
def is_api_route(path: str) -> bool:
    """Vérifier si c'est une route API publique"""
    return path.startswith('/api/subscriptions/') or path.startswith('/api/stripe/')

unrestricted_page_routes = {'/login', '/reset-password', '/forgot-password', '/welcome', '/renew-subscription', '/payment-success', '/payment-cancelled', '/pricing'}

# Créer une instance globale de l'AuthManager (partagée entre toutes les pages)
from erp.core.auth import AuthManager
from erp.core.storage_config import get_data_manager

_data_manager = get_data_manager()
_auth_manager = AuthManager(_data_manager)

# Initialiser un utilisateur admin si aucun utilisateur n'existe
def _init_default_admin():
    """Crée un utilisateur admin par défaut si aucun utilisateur n'existe"""
    from erp.utils.logger import get_logger
    from erp.core.models import User
    import uuid
    
    logger = get_logger('main')
    
    # Vérifier s'il existe déjà des utilisateurs
    try:
        users = _data_manager.users
        if len(users) > 0:
            logger.info(f"{len(users)} utilisateur(s) déjà existant(s) dans la base")
            return
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des utilisateurs: {e}")
        return
    
    # Récupérer les variables d'environnement
    initial_username = os.getenv('INITIAL_USERNAME', 'admin')
    initial_password = os.getenv('INITIAL_PASSWORD', 'admin123')
    
    # Retirer les guillemets si présents (ajoutés dans Portainer pour les caractères spéciaux)
    if initial_password.startswith('"') and initial_password.endswith('"'):
        initial_password = initial_password[1:-1]
    elif initial_password.startswith("'") and initial_password.endswith("'"):
        initial_password = initial_password[1:-1]
    
    # Log détaillé des paramètres pour déboguer les problèmes de caractères spéciaux
    logger.debug(f"INITIAL_PASSWORD reçu: '{initial_password}' (longueur: {len(initial_password)}, bytes: {initial_password.encode('utf-8')})")
    
    # Vérifier que le mot de passe n'a pas été tronqué par Portainer
    # Le caractère # est interprété comme commentaire dans les fichiers .env/YAML
    # Les caractères spéciaux comme # ? & doivent être entre guillemets dans Portainer
    if initial_password and len(initial_password) < 8:
        logger.warning(
            f"⚠️ ATTENTION: Le mot de passe semble avoir été tronqué (longueur: {len(initial_password)}). "
            f"Valeur reçue: '{initial_password}'. "
            f"Cela peut se produire si le mot de passe contient des caractères spéciaux (# ? & etc). "
            f"⚠️ SOLUTION: Entourez INITIAL_PASSWORD de guillemets dans Portainer : \"HWVnDsZ+W#9W\""
        )
    
    logger.info(f"Aucun utilisateur trouvé, création de l'admin par défaut: {initial_username}")
    
    try:
        # Créer le hash du mot de passe
        password_hash, salt = User.hash_password(initial_password)
        
        # Créer l'utilisateur admin
        admin_user = User(
            id=str(uuid.uuid4()),
            username=initial_username,
            email=f"{initial_username}@erp-btp.local",
            password_hash=password_hash,
            salt=salt,
            nom="Administrateur",
            prenom="Système",
            role="admin",
            active=True
        )
        
        # Ajouter à la base de données
        _data_manager.add_user(admin_user)
        
        app_url = os.getenv('APP_URL', 'http://localhost:8080')
        
        logger.info("=" * 70)
        logger.info("🎉 FÉLICITATIONS ! Votre ERP BTP est configuré avec succès !")
        logger.info("=" * 70)
        logger.info(f"")
        logger.info(f"  ✓ Utilisateur admin créé")
        logger.info(f"")
        logger.info(f"  📋 INFORMATIONS DE CONNEXION:")
        logger.info(f"  ├─ URL d'accès   : {app_url}/welcome")
        logger.info(f"  ├─ Nom d'utilisateur : {initial_username}")
        logger.info(f"  └─ Mot de passe      : {initial_password}")
        logger.info(f"")
        logger.info(f"  ⚠️  IMPORTANT: Changez ce mot de passe après la première connexion !")
        logger.info(f"")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur admin: {e}", exc_info=True)

# Initialiser l'admin au démarrage
_init_default_admin()

# Page de bienvenue (première installation)
@ui.page('/welcome')
def welcome_page():
    """Page de bienvenue affichant les identifiants du premier utilisateur"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    init_styles()
    
    initial_username = os.getenv('INITIAL_USERNAME', 'admin')
    initial_password = os.getenv('INITIAL_PASSWORD', 'admin123')
    
    # Retirer les guillemets si présents (ajoutés dans Portainer pour les caractères spéciaux)
    if initial_password.startswith('"') and initial_password.endswith('"'):
        initial_password = initial_password[1:-1]
    elif initial_password.startswith("'") and initial_password.endswith("'"):
        initial_password = initial_password[1:-1]
    
    app_url = os.getenv('APP_URL', 'http://localhost:8080')
    
    with ui.column().classes('w-full h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100'):
        with ui.card().classes('w-[600px] p-8 shadow-xl'):
            # Icône de succès
            with ui.row().classes('w-full justify-center mb-4'):
                ui.html('<div style="font-size: 64px;">🎉</div>', sanitize=False)
            
            ui.label('Félicitations !').classes('text-3xl font-bold text-center mb-2 text-green-600')
            ui.label('Votre ERP BTP est prêt').classes('text-xl text-center mb-6 text-gray-700')
            
            # Informations de connexion
            with ui.card().classes('w-full p-6 bg-blue-50 border-2 border-blue-200 mb-6'):
                ui.label('Informations de connexion').classes('text-lg font-semibold mb-4 text-blue-800')
                
                with ui.row().classes('w-full items-center gap-4 mb-3'):
                    ui.label('🌐 URL :').classes('font-semibold text-gray-700 w-32')
                    url_input = ui.input(value=app_url).classes('flex-1')
                    url_input.props('readonly')
                
                with ui.row().classes('w-full items-center gap-4 mb-3'):
                    ui.label('👤 Nom d\'utilisateur :').classes('font-semibold text-gray-700 w-32')
                    user_input = ui.input(value=initial_username).classes('flex-1')
                    user_input.props('readonly')
                
                with ui.row().classes('w-full items-center gap-4'):
                    ui.label('🔑 Mot de passe :').classes('font-semibold text-gray-700 w-32')
                    pwd_input = ui.input(value=initial_password, password=True, password_toggle_button=True).classes('flex-1')
                    pwd_input.props('readonly')
            
            # Avertissement de sécurité
            with ui.card().classes('w-full p-4 bg-yellow-50 border-2 border-yellow-300 mb-6'):
                ui.html('<div class="flex items-start gap-3"><div style="font-size: 24px;">⚠️</div><div>', sanitize=False)
                ui.label('Important : Changez ce mot de passe dès la première connexion !').classes('font-semibold text-yellow-800')
                ui.label('Pour des raisons de sécurité, modifiez le mot de passe par défaut dans les paramètres de votre compte.').classes('text-sm text-yellow-700 mt-1')
                ui.html('</div></div>', sanitize=False)
            
            # Bouton de connexion
            ui.button('Se connecter', on_click=lambda: ui.navigate.to('/login')).classes('w-full').style(
                'background-color: #4CAF50; color: white; padding: 12px; font-size: 16px; font-weight: bold;'
            )
            
            # Instructions supplémentaires
            with ui.expansion('📖 Premiers pas', icon='help').classes('w-full mt-4'):
                ui.markdown('''
                **Que faire ensuite ?**
                
                1. Connectez-vous avec les identifiants ci-dessus
                2. Accédez aux **Paramètres** pour :
                   - Changer votre mot de passe
                   - Configurer les informations de votre entreprise
                   - Personnaliser l'application
                3. Créez vos premiers clients, devis et projets
                
                **Besoin d'aide ?**  
                Consultez la documentation ou contactez le support technique.
                ''')

# Page de demande de réinitialisation de mot de passe
@ui.page('/forgot-password')
def forgot_password_page():
    """Page de demande de réinitialisation de mot de passe"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')

    init_styles()

    with ui.column().classes('w-full h-full items-center justify-center bg-gray-100'):
        with ui.card().classes('w-96 p-6'):
            ui.label('Mot de passe oublié ?').classes('text-2xl font-bold mb-4')
            ui.label('Entrez votre adresse email pour recevoir un lien de réinitialisation.').classes('text-sm text-gray-600 mb-4')

            email_input = ui.input('Email').classes('w-full')

            error_label = ui.label('').classes('text-red-500 text-sm')
            error_label.visible = False

            success_label = ui.label('').classes('text-green-600 text-sm')
            success_label.visible = False

            def send_reset_email():
                error_label.visible = False
                success_label.visible = False

                # Validation
                if not email_input.value:
                    error_label.text = 'Veuillez entrer votre adresse email'
                    error_label.visible = True
                    return

                if '@' not in email_input.value or '.' not in email_input.value.split('@')[1]:
                    error_label.text = 'Adresse email invalide'
                    error_label.visible = True
                    return

                # Demande de réinitialisation
                reset_token = _auth_manager.request_password_reset(email_input.value)

                # Pour des raisons de sécurité, on affiche toujours un message de succès
                if reset_token:
                    user = _data_manager.get_user_by_email(email_input.value)
                    if user:
                        # Envoyer l'email de réinitialisation
                        from erp.services.email_service import get_email_service
                        email_service = get_email_service()
                        email_sent = email_service.send_password_reset_email(email_input.value, reset_token, user.username)

                        if email_sent:
                            logger.info(f"Email de réinitialisation envoyé à {email_input.value}")
                            success_label.text = 'Un email de réinitialisation a été envoyé. Vérifiez votre boîte de réception.'
                        else:
                            logger.warning(f"Échec de l'envoi de l'email à {email_input.value}, affichage du token pour développement")
                            # En développement, si l'email ne peut pas être envoyé, afficher le lien
                            import os
                            app_url = os.getenv('APP_URL', 'http://localhost:8080')
                            reset_link = f"{app_url}/reset-password?token={reset_token}"
                            success_label.text = f'Email non configuré. Lien de réinitialisation : {reset_link}'

                        success_label.visible = True

                        # Retour au login après 5 secondes
                        ui.timer(5.0, lambda: ui.navigate.to('/login'), once=True)
                else:
                    # Même si le token n'est pas créé, on affiche un message générique
                    success_label.text = 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.'
                    success_label.visible = True
                    ui.timer(5.0, lambda: ui.navigate.to('/login'), once=True)

            with ui.row().classes('w-full gap-2 mt-4'):
                ui.button('Envoyer', on_click=send_reset_email).classes('flex-1')
                ui.button('Retour', on_click=lambda: ui.navigate.to('/login'), color='secondary').classes('flex-1')

# Page de réinitialisation de mot de passe avec token
@ui.page('/reset-password')
def reset_password_page(token: str = ''):
    """Page de réinitialisation de mot de passe avec token"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    init_styles()
    
    with ui.column().classes('w-full h-full items-center justify-center bg-gray-100'):
        with ui.card().classes('w-96 p-6'):
            if not token:
                ui.label('Lien invalide').classes('text-2xl font-bold mb-4 text-red-600')
                ui.label('Le lien de réinitialisation est invalide ou manquant.').classes('text-sm text-gray-600 mb-4')
                ui.button('Retour à la connexion', on_click=lambda: ui.navigate.to('/login')).classes('w-full')
                return
            
            # Vérifier si le token est valide
            user_id = _auth_manager.session_manager.get_user_id_from_reset_token(token)
            if not user_id:
                ui.label('Lien expiré').classes('text-2xl font-bold mb-4 text-red-600')
                ui.label('Ce lien de réinitialisation a expiré ou a déjà été utilisé.').classes('text-sm text-gray-600 mb-4')
                ui.button('Demander un nouveau lien', on_click=lambda: ui.navigate.to('/login')).classes('w-full')
                return
            
            # Formulaire de nouveau mot de passe
            ui.label('Nouveau mot de passe').classes('text-2xl font-bold mb-4')
            ui.label('Entrez votre nouveau mot de passe.').classes('text-sm text-gray-600 mb-4')
            
            new_password = ui.input('Nouveau mot de passe', password=True, password_toggle_button=True).classes('w-full')
            confirm_password = ui.input('Confirmer le mot de passe', password=True, password_toggle_button=True).classes('w-full')
            
            error_label = ui.label('').classes('text-red-500 text-sm')
            error_label.visible = False
            
            def reset_password():
                if not new_password.value or not confirm_password.value:
                    error_label.text = 'Veuillez remplir tous les champs'
                    error_label.visible = True
                    return
                
                if new_password.value != confirm_password.value:
                    error_label.text = 'Les mots de passe ne correspondent pas'
                    error_label.visible = True
                    return
                
                if len(new_password.value) < 6:
                    error_label.text = 'Le mot de passe doit contenir au moins 6 caractères'
                    error_label.visible = True
                    return
                
                # Réinitialiser le mot de passe
                success = _auth_manager.reset_password(token, new_password.value)
                
                if success:
                    logger.info("Mot de passe réinitialisé avec succès via email")
                    ui.notify('Mot de passe réinitialisé avec succès ! Vous pouvez maintenant vous connecter.', type='positive')
                    ui.navigate.to('/login')
                else:
                    error_label.text = 'Erreur lors de la réinitialisation. Le lien a peut-être expiré.'
                    error_label.visible = True
            
            ui.button('Réinitialiser', on_click=reset_password).classes('w-full mt-4')

# Page de login
@ui.page('/login')
def login_page(redirect_to: str = '/'):
    """Page de connexion"""
    # Initialiser les styles
    init_styles()
    
    # Si déjà authentifié, rediriger
    if nicegui_app.storage.user.get('authenticated', False):
      return RedirectResponse('/')
    
    def try_login():
        from erp.utils.logger import get_logger
        logger = get_logger('main')
        
        logger.info(f"=== LOGIN ATTEMPT: username={username.value} ===")
        
        result = _auth_manager.authenticate(username.value, password.value)
        logger.info(f"Authentication result: {result is not None}")
        
        if result:
            user, session_id, error_message = result
            
            # Vérifier si l'abonnement est expiré ou suspendu
            if error_message:
                logger.warning(f"✗ LOGIN BLOCKED for {username.value}: {error_message}")
                
                # Générer un token de prolongation et rediriger
                from erp.services.subscription_service import get_subscription_service
                import uuid
                from datetime import datetime, timedelta
                
                subscription_service = get_subscription_service()
                renewal_token = str(uuid.uuid4())
                expiry = datetime.now() + timedelta(hours=24)
                
                subscription_service._renewal_tokens = getattr(subscription_service, '_renewal_tokens', {})
                subscription_service._renewal_tokens[renewal_token] = {
                    'client_id': user.email or username.value,
                    'expiry': expiry
                }
                
                # Rediriger vers la page de renouvellement
                renewal_link = f"/renew-subscription?token={renewal_token}&client_id={user.email or username.value}"
                logger.info(f"Redirecting to renewal page: {renewal_link}")
                ui.navigate.to(renewal_link)
                return
            
            logger.info(f"✓ USER LOGGED IN: {user.username} (session: {session_id})")
            
            nicegui_app.storage.user.update({
                'username': user.username,
                'session_id': session_id,
                'authenticated': True
            })
            
            logger.info(f"Storage updated: {dict(nicegui_app.storage.user)}")
            logger.info(f"Navigating to: {redirect_to}")
            
            ui.navigate.to(redirect_to)
        else:
            logger.warning(f"✗ LOGIN FAILED for username: {username.value}")
            ui.notify('Nom d\'utilisateur ou mot de passe incorrect', color='negative')
    
    with ui.column().classes('w-full h-screen items-center justify-center bg-gray-100'):
        with ui.card().classes('w-96 p-6'):
            ui.label('Connexion ERP BTP').classes('text-2xl font-bold mb-4')
            username = ui.input('Nom d\'utilisateur').classes('w-full').on('keydown.enter', try_login)
            password = ui.input('Mot de passe', password=True, password_toggle_button=True).classes('w-full').on('keydown.enter', try_login)
            ui.button('Se connecter', on_click=try_login).classes('w-full')
            
            # Lien mot de passe oublié
            with ui.row().classes('w-full justify-center mt-4'):
                ui.link('Mot de passe oublié ?', '/forgot-password').classes('text-sm text-blue-600')
    
    return None


# Page de renouvellement d'abonnement
@ui.page('/renew-subscription')
def renew_subscription_page(request: Request):
    """Page pour renouveler un abonnement expiré avec choix du plan"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    logger.info("=== RENEW SUBSCRIPTION PAGE CALLED ===")
    
    # Récupérer les paramètres URL
    renewal_token = request.query_params.get('token')
    client_id = request.query_params.get('client_id')
    
    # Initialiser les styles
    init_styles()
    
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-8'):
        with ui.card().classes('w-full max-w-4xl p-8 shadow-xl'):
            # En-tête
            with ui.row().classes('w-full justify-center mb-6'):
                ui.html('<div style="font-size: 48px;">⚠️</div>', sanitize=False)
            
            ui.label('Votre abonnement a expiré').classes('text-3xl font-bold text-center mb-2 text-orange-600')
            ui.label('Choisissez un plan pour continuer à utiliser ERP BTP').classes('text-lg text-center mb-8 text-gray-600')
            
            # Conteneur pour les plans
            plans_container = ui.row().classes('w-full justify-center gap-6 mb-8')
            
            # Récupérer les plans depuis le service Stripe
            from erp.services.stripe_service import get_stripe_service
            stripe_service = get_stripe_service()
            plans = stripe_service.get_plans()
            
            selected_plan = {'value': None}
            plan_cards = {}
            
            with plans_container:
                for plan_id, plan_info in plans.items():
                    with ui.card().classes('w-72 p-6 cursor-pointer transition-all hover:shadow-lg border-2 border-transparent') as card:
                        plan_cards[plan_id] = card
                        
                        # Badge pour le plan recommandé
                        if plan_id == 'annuel':
                            ui.badge('🏆 Meilleur rapport qualité/prix', color='green').classes('mb-4')
                        
                        ui.label(plan_info['name']).classes('text-xl font-bold mb-2')
                        ui.label(plan_info['price_display']).classes('text-3xl font-bold text-blue-600 mb-4')
                        
                        if plan_id == 'annuel':
                            # Calculer l'économie
                            monthly_yearly = plans['mensuel']['price'] * 12
                            savings = monthly_yearly - plan_info['price']
                            ui.label(f'💰 Économisez {savings:.0f}€/an').classes('text-green-600 text-sm mb-4')
                        else:
                            ui.label(f'{plan_info["duration_days"]} jours').classes('text-gray-500 text-sm mb-4')
                        
                        # Fonctionnalités
                        with ui.column().classes('gap-2 mb-6'):
                            for feature in plan_info['features']:
                                with ui.row().classes('items-center gap-2'):
                                    ui.html('<span style="color: green;">✓</span>', sanitize=False)
                                    ui.label(feature).classes('text-sm text-gray-600')
                        
                        def select_plan(p=plan_id, c=card):
                            selected_plan['value'] = p
                            # Mettre à jour les styles
                            for pid, pcard in plan_cards.items():
                                if pid == p:
                                    pcard.classes('border-blue-500 bg-blue-50', remove='border-transparent')
                                else:
                                    pcard.classes('border-transparent', remove='border-blue-500 bg-blue-50')
                        
                        card.on('click', select_plan)
            
            # Message d'erreur
            error_label = ui.label('').classes('text-red-500 text-center mb-4')
            error_label.visible = False
            
            # Boutons d'action
            with ui.row().classes('w-full justify-center gap-4'):
                async def proceed_to_payment():
                    if not selected_plan['value']:
                        error_label.text = 'Veuillez sélectionner un plan'
                        error_label.visible = True
                        return
                    
                    error_label.visible = False
                    
                    # Créer la session Stripe
                    checkout_url, error = stripe_service.create_checkout_session(
                        plan=selected_plan['value'],
                        client_id=client_id or 'unknown',
                        client_email=client_id if client_id and '@' in client_id else f'{client_id}@client.erp-btp.fr'
                    )
                    
                    if checkout_url:
                        logger.info(f"Redirecting to Stripe checkout: {checkout_url}")
                        ui.run_javascript(f'window.location.href = "{checkout_url}"')
                    else:
                        error_label.text = f'Erreur: {error}'
                        error_label.visible = True
                
                ui.button('💳 Procéder au paiement', on_click=proceed_to_payment).classes(
                    'px-8 py-3 text-lg'
                ).style('background-color: #4CAF50; color: white; font-weight: bold;')
                
                ui.button('Retour', on_click=lambda: ui.navigate.to('/login')).classes(
                    'px-8 py-3 text-lg bg-gray-400'
                )
            
            # Informations de sécurité
            with ui.row().classes('w-full justify-center mt-8 gap-4 text-gray-500 text-sm'):
                ui.html('🔒 Paiement sécurisé par Stripe', sanitize=False)
                ui.html('|', sanitize=False)
                ui.html('💳 Cartes Visa, Mastercard, Amex acceptées', sanitize=False)
    
    return None


# Page de succès de paiement
@ui.page('/payment-success')
def payment_success_page(request: Request):
    """Page affichée après un paiement réussi"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    session_id = request.query_params.get('session_id')
    
    init_styles()
    
    with ui.column().classes('w-full h-screen items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100'):
        with ui.card().classes('w-[500px] p-8 shadow-xl text-center'):
            ui.html('<div style="font-size: 64px;">🎉</div>', sanitize=False)
            
            ui.label('Paiement réussi !').classes('text-3xl font-bold text-green-600 mb-4')
            ui.label('Merci pour votre confiance.').classes('text-xl text-gray-700 mb-2')
            ui.label('Votre abonnement a été activé avec succès.').classes('text-gray-600 mb-6')
            
            # Récupérer les détails de la session si disponible
            if session_id:
                try:
                    from erp.services.stripe_service import get_stripe_service
                    stripe_service = get_stripe_service()
                    details = stripe_service.get_session_details(session_id)
                    
                    if details:
                        with ui.card().classes('w-full p-4 bg-green-50 mb-6'):
                            ui.label('Détails du paiement').classes('font-semibold mb-2')
                            ui.label(f"Montant: {details.get('amount_total', 0) / 100:.2f}€").classes('text-sm')
                            ui.label(f"Email: {details.get('customer_email', 'N/A')}").classes('text-sm')
                except Exception as e:
                    logger.error(f"Error fetching session details: {e}")
            
            ui.button('Se connecter', on_click=lambda: ui.navigate.to('/login')).classes('w-full').style(
                'background-color: #4CAF50; color: white; padding: 12px; font-size: 16px; font-weight: bold;'
            )
            
            logger.info(f"Payment success page displayed for session: {session_id}")
    
    return None


# Page d'annulation de paiement
@ui.page('/payment-cancelled')
def payment_cancelled_page():
    """Page affichée après annulation d'un paiement"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    init_styles()
    
    with ui.column().classes('w-full h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100'):
        with ui.card().classes('w-[500px] p-8 shadow-xl text-center'):
            ui.html('<div style="font-size: 64px;">😕</div>', sanitize=False)
            
            ui.label('Paiement annulé').classes('text-3xl font-bold text-gray-600 mb-4')
            ui.label('Vous avez annulé le processus de paiement.').classes('text-gray-600 mb-6')
            
            with ui.row().classes('w-full gap-4 justify-center'):
                ui.button('Réessayer', on_click=lambda: ui.navigate.to('/renew-subscription')).style(
                    'background-color: #2196F3; color: white; padding: 12px 24px;'
                )
                ui.button('Retour', on_click=lambda: ui.navigate.to('/login')).style(
                    'background-color: #9e9e9e; color: white; padding: 12px 24px;'
                )
            
            logger.info("Payment cancelled page displayed")
    
    return None


# Page de tarification (accessible sans connexion)
@ui.page('/pricing')
def pricing_page():
    """Page publique affichant les tarifs"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')
    
    init_styles()
    
    with ui.column().classes('w-full min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100'):
        # Header
        with ui.row().classes('w-full p-6 justify-between items-center'):
            ui.label('ERP BTP').classes('text-2xl font-bold text-blue-600')
            ui.button('Se connecter', on_click=lambda: ui.navigate.to('/login')).classes('bg-blue-600')
        
        # Contenu principal
        with ui.column().classes('w-full items-center p-8'):
            ui.label('Tarifs').classes('text-4xl font-bold mb-2')
            ui.label('Choisissez le plan adapté à vos besoins').classes('text-xl text-gray-600 mb-12')
            
            # Récupérer les plans
            from erp.services.stripe_service import get_stripe_service
            stripe_service = get_stripe_service()
            plans = stripe_service.get_plans()
            
            with ui.row().classes('w-full max-w-4xl justify-center gap-8'):
                for plan_id, plan_info in plans.items():
                    is_popular = plan_id == 'annuel'
                    
                    with ui.card().classes(f'w-80 p-8 {"shadow-xl border-2 border-blue-500" if is_popular else "shadow-lg"}'):
                        if is_popular:
                            ui.badge('POPULAIRE', color='blue').classes('mb-4')
                        
                        ui.label(plan_info['name']).classes('text-2xl font-bold mb-4')
                        
                        with ui.row().classes('items-end mb-6'):
                            ui.label(f"{plan_info['price']:.0f}€").classes('text-4xl font-bold text-blue-600')
                            period = '/mois' if plan_id == 'mensuel' else '/an'
                            ui.label(period).classes('text-gray-500 ml-1 mb-1')
                        
                        if plan_id == 'annuel':
                            monthly_yearly = plans['mensuel']['price'] * 12
                            savings = monthly_yearly - plan_info['price']
                            ui.label(f'💰 Économisez {savings:.0f}€/an').classes('text-green-600 mb-6')
                        
                        with ui.column().classes('gap-3 mb-8'):
                            for feature in plan_info['features']:
                                with ui.row().classes('items-center gap-2'):
                                    ui.html('<span style="color: #4CAF50; font-size: 18px;">✓</span>', sanitize=False)
                                    ui.label(feature).classes('text-gray-600')
                        
                        ui.button(
                            'Commencer maintenant',
                            on_click=lambda: ui.navigate.to('/login')
                        ).classes('w-full').style(
                            f'background-color: {"#2196F3" if is_popular else "#e0e0e0"}; '
                            f'color: {"white" if is_popular else "#333"};'
                        )
            
            # Section FAQ
            with ui.column().classes('w-full max-w-2xl mt-16'):
                ui.label('Questions fréquentes').classes('text-2xl font-bold mb-6 text-center')
                
                with ui.expansion('Comment fonctionne la période d\'essai ?').classes('w-full mb-2'):
                    ui.label(
                        'Vous bénéficiez de 30 jours d\'essai gratuit avec un accès complet à toutes les '
                        'fonctionnalités. Aucune carte bancaire n\'est requise pour commencer.'
                    )
                
                with ui.expansion('Puis-je changer de plan ?').classes('w-full mb-2'):
                    ui.label(
                        'Oui, vous pouvez passer du plan mensuel au plan annuel à tout moment. '
                        'Le changement prendra effet à la fin de votre période de facturation actuelle.'
                    )
                
                with ui.expansion('Quels moyens de paiement acceptez-vous ?').classes('w-full mb-2'):
                    ui.label(
                        'Nous acceptons les cartes Visa, Mastercard et American Express via notre '
                        'partenaire de paiement sécurisé Stripe.'
                    )
                
                with ui.expansion('Puis-je annuler mon abonnement ?').classes('w-full mb-2'):
                    ui.label(
                        'Oui, vous pouvez annuler votre abonnement à tout moment depuis les paramètres '
                        'de votre compte. Vous conserverez l\'accès jusqu\'à la fin de votre période payée.'
                    )
    
    return None


# Page principale 
from nicegui import app as nicegui_app
from starlette.requests import Request
import asyncio

@ui.page('/')
def index_page(request: Request):
    """Page principale de l'application"""
    from erp.utils.logger import get_logger
    logger = get_logger('main')

    logger.info("=== INDEX PAGE CALLED ===")
    logger.info(f"Storage contents: {dict(nicegui_app.storage.user)}")

    # Initialiser les styles
    init_styles()

    # Récupérer la session
    session_id = nicegui_app.storage.user.get('session_id')
    logger.info(f"Session ID from storage: {session_id}")

    # Vérifier que la session est valide avec l'auth_manager global
    current_user = _auth_manager.get_current_user(session_id)
    logger.info(f"Current user: {current_user}")

    if not current_user:
        logger.warning("No valid user, redirecting to login")
        nicegui_app.storage.user.clear()
        return RedirectResponse('/login')

    logger.info(f"Creating main UI for user {current_user.username}")

    # Charger le thème depuis le storage utilisateur
    from erp.config.theme import get_theme, set_accent_color
    saved_color = nicegui_app.storage.user.get('theme_accent_color', '#c84c3c')
    logger.info(f"Theme color from storage: {saved_color}")
    set_accent_color(saved_color, save_to_storage=False)

    # Créer l'interface principale
    app = get_app()
    app.current_user = current_user
    app.session_id = session_id

    # Appliquer le thème via CSS avant de créer l'UI
    ui.run_javascript(f'''
        document.documentElement.style.setProperty('--todoist-accent', '{saved_color}');
        document.documentElement.style.setProperty('--q-primary', '{saved_color}');
        document.documentElement.style.setProperty('--q-positive', '{saved_color}');
        document.body.style.setProperty('--todoist-accent', '{saved_color}');
        document.body.style.setProperty('--q-primary', '{saved_color}');
    ''')

    # Forcer la section par défaut sur la liste des devis et afficher la structure complète
    app.current_section = {'value': 'liste_devis'}
    app.create_main_ui(default_subsection='liste')
    logger.info("Affichage de la structure complète avec la liste des devis sur la page d'accueil")


def main():
    """Configure l'application"""
    # Gestion des chemins pour PyInstaller
    if getattr(sys, 'frozen', False):
        # Mode exécutable: utiliser le dossier de l'exécutable
        base_path = Path(sys.executable).parent
    else:
        # Mode développement
        base_path = Path(__file__).parent
    
    # Serve static files from data and static directories
    nicegui_app.add_static_files('/data', str(base_path / 'data'))
    nicegui_app.add_static_files('/static', str(base_path / 'static'))
    
    # ==================== API ROUTES ====================
    
    @nicegui_app.post("/api/subscriptions/renew")
    async def renew_subscription_api(request):
        """
        API endpoint pour prolonger un abonnement
        
        Body:
            {
                "renewal_token": "token_uuid",
                "client_id": "client_email_or_id"
            }
        
        Response:
            {
                "success": bool,
                "message": str,
                "new_expiry": date (si succès)
            }
        """
        try:
            from erp.services.subscription_service import get_subscription_service
            from erp.utils.logger import get_logger
            
            logger = get_logger(__name__)
            
            # Récupérer les données du body
            body = await request.json()
            renewal_token = body.get('renewal_token')
            client_id = body.get('client_id')
            
            if not renewal_token:
                return {
                    'success': False,
                    'message': 'renewal_token est requis'
                }
            
            # Appeler le service pour prolonger
            subscription_service = get_subscription_service()
            success, error_message = subscription_service.renew_subscription(renewal_token)
            
            if success:
                logger.info(f"Subscription renewed via API for client {client_id}")
                # Calculer la nouvelle date d'expiration (30 jours à partir de maintenant)
                from datetime import datetime, timedelta
                new_expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                return {
                    'success': True,
                    'message': 'Abonnement prolongé avec succès',
                    'new_expiry': new_expiry
                }
            else:
                logger.warning(f"Subscription renewal failed for client {client_id}: {error_message}")
                return {
                    'success': False,
                    'message': error_message or 'Erreur lors de la prolongation'
                }
                
        except Exception as e:
            from erp.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error in renew_subscription_api: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Erreur serveur: {str(e)}'
            }
    
    @nicegui_app.get("/api/subscriptions/status/{client_id}")
    async def get_subscription_status(client_id: str):
        """
        API endpoint pour vérifier le statut d'un abonnement
        
        Response:
            {
                "active": bool,
                "client_id": str,
                "expiry_date": date,
                "status": str
            }
        """
        try:
            from erp.services.subscription_service import get_subscription_service
            from erp.utils.logger import get_logger
            
            logger = get_logger(__name__)
            
            subscription_service = get_subscription_service()
            is_active, error_message = subscription_service.check_subscription(client_id)
            
            # Récupérer les infos d'abonnement
            info = subscription_service.get_subscription_info(client_id)
            
            if info:
                return {
                    'active': is_active,
                    'client_id': client_id,
                    'expiry_date': info.get('date_fin_essai'),
                    'status': info.get('statut')
                }
            else:
                return {
                    'active': False,
                    'client_id': client_id,
                    'message': 'Abonnement non trouvé'
                }
                
        except Exception as e:
            from erp.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error in get_subscription_status: {e}", exc_info=True)
            return {
                'active': False,
                'message': f'Erreur serveur: {str(e)}'
            }
    
    # ==================== STRIPE API ROUTES ====================
    
    @nicegui_app.post("/api/stripe/create-checkout-session")
    async def create_stripe_checkout(request):
        """
        Crée une session de paiement Stripe Checkout
        
        Body:
            {
                "plan": "mensuel" | "annuel",
                "client_id": str,
                "client_email": str
            }
        
        Response:
            {
                "success": bool,
                "checkout_url": str (si succès),
                "error": str (si erreur)
            }
        """
        try:
            from erp.services.stripe_service import get_stripe_service
            from erp.utils.logger import get_logger
            
            logger = get_logger(__name__)
            
            body = await request.json()
            plan = body.get('plan')
            client_id = body.get('client_id')
            client_email = body.get('client_email')
            
            if not all([plan, client_id, client_email]):
                return {
                    'success': False,
                    'error': 'plan, client_id et client_email sont requis'
                }
            
            stripe_service = get_stripe_service()
            checkout_url, error = stripe_service.create_checkout_session(
                plan=plan,
                client_id=client_id,
                client_email=client_email
            )
            
            if checkout_url:
                logger.info(f"Checkout session created for {client_id}, plan: {plan}")
                return {
                    'success': True,
                    'checkout_url': checkout_url
                }
            else:
                logger.warning(f"Failed to create checkout: {error}")
                return {
                    'success': False,
                    'error': error
                }
                
        except Exception as e:
            from erp.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error in create_stripe_checkout: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }
    
    @nicegui_app.get("/api/stripe/plans")
    async def get_stripe_plans():
        """
        Retourne les plans d'abonnement disponibles
        
        Response:
            {
                "plans": {
                    "mensuel": {...},
                    "annuel": {...}
                }
            }
        """
        try:
            from erp.services.stripe_service import get_stripe_service
            
            stripe_service = get_stripe_service()
            return {
                'plans': stripe_service.get_plans()
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    @nicegui_app.get("/api/stripe/config")
    async def get_stripe_config():
        """
        Retourne la configuration Stripe pour le frontend
        
        Response:
            {
                "publishable_key": str,
                "configured": bool
            }
        """
        try:
            from erp.services.stripe_service import get_stripe_service
            
            stripe_service = get_stripe_service()
            return {
                'publishable_key': stripe_service.get_publishable_key(),
                'configured': stripe_service.is_configured()
            }
        except Exception as e:
            return {
                'publishable_key': '',
                'configured': False,
                'error': str(e)
            }
    
    @nicegui_app.post("/api/stripe/webhook")
    async def stripe_webhook(request):
        """
        Endpoint pour recevoir les webhooks Stripe
        
        Traite les événements:
        - checkout.session.completed: Paiement réussi
        """
        try:
            from erp.services.stripe_service import get_stripe_service
            from erp.utils.logger import get_logger
            
            logger = get_logger(__name__)
            
            # Récupérer le payload et la signature
            payload = await request.body()
            signature = request.headers.get('Stripe-Signature', '')
            
            stripe_service = get_stripe_service()
            event, error = stripe_service.verify_webhook_signature(payload, signature)
            
            if error:
                logger.warning(f"Webhook signature invalid: {error}")
                return JSONResponse({'error': error}, status_code=400)
            
            # Traiter l'événement
            event_type = event.get('type')
            logger.info(f"Webhook received: {event_type}")
            
            if event_type == 'checkout.session.completed':
                session = event.get('data', {}).get('object', {})
                success, error_msg = stripe_service.handle_checkout_completed(session)
                
                if success:
                    logger.info(f"Checkout completed successfully")
                    return {'status': 'success'}
                else:
                    logger.error(f"Checkout handling failed: {error_msg}")
                    return JSONResponse({'error': error_msg}, status_code=500)
            
            # Autres événements (logging uniquement)
            logger.info(f"Unhandled webhook event: {event_type}")
            return {'status': 'received'}
            
        except Exception as e:
            from erp.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Webhook error: {e}", exc_info=True)
            return JSONResponse({'error': str(e)}, status_code=500)
    
    # ==================== MIDDLEWARE ====================
    @nicegui_app.add_middleware
    class AuthMiddleware(BaseHTTPMiddleware):
        """Middleware qui restreint l'accès aux pages"""
        async def dispatch(self, request: Request, call_next):
            # Autoriser les ressources NiceGUI internes, les routes non restreintes et les APIs publiques
            if request.url.path.startswith('/_nicegui') or request.url.path in unrestricted_page_routes or is_api_route(request.url.path):
                return await call_next(request)
            
            # Vérifier l'authentification (le storage peut ne pas être encore initialisé)
            try:
                if nicegui_app.storage.user.get('authenticated', False):
                    return await call_next(request)
            except:
                pass
            
            # Rediriger vers login si non authentifié
            return RedirectResponse(f'/login?redirect_to={request.url.path}')


if __name__ in {"__main__", "__mp_main__"}:
    # Gestion du chemin pour le favicon
    import sys
    
    # En mode exécutable, modifier sys.argv[0] pour éviter l'erreur runpy
    if getattr(sys, 'frozen', False):
        # Sauvegarder l'original
        original_argv0 = sys.argv[0]
        # Utiliser un fichier Python dummy pour éviter l'erreur
        sys.argv[0] = str(Path(sys.executable).parent / '__main__.py')
        favicon_path = Path(sys.executable).parent / 'static' / 'favicon.svg'
    else:
        favicon_path = Path(__file__).parent / 'static' / 'favicon.svg'
    
    # Appeler main() pour configurer les pages et routes
    main()

    import sys
    import secrets
    import logging
    
    # Filtrer les warnings NiceGUI non pertinents
    class NiceGUIWarningFilter(logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            return '.js.map not found' not in msg and '.well-known/' not in msg
    
    nicegui_logger = logging.getLogger('nicegui')
    nicegui_logger.addFilter(NiceGUIWarningFilter())
    
    # Générer ou charger le secret pour le storage
    storage_secret_file = Path(__file__).parent / 'data' / '.storage_secret'
    if storage_secret_file.exists():
        storage_secret = storage_secret_file.read_text().strip()
    else:
        storage_secret = secrets.token_hex(32)
        storage_secret_file.parent.mkdir(parents=True, exist_ok=True)
        storage_secret_file.write_text(storage_secret)
    
    # Mode reload : True en dev (NICEGUI_RELOAD=true), False en prod
    reload_mode = os.getenv('NICEGUI_RELOAD', 'false').lower() == 'true'
    
    ui.run(
        title='ERP BTP',
        favicon=str(favicon_path) if favicon_path.exists() else None,
        dark=False,
        host='0.0.0.0',
        port=8080,
        reload=reload_mode,
        show=True,
        storage_secret=storage_secret,
    )

