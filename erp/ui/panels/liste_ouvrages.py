"""
Panel de liste des ouvrages
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error
import json
from pathlib import Path


def create_liste_ouvrages_panel(app_instance):
    """Crée le panneau de liste des ouvrages
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        ui.label('Liste des Ouvrages').classes('text-3xl font-bold text-gray-900 mb-6')
        
        selected_filters = {'categorie': None}
        
        # Charger les catégories depuis le fichier
        def load_categories():
            categories_file = Path('data') / 'categories.json'
            if categories_file.exists():
                with open(categories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        
        categories_data = load_categories()
        
        # Conteneurs
        filters_container = ui.column().classes('w-full')
        ouvrages_container = ui.column().classes('w-full gap-0')
        
        def refresh_ouvrages_list():
            app_instance.dm.load_data()
            ouvrages_container.clear()
            
            # Appliquer les filtres
            filtered_ouvrages = app_instance.dm.ouvrages
            
            # Filtrer par catégorie uniquement
            if selected_filters['categorie']:
                # Filtre par catégorie principale : inclure les ouvrages de cette catégorie et de ses sous-catégories
                cat_node = next((c for c in categories_data if c['id'] == selected_filters['categorie']), None)
                if cat_node:
                    allowed_categories = [selected_filters['categorie']]
                    if cat_node.get('children'):
                        allowed_categories.extend([child['id'] for child in cat_node['children']])
                    filtered_ouvrages = [o for o in filtered_ouvrages if o.categorie in allowed_categories]
            
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
        
        # Section filtres en haut (après la définition de refresh_ouvrages_list)
        with filters_container:
            with ui.card().classes('w-full shadow-none border').style('padding: 16px; margin-bottom: 20px;'):
                ui.label('Filtrer les ouvrages').classes('font-semibold text-lg text-gray-800 mb-4')
                
                # Filtre par catégorie avec sous-catégories
                with ui.row().classes('w-full items-center gap-2 mb-3'):
                    ui.label('Catégorie:').classes('font-medium text-gray-700 w-24')
                    with ui.row().classes('gap-2 flex-wrap'):
                        # Bouton "Toutes"
                        def select_all():
                            selected_filters['categorie'] = None
                            refresh_ouvrages_list()
                        
                        ui.button('Toutes', on_click=select_all).props('size=sm')
                        
                        # Créer un bouton avec menu déroulant pour chaque catégorie
                        for cat in categories_data:
                            cat_id = cat['id']
                            cat_label = cat['label']
                            children = cat.get('children', [])
                            
                            # Simple bouton pour chaque catégorie (inclut automatiquement les sous-catégories)
                            def make_select_cat(c_id=cat_id):
                                def select_cat():
                                    selected_filters['categorie'] = c_id
                                    refresh_ouvrages_list()
                                return select_cat
                            
                            ui.button(cat_label, on_click=make_select_cat(cat_id)).props('size=sm flat')
        
        # Appeler refresh pour remplir le tableau initial
        refresh_ouvrages_list()
