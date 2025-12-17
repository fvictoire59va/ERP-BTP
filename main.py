from nicegui import ui, app as nicegui_app
from erp.ui.app import DevisApp
from pathlib import Path
import sys

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


# Imports pour l'authentification
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

unrestricted_page_routes = {'/login'}

# Créer une instance globale de l'AuthManager (partagée entre toutes les pages)
from erp.core.auth import AuthManager
from erp.core.data_manager import DataManager

_data_manager = DataManager()
_auth_manager = AuthManager(_data_manager)

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
            user, session_id = result
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
    
    return None


# Page principale 
@ui.page('/')
def index_page():
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
    
    app.create_main_ui()
    
    logger.info("Main UI created successfully")


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
    
    # Ajouter le middleware d'authentification
    @nicegui_app.add_middleware
    class AuthMiddleware(BaseHTTPMiddleware):
        """Middleware qui restreint l'accès aux pages"""
        async def dispatch(self, request: Request, call_next):
            # Autoriser les ressources NiceGUI internes et les routes non restreintes
            if request.url.path.startswith('/_nicegui') or request.url.path in unrestricted_page_routes:
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
    
    ui.run(
        title='ERP BTP',
        favicon=str(favicon_path) if favicon_path.exists() else None,
        dark=False,
        port=8080,
        reload=not getattr(sys, 'frozen', False),  # Désactiver reload en mode exécutable
        show=True,
        storage_secret=storage_secret,
    )

