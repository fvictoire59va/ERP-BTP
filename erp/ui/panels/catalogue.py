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
                    refresh_articles_list()
                
                ui.button('Enregistrer', on_click=save_article).classes('themed-button')
        
        # Section Liste des articles existants
        with ui.card().classes('w-full shadow-sm').style('padding: 24px;'):
            ui.label('Articles existants').classes('text-2xl font-bold text-gray-900 mb-6')
            
            articles_container = ui.column().classes('w-full gap-0')
            
            def refresh_articles_list():
                app_instance.dm.load_data()  # Recharger les données du fichier
                articles_container.clear()
                
                if not app_instance.dm.articles:
                    with articles_container:
                        ui.label('Aucun article. Créez-en un ci-dessus.').classes('text-gray-500 text-center py-8')
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
                    for article in app_instance.dm.articles:
                        article_id = article.id  # Capturer l'ID immédiatement
                        with ui.row().classes('w-full gap-2 p-1 items-center hover:bg-gray-50 text-sm border-b border-gray-100'):
                            ui.label(article.reference).classes('w-40 font-mono')
                            ui.label(article.designation).classes('flex-1')
                            ui.label(article.type_article).classes('w-32 text-center')
                            ui.label(getattr(article, 'categorie', 'general')).classes('w-32 text-center')
                            ui.label(article.unite).classes('w-20 text-center')
                            ui.label(f"{article.prix_unitaire:.2f} EUR").classes('w-32 text-right font-semibold')
                            
                            def make_edit_handler(article_id_val):
                                """Factory function pour créer le handler d'édition"""
                                def on_modify_click():
                                    # Trouver l'article dans les données actuelles
                                    art = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                    if not art:
                                        notify_error('Article non trouvé')
                                        return
                                    
                                    def save_article_update(values):
                                        # Recharger l'article au cas où il aurait changé
                                        art_updated = next((a for a in app_instance.dm.articles if a.id == article_id_val), None)
                                        if not art_updated:
                                            return
                                        
                                        # Vérifier la référence si elle a changé
                                        if values.get('référence') != art_updated.reference:
                                            if any(a.reference == values.get('référence') for a in app_instance.dm.articles if a.id != art_updated.id):
                                                notify_error(f'La référence "{values.get("référence")}" existe déjà')
                                                return
                                        
                                        # Mettre à jour l'article
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
                                    
                                    # Créer la dialog avec create_edit_dialog
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
