"""
Panel de gestion du catalogue d'articles

Contient tous les composants pour créer, éditer et gérer les articles.
"""

from nicegui import ui
from erp.core.models import Article
from erp.ui.components import create_edit_dialog
from erp.ui.utils import notify_success, notify_error
from erp.utils.validators import validate_article
import json
from pathlib import Path


def create_catalogue_panel(app_instance):
    """Crée le panneau de gestion des articles
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Charger les catégories depuis le fichier
    def load_categories():
        categories_file = Path('data') / 'categories.json'
        if categories_file.exists():
            with open(categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    categories_data = load_categories()
    
    with ui.card().classes('w-full shadow-sm').style('padding: 48px; min-height: 600px; min-width: 1200px; width: 100%;'):
        ui.label('Articles').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Section pour ajouter un nouvel article
        with ui.card().classes('w-full shadow-sm').style('padding: 24px; margin-bottom: 20px;'):
            ui.label('Ajouter un nouvel article').classes('text-2xl font-bold text-gray-900 mb-6')
            
            with ui.column().classes('w-full gap-4'):
                # Ligne 1: Référence et Désignation
                with ui.row().classes('w-full gap-4'):
                    ref_input = ui.input('Référence', placeholder='ART-001').classes('flex-1 article-reference')
                    desig_input = ui.input('Désignation', placeholder='Nom de l\'article...').classes('flex-1 article-designation')
                
                # Ligne 2: Description et Type
                with ui.row().classes('w-full gap-4'):
                    desc_input = ui.textarea('Description', placeholder='Description détaillée').classes('flex-1 article-description').props('rows=2')
                    type_select = ui.select(
                        label='Type',
                        options={
                            'materiau': 'Matériau',
                            'fourniture': 'Fourniture',
                            'main_oeuvre': 'Main d\'œuvre',
                            'consommable': 'Consommable'
                        },
                        value='materiau'
                    ).classes('w-48 article-type')
                
                # Ligne 3: Catégorie, Sous-catégorie et Unité
                with ui.row().classes('w-full gap-4'):
                    # Créer les options pour la catégorie depuis categories_data
                    cat_options = {}
                    for cat in categories_data:
                        cat_options[cat['id']] = cat['label']
                    
                    categorie_select = ui.select(
                        label='Catégorie',
                        options=cat_options,
                        value=list(cat_options.keys())[0] if cat_options else None
                    ).classes('w-48 article-categorie')
                    
                    # Conteneur pour la sous-catégorie
                    sous_cat_container = ui.row().classes('w-48')
                    
                    unite_select = ui.select(
                        label='Unité',
                        options={'m²': 'm²', 'ml': 'ml', 'u': 'unité', 'h': 'heure', 'kg': 'kg', 'l': 'l', 'forfait': 'forfait'}
                    ).classes('w-32 article-unite')
                    
                # Variable pour stocker la sous-catégorie sélectionnée
                selected_sous_cat = {'value': None}
                sous_cat_select_ref = {'ref': None}
                
                def update_sous_cat_select():
                    sous_cat_container.clear()
                    with sous_cat_container:
                        if categorie_select.value:
                            cat_node = next((c for c in categories_data if c['id'] == categorie_select.value), None)
                            if cat_node and cat_node.get('children'):
                                sous_cat_options = {'': 'Aucune (catégorie principale)'}
                                for child in cat_node['children']:
                                    sous_cat_options[child['id']] = child['label']
                                
                                sous_cat_select = ui.select(
                                    label='Sous-catégorie',
                                    options=sous_cat_options,
                                    value=''
                                ).classes('w-full')
                                sous_cat_select_ref['ref'] = sous_cat_select
                                
                                def on_sous_cat_change():
                                    selected_sous_cat['value'] = sous_cat_select.value if sous_cat_select.value else None
                                
                                sous_cat_select.on_value_change(on_sous_cat_change)
                            else:
                                ui.label('Pas de sous-catégorie').classes('text-sm text-gray-400 self-center')
                                selected_sous_cat['value'] = None
                
                categorie_select.on_value_change(lambda: update_sous_cat_select())
                update_sous_cat_select()
                
                # Ligne 4: Prix unitaire
                with ui.row().classes('w-full gap-4'):
                    price_input = ui.number('Prix unitaire (EUR)', value=0.0, min=0, step=0.01).classes('w-48 article-price')
                    ui.label('').classes('flex-1')  # Spacer
            
            # Bouton d'action
            with ui.row().classes('gap-2 mt-6 justify-end'):
                def save_article():
                    # Préparer les données pour validation
                    article_data = {
                        'reference': ref_input.value,
                        'designation': desig_input.value,
                        'prix_unitaire': price_input.value
                    }
                    
                    # Valider les données
                    is_valid, error_message = validate_article(article_data)
                    if not is_valid:
                        notify_error(error_message)
                        return
                    
                    # Vérifier que la référence n'existe pas déjà
                    if any(a.reference == ref_input.value for a in app_instance.dm.articles):
                        notify_error(f'La référence "{ref_input.value}" existe déjà')
                        return
                    
                    article_id = max((a.id for a in app_instance.dm.articles), default=0) + 1
                    
                    # Déterminer la catégorie à sauvegarder : sous-catégorie si sélectionnée, sinon catégorie principale
                    final_category = selected_sous_cat['value'] if selected_sous_cat['value'] else categorie_select.value
                    
                    try:
                        new_article = Article(
                            id=article_id,
                            reference=ref_input.value.strip(),
                            designation=desig_input.value.strip(),
                            description=desc_input.value.strip() if desc_input.value else '',
                            unite=unite_select.value or 'm²',
                            prix_unitaire=price_input.value,
                            type_article=type_select.value or 'materiau',
                            categorie=final_category or 'general',
                            fournisseur_id=0  # Par défaut: sans fournisseur
                        )
                        
                        app_instance.dm.add_article(new_article)
                        
                        # Réinitialiser le formulaire
                        ref_input.value = ''
                        desig_input.value = ''
                        desc_input.value = ''
                        unite_select.value = 'm²'
                        type_select.value = 'materiau'
                        categorie_select.value = 'general'
                        price_input.value = 0.0
                        
                        notify_success('Article créé avec succès')
                    except Exception as e:
                        notify_error(f"Erreur lors de la création : {str(e)}")
                
                ui.button('Enregistrer', on_click=save_article).classes('themed-button')
