"""
Panel de liste des articles
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error
from erp.ui.components import create_edit_dialog
from erp.utils.validators import validate_article
import json
from pathlib import Path


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
        
        selected_filters = {'type': None, 'categorie': None, 'sous_categorie': None}
        
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
        articles_container = ui.column().classes('w-full gap-0')
        
        def refresh_articles_list():
            app_instance.dm.load_data()
            articles_container.clear()
            
            # Appliquer les filtres
            filtered_articles = app_instance.dm.articles
            
            if selected_filters['type'] is not None:
                filtered_articles = [a for a in filtered_articles if a.type_article == selected_filters['type']]
            
            # Filtrer par catégorie ou sous-catégorie
            if selected_filters['sous_categorie'] is not None:
                # Filtre par sous-catégorie uniquement
                filtered_articles = [a for a in filtered_articles if getattr(a, 'categorie', 'general') == selected_filters['sous_categorie']]
            elif selected_filters['categorie'] is not None:
                # Filtre par catégorie principale : inclure les articles de cette catégorie et de ses sous-catégories
                cat_node = next((c for c in categories_data if c['id'] == selected_filters['categorie']), None)
                if cat_node:
                    allowed_categories = [selected_filters['categorie']]
                    if cat_node.get('children'):
                        allowed_categories.extend([child['id'] for child in cat_node['children']])
                    filtered_articles = [a for a in filtered_articles if getattr(a, 'categorie', 'general') in allowed_categories]
            
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
                    ui.label('Sous-catégorie').classes('w-40 text-center')
                    ui.label('Unité').classes('w-20 text-center')
                    ui.label('Prix unitaire').classes('w-32 text-right')
                    ui.label('Actions').classes('w-32')
                
                # Rows
                for article in filtered_articles:
                    article_id = article.id
                    
                    # Déterminer la catégorie et sous-catégorie pour l'affichage
                    article_cat = getattr(article, 'categorie', 'general')
                    display_cat = article_cat
                    display_sous_cat = '-'
                    
                    # Chercher si c'est une sous-catégorie
                    for cat in categories_data:
                        if cat['id'] == article_cat:
                            # C'est une catégorie principale
                            display_cat = cat['label']
                            break
                        for child in cat.get('children', []):
                            if child['id'] == article_cat:
                                # C'est une sous-catégorie
                                display_cat = cat['label']
                                display_sous_cat = child['label']
                                break
                        if display_sous_cat != '-':
                            break
                    
                    with ui.row().classes('w-full gap-2 p-1 items-center hover:bg-gray-50 text-sm border-b border-gray-100'):
                        ui.label(article.reference).classes('w-40 font-mono')
                        ui.label(article.designation).classes('flex-1')
                        ui.label(article.type_article).classes('w-32 text-center')
                        ui.label(display_cat).classes('w-32 text-center')
                        ui.label(display_sous_cat).classes('w-40 text-center text-gray-600')
                        ui.label(article.unite).classes('w-20 text-center')
                        ui.label(f"{article.prix_unitaire:.2f} EUR").classes('w-32 text-right font-semibold')
                        
                        def make_edit_handler(article_id_val):
                            def on_modify_click():
                                art = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                if not art:
                                    notify_error('Article non trouvé')
                                    return
                                
                                # Charger les catégories pour le dialogue
                                categories_data = load_categories()
                                
                                # Déterminer la catégorie parente et la sous-catégorie de l'article
                                article_cat = getattr(art, 'categorie', 'general')
                                parent_cat_id = None
                                sous_cat_id = None
                                
                                # Trouver si c'est une catégorie parent ou une sous-catégorie
                                for cat in categories_data:
                                    if cat['id'] == article_cat:
                                        parent_cat_id = article_cat
                                        break
                                    for child in cat.get('children', []):
                                        if child['id'] == article_cat:
                                            parent_cat_id = cat['id']
                                            sous_cat_id = article_cat
                                            break
                                    if parent_cat_id:
                                        break
                                
                                # Si aucune correspondance, utiliser 'general'
                                if not parent_cat_id:
                                    parent_cat_id = 'general'
                                
                                # State pour la sélection
                                edit_selected_sous_cat = {'value': sous_cat_id}
                                
                                with ui.dialog() as edit_dialog, ui.card().classes('p-6 w-96'):
                                    ui.label('Modifier l\'article').classes('text-xl font-bold mb-4')
                                    
                                    reference_input = ui.input('Référence', value=art.reference).classes('w-full')
                                    designation_input = ui.input('Désignation', value=art.designation).classes('w-full')
                                    description_input = ui.textarea('Description', value=art.description).props('rows=2').classes('w-full')
                                    
                                    type_select = ui.select(
                                        label='Type',
                                        options={'materiau': 'Matériau', 'fourniture': 'Fourniture', 'main_oeuvre': 'Main d\'œuvre', 'consommable': 'Consommable'},
                                        value=art.type_article
                                    ).classes('w-full')
                                    
                                    # Catégorie principale (avec options dynamiques)
                                    cat_options = {cat['id']: cat['label'] for cat in categories_data}
                                    categorie_select = ui.select(
                                        label='Catégorie',
                                        options=cat_options,
                                        value=parent_cat_id
                                    ).classes('w-full')
                                    
                                    # Container pour la sous-catégorie
                                    sous_cat_container = ui.column().classes('w-full')
                                    
                                    def update_sous_cat_select():
                                        sous_cat_container.clear()
                                        selected_cat = categorie_select.value
                                        
                                        if not selected_cat:
                                            return
                                        
                                        # Trouver la catégorie sélectionnée
                                        cat = next((c for c in categories_data if c['id'] == selected_cat), None)
                                        if not cat or not cat.get('children'):
                                            edit_selected_sous_cat['value'] = None
                                            return
                                        
                                        # Construire les options de sous-catégorie
                                        sous_cat_options = {'': 'Aucune (catégorie principale)'}
                                        sous_cat_options.update({child['id']: child['label'] for child in cat['children']})
                                        
                                        with sous_cat_container:
                                            def on_sous_cat_change(e):
                                                edit_selected_sous_cat['value'] = e.value if e.value else None
                                            
                                            ui.select(
                                                label='Sous-catégorie',
                                                options=sous_cat_options,
                                                value=edit_selected_sous_cat['value'] or '',
                                                on_change=on_sous_cat_change
                                            ).classes('w-full')
                                    
                                    # Mettre à jour la sous-catégorie quand la catégorie change
                                    categorie_select.on_value_change(lambda: update_sous_cat_select())
                                    
                                    # Initialiser la sous-catégorie
                                    update_sous_cat_select()
                                    
                                    unite_select = ui.select(
                                        label='Unité',
                                        options={'m²': 'm²', 'ml': 'ml', 'u': 'unité', 'h': 'heure', 'kg': 'kg', 'l': 'l', 'forfait': 'forfait'},
                                        value=art.unite
                                    ).classes('w-full')
                                    
                                    prix_input = ui.number('Prix unitaire (EUR)', value=art.prix_unitaire, min=0, step=0.01).classes('w-full')
                                    
                                    with ui.row().classes('gap-2 mt-4 w-full justify-end'):
                                        ui.button('Annuler', on_click=edit_dialog.close).props('flat')
                                        
                                        def save_article_update():
                                            art_updated = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                            if not art_updated:
                                                return
                                            
                                            # Préparer les données pour validation
                                            article_data = {
                                                'reference': reference_input.value,
                                                'designation': designation_input.value,
                                                'prix_unitaire': prix_input.value
                                            }
                                            
                                            # Valider les données
                                            is_valid, error_message = validate_article(article_data)
                                            if not is_valid:
                                                notify_error(error_message)
                                                return
                                            
                                            # Vérifier la référence si elle a changé
                                            if reference_input.value != art_updated.reference:
                                                if any(a.reference == reference_input.value for a in app_instance.dm.articles if a.id != art_updated.id):
                                                    notify_error(f'La référence "{reference_input.value}" existe déjà')
                                                    return
                                            
                                            art_updated.reference = reference_input.value.strip()
                                            art_updated.designation = designation_input.value.strip()
                                            art_updated.description = description_input.value.strip() if description_input.value else ''
                                            art_updated.unite = unite_select.value or 'm²'
                                            art_updated.prix_unitaire = prix_input.value or 0
                                            art_updated.type_article = type_select.value or 'materiau'
                                            
                                            # Utiliser la sous-catégorie si elle est sélectionnée, sinon la catégorie
                                            final_category = edit_selected_sous_cat['value'] if edit_selected_sous_cat['value'] else categorie_select.value
                                            art_updated.categorie = final_category or 'general'
                                            
                                            try:
                                                app_instance.dm.update_article(art_updated)
                                                edit_dialog.close()
                                                refresh_articles_list()
                                                notify_success('Article modifié avec succès')
                                            except Exception as e:
                                                notify_error(f"Erreur lors de la sauvegarde : {str(e)}")
                                        
                                        ui.button('Enregistrer', on_click=save_article_update).props('color=primary')
                                
                                edit_dialog.open()
                            
                            return on_modify_click
                        
                        def make_duplicate_handler(article_id_val):
                            def on_duplicate_click():
                                art = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                if not art:
                                    notify_error('Article non trouvé')
                                    return
                                
                                with ui.dialog() as duplicate_dialog, ui.card().classes('p-6 w-96'):
                                    ui.label('Dupliquer l\'article').classes('text-xl font-bold mb-4')
                                    
                                    # Générer une référence par défaut avec suffixe "-COPIE"
                                    base_ref = art.reference
                                    new_ref = f"{base_ref}-COPIE"
                                    counter = 1
                                    while any(a.reference == new_ref for a in app_instance.dm.articles):
                                        new_ref = f"{base_ref}-COPIE{counter}"
                                        counter += 1
                                    
                                    reference_input = ui.input('Nouvelle référence', value=new_ref).classes('w-full')
                                    ui.label(f"Copie de: {art.designation}").classes('text-gray-600 text-sm mb-2')
                                    
                                    with ui.row().classes('gap-2 mt-4 w-full justify-end'):
                                        ui.button('Annuler', on_click=duplicate_dialog.close).props('flat')
                                        
                                        def save_duplicate():
                                            # Vérifier que la référence n'existe pas déjà
                                            if any(a.reference == reference_input.value for a in app_instance.dm.articles):
                                                notify_error(f'La référence "{reference_input.value}" existe déjà')
                                                return
                                            
                                            # Créer le nouvel article (copie)
                                            from erp.core.models import Article
                                            new_article = Article(
                                                id=0,  # ID temporaire, sera généré par la base
                                                reference=reference_input.value.strip(),
                                                designation=art.designation,
                                                description=art.description,
                                                unite=art.unite,
                                                prix_unitaire=art.prix_unitaire,
                                                type_article=art.type_article,
                                                fournisseur_id=art.fournisseur_id,
                                                categorie=getattr(art, 'categorie', 'general')
                                            )
                                            
                                            try:
                                                app_instance.dm.add_article(new_article)
                                                duplicate_dialog.close()
                                                refresh_articles_list()
                                                notify_success(f'Article dupliqué avec la référence {reference_input.value}')
                                            except Exception as e:
                                                notify_error(f"Erreur lors de la duplication : {str(e)}")
                                        
                                        ui.button('Dupliquer', on_click=save_duplicate).props('color=primary')
                                
                                duplicate_dialog.open()
                            
                            return on_duplicate_click
                        
                        with ui.row().classes('gap-2 items-center'):
                            app_instance.material_icon_button('edit', on_click=make_edit_handler(article_id))
                            app_instance.material_icon_button('content_copy', on_click=make_duplicate_handler(article_id))
                            app_instance.material_icon_button('delete', on_click=lambda a=article: (
                                notify_success('Article supprimé'),
                                app_instance.dm.delete_article(a.id),
                                refresh_articles_list()
                            ), is_delete=True)
        
        # Section filtres en haut (après la définition de refresh_articles_list)
        with filters_container:
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
                
                # Filtre par catégorie avec sous-catégories
                with ui.row().classes('w-full items-center gap-2 mb-3'):
                    ui.label('Catégorie:').classes('font-medium text-gray-700 w-24')
                    with ui.row().classes('gap-2 flex-wrap'):
                        # Bouton "Toutes"
                        def select_all():
                            selected_filters['categorie'] = None
                            selected_filters['sous_categorie'] = None
                            refresh_articles_list()
                        
                        ui.button('Toutes', on_click=select_all).props('size=sm')
                        
                        # Créer un bouton avec menu déroulant pour chaque catégorie
                        for cat in categories_data:
                            cat_id = cat['id']
                            cat_label = cat['label']
                            children = cat.get('children', [])
                            
                            if children:
                                # Catégorie avec sous-catégories : créer un menu déroulant
                                with ui.button(cat_label).props('size=sm flat icon-right=arrow_drop_down'):
                                    with ui.menu() as menu:
                                        # Option pour sélectionner toute la catégorie
                                        def make_select_cat(c_id=cat_id, m=menu):
                                            def select_cat():
                                                selected_filters['categorie'] = c_id
                                                selected_filters['sous_categorie'] = None
                                                m.close()
                                                refresh_articles_list()
                                            return select_cat
                                        
                                        ui.menu_item(f'Toute la catégorie {cat_label}', on_click=make_select_cat(cat_id, menu))
                                        ui.separator()
                                        
                                        # Options pour chaque sous-catégorie
                                        for child in children:
                                            def make_select_subcat(sc_id=child['id'], m=menu):
                                                def select_subcat():
                                                    selected_filters['categorie'] = None
                                                    selected_filters['sous_categorie'] = sc_id
                                                    m.close()
                                                    refresh_articles_list()
                                                return select_subcat
                                            
                                            ui.menu_item(child['label'], on_click=make_select_subcat(child['id'], menu))
                            else:
                                # Catégorie sans sous-catégories : simple bouton
                                def make_select_cat_only(c_id=cat_id):
                                    def select_cat_only():
                                        selected_filters['categorie'] = c_id
                                        selected_filters['sous_categorie'] = None
                                        refresh_articles_list()
                                    return select_cat_only
                                
                                ui.button(cat_label, on_click=make_select_cat_only(cat_id)).props('size=sm flat')
        
        # Appeler refresh pour remplir le tableau initial
        refresh_articles_list()
