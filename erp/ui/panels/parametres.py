"""
Panel de paramètres

Contient les paramètres globaux de l'application (thème, couleurs, etc.)
"""

from nicegui import ui
from erp.config.theme import get_theme, set_accent_color, THEME_PRESETS
from erp.ui.utils import notify_success


def create_parametres_panel(app_instance):
    """Crée le panneau de paramètres
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 48px; min-height: 600px; min-width: 1200px; width: 100%;'):
        ui.label('Paramètres').classes('text-3xl font-bold text-gray-900 mb-8')
        
        # Section Thème et couleurs
        with ui.card().classes('w-full shadow-none border').style('padding: 24px; margin-bottom: 24px;'):
            ui.label('Thème et apparence').classes('text-xl font-bold text-gray-800 mb-6')
            
            with ui.column().classes('w-full gap-6'):
                # Sélecteur de thème
                with ui.row().classes('w-full items-center gap-4'):
                    ui.label('Thème:').classes('text-sm font-semibold text-gray-700 w-32')
                    
                    # Conteneur pour l'aperçu
                    preview_container = ui.row()
                    
                    def on_theme_change(e):
                        preset_name = e.value
                        if preset_name in THEME_PRESETS:
                            color = THEME_PRESETS[preset_name].accent_color
                            set_accent_color(color)
                            # Mettre à jour le color picker
                            color_pick.value = color
                            # Mettre à jour l'aperçu
                            preview_card.style(f'background-color: {color}; height: 40px; border-radius: 4px;')
                            # Mettre à jour les variables CSS en temps réel
                            ui.run_javascript(f'''
                                document.documentElement.style.setProperty('--q-primary', '{color}');
                                document.documentElement.style.setProperty('--q-positive', '{color}');
                                document.documentElement.style.setProperty('--q-color-primary', '{color}');
                                document.documentElement.style.setProperty('--theme-accent', '{color}');
                                document.body.style.setProperty('--q-primary', '{color}');
                                document.body.style.setProperty('--q-positive', '{color}');
                                document.body.style.setProperty('--q-color-primary', '{color}');
                                document.body.style.setProperty('--theme-accent', '{color}');
                            ''')
                            notify_success('Thème mis à jour')
                    
                    theme_select = ui.select(
                        options=list(THEME_PRESETS.keys()),
                        value='default',
                        on_change=on_theme_change
                    ).classes('flex-1 max-w-xs').props('size=sm')
                
                # Sélecteur de couleur personnalisée
                with ui.row().classes('w-full items-center gap-4'):
                    ui.label('Couleur d\'accent:').classes('text-sm font-semibold text-gray-700 w-32')
                    
                    def on_color_change(e):
                        set_accent_color(e.value)
                        # Mettre à jour l'aperçu
                        preview_card.style(f'background-color: {e.value}; height: 40px; border-radius: 4px;')
                        # Mettre à jour les variables CSS en temps réel
                        ui.run_javascript(f'''
                            document.documentElement.style.setProperty('--q-primary', '{e.value}');
                            document.documentElement.style.setProperty('--q-positive', '{e.value}');
                            document.documentElement.style.setProperty('--q-color-primary', '{e.value}');
                            document.documentElement.style.setProperty('--theme-accent', '{e.value}');
                            document.body.style.setProperty('--q-primary', '{e.value}');
                            document.body.style.setProperty('--q-positive', '{e.value}');
                            document.body.style.setProperty('--q-color-primary', '{e.value}');
                            document.body.style.setProperty('--theme-accent', '{e.value}');
                        ''')
                        notify_success('Couleur d\'accent mise à jour')
                    
                    color_pick = ui.color_input(
                        value=get_theme().accent_color,
                        on_change=on_color_change
                    ).classes('max-w-xs')
                
                # Aperçu de la couleur
                with ui.row().classes('w-full items-center gap-4 mt-4'):
                    ui.label('Aperçu:').classes('text-sm font-semibold text-gray-700 w-32')
                    preview_card = ui.card().classes('flex-1 max-w-xs').style(f'background-color: {get_theme().accent_color}; height: 40px; border-radius: 4px;')
