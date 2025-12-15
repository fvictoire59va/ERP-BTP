"""
Panel de liste des articles
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error
from erp.ui.components import create_edit_dialog


def create_liste_articles_panel(app_instance):
    """Crée le panneau de liste des articles
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        ui.label('Liste des Articles').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Filtres
        types_articles = {
            None: 'Tous',
            'materiau': 'Matériau',
            'fourniture': 'Fourniture',
            'main_oeuvre': 'Main d\'œuvre',
            'consommable': 'Consommable'
        }
        
        categories_articles = {
            None: 'Toutes',
            'general': 'Général',
            'platrerie': 'Plâtrerie',
            'menuiserie_int': 'Menuiserie Int.',
            'menuiserie_ext': 'Menuiserie Ext.',
            'faux_plafond': 'Faux Plafond',
            'agencement': 'Agencement',
            'isolation': 'Isolation',
            'peinture': 'Peinture'
        }
        
        selected_filters = {'type': None, 'categorie': None}
        
        # Section filtres en haut
        with ui.card().classes('w-full shadow-none border').style('padding: 16px; margin-bottom: 20px;'):
            ui.label('Filtrer les articles').classes('font-semibold text-lg text-gray-800 mb-4')
            
            # Filtre par type
            with ui.row().classes('w-full items-center gap-2 mb-3'):
                ui.label('Type:').classes('font-medium text-gray-700 w-24')
                with ui.row().classes('gap-2 flex-wrap'):
                    for type_key, type_label in types_articles.items():
                        def make_select_type(t=type_key):
                            def select_type():
                                selected_filters['type'] = t
                                refresh_articles_list()
                            return select_type
                        
                        count = len([a for a in app_instance.dm.articles if (type_key is None or a.type_article == type_key)])
                        btn_props = 'size=sm' if type_key is None else 'size=sm flat'
                        ui.button(f"{type_label} ({count})", on_click=make_select_type(type_key)).props(btn_props)
            
            # Filtre par catégorie
            with ui.row().classes('w-full items-center gap-2'):
                ui.label('Catégorie:').classes('font-medium text-gray-700 w-24')
                with ui.row().classes('gap-2 flex-wrap'):
                    for cat_key, cat_label in categories_articles.items():
                        def make_select_categorie(c=cat_key):
                            def select_categorie():
                                selected_filters['categorie'] = c
                                refresh_articles_list()
                            return select_categorie
                        
                        count = len([a for a in app_instance.dm.articles if (cat_key is None or getattr(a, 'categorie', 'general') == cat_key)])
                        btn_props = 'size=sm' if cat_key is None else 'size=sm flat'
                        ui.button(f"{cat_label} ({count})", on_click=make_select_categorie(cat_key)).props(btn_props)
        
        # Section tableau
        articles_container = ui.column().classes('w-full gap-0')
        
        def refresh_articles_list():
            app_instance.dm.load_data()
            articles_container.clear()
            
            # Appliquer les filtres
            filtered_articles = app_instance.dm.articles
            
            if selected_filters['type'] is not None:
                filtered_articles = [a for a in filtered_articles if a.type_article == selected_filters['type']]
            
            if selected_filters['categorie'] is not None:
                filtered_articles = [a for a in filtered_articles if getattr(a, 'categorie', 'general') == selected_filters['categorie']]
            
            if not filtered_articles:
                with articles_container:
                    ui.label('Aucun article correspondant aux filtres.' if app_instance.dm.articles else 'Aucun article. Créez-en un dans l\'onglet Articles.').classes('text-gray-500 text-center py-8')
                return
            
            with articles_container:
                # Headers
                with ui.row().classes('w-full gap-2 font-bold bg-gray-100 p-1 rounded'):
                    ui.label('Référence').classes('w-40')
                    ui.label('Désignation').classes('flex-1')
                    ui.label('Type').classes('w-32 text-center')
                    ui.label('Catégorie').classes('w-32 text-center')
                    ui.label('Unité').classes('w-20 text-center')
                    ui.label('Prix unitaire').classes('w-32 text-right')
                    ui.label('Actions').classes('w-32')
                
                # Rows
                for article in filtered_articles:
                    article_id = article.id
                    with ui.row().classes('w-full gap-2 p-1 items-center hover:bg-gray-50 text-sm border-b border-gray-100'):
                        ui.label(article.reference).classes('w-40 font-mono')
                        ui.label(article.designation).classes('flex-1')
                        ui.label(article.type_article).classes('w-32 text-center')
                        ui.label(getattr(article, 'categorie', 'general')).classes('w-32 text-center')
                        ui.label(article.unite).classes('w-20 text-center')
                        ui.label(f"{article.prix_unitaire:.2f} EUR").classes('w-32 text-right font-semibold')
                        
                        def make_edit_handler(article_id_val):
                            def on_modify_click():
                                art = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                if not art:
                                    notify_error('Article non trouvé')
                                    return
                                
                                def save_article_update(values):
                                    art_updated = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                    if not art_updated:
                                        return
                                    
                                    # Vérifier la référence si elle a changé
                                    if values.get('référence') != art_updated.reference:
                                        if any(a.reference == values.get('référence') for a in app_instance.dm.articles if a.id != art_updated.id):
                                            notify_error(f'La référence "{values.get("référence")}" existe déjà')
                                            return
                                    
                                    art_updated.reference = values.get('référence', '')
                                    art_updated.designation = values.get('désignation', '')
                                    art_updated.description = values.get('description', '')
                                    art_updated.unite = values.get('unité') or 'm²'
                                    art_updated.prix_unitaire = values.get('prix_unitaire_(eur)', 0)
                                    art_updated.type_article = values.get('type') or 'materiau'
                                    art_updated.categorie = values.get('catégorie') or 'general'
                                    
                                    app_instance.dm.save_data()
                                    refresh_articles_list()
                                    notify_success('Article modifié avec succès')
                                
                                edit_dialog = create_edit_dialog(
                                    'Modifier l\'article',
                                    fields=[
                                        {'type': 'input', 'label': 'Référence', 'value': art.reference, 'key': 'référence'},
                                        {'type': 'input', 'label': 'Désignation', 'value': art.designation, 'key': 'désignation'},
                                        {'type': 'textarea', 'label': 'Description', 'value': art.description, 'rows': 2, 'key': 'description'},
                                        {'type': 'select', 'label': 'Type', 'options': {'materiau': 'Matériau', 'fourniture': 'Fourniture', 'main_oeuvre': 'Main d\'œuvre', 'consommable': 'Consommable'}, 'value': art.type_article, 'key': 'type'},
                                        {'type': 'select', 'label': 'Catégorie', 'options': {'general': 'Général', 'platrerie': 'Plâtrerie', 'menuiserie_int': 'Menuiserie Int.', 'menuiserie_ext': 'Menuiserie Ext.', 'faux_plafond': 'Faux Plafond', 'agencement': 'Agencement', 'isolation': 'Isolation', 'peinture': 'Peinture'}, 'value': getattr(art, 'categorie', 'general'), 'key': 'catégorie'},
                                        {'type': 'select', 'label': 'Unité', 'options': {'m²': 'm²', 'ml': 'ml', 'u': 'unité', 'h': 'heure', 'kg': 'kg', 'l': 'l', 'forfait': 'forfait'}, 'value': art.unite, 'key': 'unité'},
                                        {'type': 'number', 'label': 'Prix unitaire (EUR)', 'value': art.prix_unitaire, 'min': 0, 'step': 0.01, 'key': 'prix_unitaire_(eur)'},
                                    ],
                                    on_save=save_article_update
                                )
                                edit_dialog.open()
                            
                            return on_modify_click
                        
                        with ui.row().classes('gap-2 items-center'):
                            app_instance.material_icon_button('edit', on_click=make_edit_handler(article_id))
                            app_instance.material_icon_button('delete', on_click=lambda a=article: (
                                notify_success('Article supprimé'),
                                app_instance.dm.articles.remove(a),
                                app_instance.dm.save_data(),
                                refresh_articles_list()
                            ), is_delete=True)
        
        refresh_articles_list()
