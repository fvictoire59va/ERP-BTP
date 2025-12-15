"""
Panel de liste des ouvrages
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error


def create_liste_ouvrages_panel(app_instance):
    """Crée le panneau de liste des ouvrages
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        ui.label('Liste des Ouvrages').classes('text-3xl font-bold text-gray-900 mb-6')
        
        categories = {
            'platrerie': 'Plâtrerie',
            'menuiserie_int': 'Menuiserie int.',
            'menuiserie_ext': 'Menuiserie ext.',
            'faux_plafond': 'Faux plafond',
            'agencement': 'Agencement',
            'isolation': 'Isolation',
            'peinture': 'Peinture'
        }
        
        selected_category = {'value': None}
        
        # Section filtre en haut
        with ui.card().classes('w-full shadow-none border').style('padding: 16px; margin-bottom: 20px;'):
            ui.label('Filtrer par catégorie').classes('font-semibold text-lg text-gray-800 mb-4')
            
            with ui.row().classes('w-full gap-2 flex-wrap'):
                # Bouton "Tous"
                def select_all_categories():
                    selected_category['value'] = None
                    refresh_ouvrages_list()
                
                ui.button('Tous', on_click=select_all_categories).props('size=sm')
                
                # Boutons pour chaque catégorie
                for cat_id, cat_label in categories.items():
                    def make_select_category(cat=cat_id):
                        def select_category():
                            selected_category['value'] = cat
                            refresh_ouvrages_list()
                        return select_category
                    
                    count = len([o for o in app_instance.dm.ouvrages if o.categorie == cat_id])
                    ui.button(f"{cat_label} ({count})", on_click=make_select_category(cat_id)).props('size=sm flat')
        
        # Section tableau
        ouvrages_container = ui.column().classes('w-full gap-0')
        
        def refresh_ouvrages_list():
            app_instance.dm.load_data()
            ouvrages_container.clear()
            
            # Filtrer par catégorie si sélectionnée
            if selected_category['value']:
                filtered_ouvrages = [o for o in app_instance.dm.ouvrages if o.categorie == selected_category['value']]
            else:
                filtered_ouvrages = app_instance.dm.ouvrages
            
            if not filtered_ouvrages:
                with ouvrages_container:
                    ui.label('Aucun ouvrage dans cette catégorie.').classes('text-gray-500 text-center py-8')
                return
            
            with ouvrages_container:
                # Headers
                with ui.row().classes('w-full gap-2 font-bold bg-gray-100 p-1 rounded'):
                    ui.label('Reference').classes('w-40')
                    ui.label('Designation').classes('flex-1')
                    ui.label('Catégorie').classes('w-32')
                    ui.label('Prix revient').classes('w-24 text-right')
                    ui.label('Actions').classes('w-32')
                
                # Rows
                for ouvrage in filtered_ouvrages:
                    with ui.row().classes('w-full gap-2 p-1 items-center hover:bg-gray-50 text-sm border-b border-gray-100'):
                        ui.label(ouvrage.reference).classes('w-40 font-mono')
                        ui.label(ouvrage.designation).classes('flex-1')
                        ui.label(ouvrage.categorie).classes('w-32 text-gray-600')
                        ui.label(f"{ouvrage.prix_revient_unitaire:.2f}").classes('w-24 text-right font-semibold')
                        
                        def make_edit_handler(ouv):
                            def edit_ouvrage():
                                # Stocker l'ouvrage à éditer dans l'instance de l'app
                                app_instance.ouvrage_to_edit = ouv
                                
                                # Naviguer vers la section ouvrages
                                if hasattr(app_instance, 'show_section_with_children'):
                                    app_instance.current_section['value'] = 'ouvrages'
                                    app_instance.show_section_with_children('ouvrages', ['ouvrages', 'liste_ouvrages'])
                                    if hasattr(app_instance, 'tab_selector'):
                                        app_instance.tab_selector.value = 'ouvrages_tab'
                            return edit_ouvrage
                        
                        def make_delete_handler(ouv):
                            def delete_ouvrage():
                                notify_success('Ouvrage supprimé')
                                app_instance.dm.ouvrages.remove(ouv)
                                app_instance.dm.save_data()
                                refresh_ouvrages_list()
                            return delete_ouvrage
                        
                        with ui.row().classes('gap-1 w-32'):
                            app_instance.material_icon_button('edit', on_click=make_edit_handler(ouvrage))
                            app_instance.material_icon_button('delete', on_click=make_delete_handler(ouvrage), is_delete=True)
        
        refresh_ouvrages_list()
