"""
Panel de gestion du catalogue d'articles

Contient tous les composants pour créer, éditer et gérer les articles.
"""

from nicegui import ui
from erp.core.models import Article
from erp.ui.components import create_edit_dialog
from erp.ui.utils import notify_success, notify_error


def create_catalogue_panel(app_instance):
    """Crée le panneau de gestion des articles
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
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
                
                # Ligne 3: Catégorie et Unité
                with ui.row().classes('w-full gap-4'):
                    categorie_select = ui.select(
                        label='Catégorie',
                        options={
                            'general': 'Général',
                            'platrerie': 'Plâtrerie',
                            'menuiserie_int': 'Menuiserie Int.',
                            'menuiserie_ext': 'Menuiserie Ext.',
                            'faux_plafond': 'Faux Plafond',
                            'agencement': 'Agencement',
                            'isolation': 'Isolation',
                            'peinture': 'Peinture'
                        },
                        value='general'
                    ).classes('w-48 article-categorie')
                    unite_select = ui.select(
                        label='Unité',
                        options={'m²': 'm²', 'ml': 'ml', 'u': 'unité', 'h': 'heure', 'kg': 'kg', 'l': 'l', 'forfait': 'forfait'}
                    ).classes('w-32 article-unite')
                
                # Ligne 4: Prix unitaire
                with ui.row().classes('w-full gap-4'):
                    price_input = ui.number('Prix unitaire (EUR)', value=0.0, min=0, step=0.01).classes('w-48 article-price')
                    ui.label('').classes('flex-1')  # Spacer
            
            # Bouton d'action
            with ui.row().classes('gap-2 mt-6 justify-end'):
                def save_article():
                    if not ref_input.value or not desig_input.value:
                        notify_error('Veuillez remplir référence et désignation')
                        return
                    
                    # Vérifier que la référence n'existe pas déjà
                    if any(a.reference == ref_input.value for a in app_instance.dm.articles):
                        notify_error(f'La référence "{ref_input.value}" existe déjà')
                        return
                    
                    article_id = max((a.id for a in app_instance.dm.articles), default=0) + 1
                    new_article = Article(
                        id=article_id,
                        reference=ref_input.value,
                        designation=desig_input.value,
                        description=desc_input.value,
                        unite=unite_select.value or 'm²',
                        prix_unitaire=price_input.value,
                        type_article=type_select.value or 'materiau',
                        categorie=categorie_select.value or 'general',
                        fournisseur_id=0  # Par défaut: sans fournisseur
                    )
                    
                    app_instance.dm.articles.append(new_article)
                    app_instance.dm.save_data()
                    
                    # Réinitialiser le formulaire
                    ref_input.value = ''
                    desig_input.value = ''
                    desc_input.value = ''
                    unite_select.value = 'm²'
                    type_select.value = 'materiau'
                    categorie_select.value = 'general'
                    price_input.value = 0.0
                    
                    notify_success('Article créé avec succès')
                
                ui.button('Enregistrer', on_click=save_article).classes('themed-button')
