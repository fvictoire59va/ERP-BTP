"""
Panel de gestion des ouvrages

Contient tous les composants pour créer, éditer et gérer les ouvrages.
"""

from nicegui import ui
from erp.core.models import Ouvrage, ComposantOuvrage
from erp.ui.utils import notify_success, notify_error, notify_info


def create_ouvrages_panel(app_instance):
    """Crée le panneau de gestion des ouvrages
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Ajouter le style CSS global pour masquer les flèches des champs number
    ui.add_head_html('''
        <style>
            .no-spinner input[type=number]::-webkit-inner-spin-button,
            .no-spinner input[type=number]::-webkit-outer-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }
            .no-spinner input[type=number] {
                -moz-appearance: textfield;
            }
        </style>
    ''')
    
    with ui.column().classes('w-full'):
            # Section pour ajouter un nouvel ouvrage
            with ui.card().classes('w-full shadow-sm').style('padding: 24px;'):
                ui.label('Ajouter un nouvel ouvrage').classes('text-2xl font-bold text-gray-900 mb-6')
                
                with ui.column().classes('w-full gap-4'):
                    # Ligne 1: Reference et Designation
                    with ui.row().classes('w-full gap-4'):
                        reference_input = ui.input('Reference', placeholder='CLO-BA13-SIMPLE').classes('flex-1 ouvrage-reference')
                        designation_input = ui.input('Designation', placeholder='Cloison BA13 simple...').classes('flex-1 ouvrage-designation')
                    
                    # Ligne 2: Description et Catégorie
                    with ui.row().classes('w-full gap-4'):
                        description_input = ui.textarea('Description', placeholder='Courte description').classes('flex-1 ouvrage-description').props('rows=2')
                        categorie_select = ui.select(
                            label='Catégorie',
                            options={
                                'platrerie': 'Plâtrerie',
                                'menuiserie_int': 'Menuiserie intérieure',
                                'menuiserie_ext': 'Menuiserie extérieure',
                                'faux_plafond': 'Faux plafond',
                                'agencement': 'Agencement',
                                'isolation': 'Isolation',
                                'peinture': 'Peinture'
                            }
                        ).classes('w-48 ouvrage-categorie')
                    
                    # Ligne 3: Unité
                    with ui.row().classes('w-full gap-4'):
                        unite_select = ui.select(
                            label='Unité',
                            options={
                                'm²': 'm²',
                                'ml': 'ml',
                                'u': 'unité',
                                'forfait': 'forfait'
                            }
                        ).classes('w-32 ouvrage-unite')
                        ui.label('').classes('flex-1')  # Spacer
                
                # Section Composants
                with ui.card().classes('w-full shadow-none border').style('padding: 16px;'):
                    with ui.row().classes('w-full justify-between items-center mb-4'):
                        ui.label('Composants').classes('font-semibold text-lg text-gray-800')
                        with ui.row().classes('gap-2'):
                            ui.button('+ Ajouter manuellement', on_click=lambda: add_composant()).classes('themed-button').props('size=sm')
                            ui.button('📦 Choisir dans le catalogue', on_click=lambda: add_article_from_catalogue()).classes('themed-button').props('size=sm')
                    
                    composants_list = []  # Liste pour stocker les données des composants
                    composants_container = ui.column().classes('w-full gap-2')
                    next_comp_id = {'value': 1}  # Compteur pour les IDs uniques des composants
                    edit_mode = {'active': False, 'ouvrage_id': None}  # Mode édition
                    
                    def refresh_composants_display():
                        """Rafraîchir l'affichage des composants"""
                        composants_container.clear()
                        with composants_container:
                            if not composants_list:
                                ui.label('Aucun composant. Ajoutez-en un ci-dessous.').classes('text-gray-500 text-center py-4')
                                return
                            
                            # En-tête (format style devis)
                            with ui.row().classes('w-full gap-2 font-bold bg-gray-100 p-2 rounded'):
                                ui.label('Article').classes('flex-1')
                                ui.label('Qte').classes('w-16 text-right')
                                ui.label('Unité').classes('w-16 text-center')
                                ui.label('P.U.').classes('w-20 text-right')
                                ui.label('Total').classes('w-24 text-right')
                                ui.label('Actions').classes('w-24')
                            # Lignes composants
                            for comp_data in composants_list:
                                with ui.row().classes('w-full gap-2 py-1 px-2 items-center border-b border-gray-100'):
                                    designation_input = ui.input(value=comp_data.get('designation', '')).classes('flex-1 comp-designation').props('dense')
                                    quantite_input = ui.number(value=comp_data.get('quantite', 1.0), min=0.01, step=0.1).classes('w-16 comp-qte text-right no-spinner').props('dense')
                                    unite_input = ui.input(value=comp_data.get('unite', 'm²')).classes('w-16 comp-unite text-center').props('dense')
                                    pu_input = ui.number(value=comp_data.get('prix_unitaire', 0.0), min=0, step=0.01).classes('w-20 comp-pu text-right no-spinner').props('dense')
                                    total_label = ui.label(f"{(quantite_input.value or 0) * (pu_input.value or 0):.2f}").classes('w-24 text-right font-bold')
                                    # Mise à jour dynamique du total
                                    def update_comp_data(comp=comp_data, des=designation_input, qte=quantite_input, uni=unite_input, pu=pu_input, total=total_label):
                                        comp['designation'] = des.value
                                        comp['quantite'] = qte.value
                                        comp['unite'] = uni.value
                                        comp['prix_unitaire'] = pu.value
                                        try:
                                            total.text = f"{(float(qte.value or 0) * float(pu.value or 0)):.2f}"
                                        except Exception:
                                            total.text = "0.00"
                                    designation_input.on_value_change(lambda e, c=comp_data, d=designation_input, q=quantite_input, u=unite_input, p=pu_input, t=total_label: update_comp_data(c, d, q, u, p, t))
                                    quantite_input.on_value_change(lambda e, c=comp_data, d=designation_input, q=quantite_input, u=unite_input, p=pu_input, t=total_label: update_comp_data(c, d, q, u, p, t))
                                    unite_input.on_value_change(lambda e, c=comp_data, d=designation_input, q=quantite_input, u=unite_input, p=pu_input, t=total_label: update_comp_data(c, d, q, u, p, t))
                                    pu_input.on_value_change(lambda e, c=comp_data, d=designation_input, q=quantite_input, u=unite_input, p=pu_input, t=total_label: update_comp_data(c, d, q, u, p, t))
                                    with ui.row().classes('gap-1 w-24 justify-end'):
                                        ui.button(icon='delete', on_click=lambda comp=comp_data: (composants_list.remove(comp), refresh_composants_display()) if comp in composants_list else None).props('flat dense color=negative').classes('text-red-600')
                    
                    def add_composant():
                        # Générer un nouvel ID unique et incrémental
                        comp_id = next_comp_id['value']
                        next_comp_id['value'] += 1
                        
                        comp_data = {
                            'id': comp_id,
                            'designation': '',
                            'quantite': 1.0,
                            'unite': 'm²',
                            'prix_unitaire': 0.0
                        }
                        composants_list.append(comp_data)
                        refresh_composants_display()
                    
                    def add_article_from_catalogue():
                        """Ouvrir un dialogue pour choisir un article du catalogue"""
                        with ui.dialog() as article_dialog, ui.card().classes('w-full max-w-4xl'):
                            ui.label('Choisir un article du catalogue').classes('text-xl font-bold mb-4')
                            
                            # Conteneur pour les filtres
                            with ui.row().classes('w-full gap-4 mb-4'):
                                search_input = ui.input(placeholder='Rechercher (référence, désignation...)').classes('flex-1')
                                categorie_filter = ui.select(
                                    label='Catégorie',
                                    options={
                                        'toutes': 'Toutes',
                                        'general': 'Général',
                                        'platrerie': 'Plâtrerie',
                                        'menuiserie_int': 'Menuiserie Int.',
                                        'menuiserie_ext': 'Menuiserie Ext.',
                                        'faux_plafond': 'Faux Plafond',
                                        'agencement': 'Agencement',
                                        'isolation': 'Isolation',
                                        'peinture': 'Peinture'
                                    },
                                    value='toutes'
                                ).classes('w-48')
                                type_filter = ui.select(
                                    label='Type',
                                    options={
                                        'tous': 'Tous',
                                        'materiau': 'Matériau',
                                        'fourniture': 'Fourniture',
                                        'main_oeuvre': 'Main d\'œuvre',
                                        'consommable': 'Consommable'
                                    },
                                    value='tous'
                                ).classes('w-48')
                            
                            # Conteneur pour la liste des articles
                            articles_list_container = ui.column().classes('w-full gap-0 max-h-96 overflow-y-auto')
                            
                            def filter_articles():
                                """Filtrer et afficher les articles"""
                                articles_list_container.clear()
                                
                                # Récupérer tous les articles
                                articles = app_instance.dm.articles
                                
                                # Filtrer par catégorie
                                if categorie_filter.value != 'toutes':
                                    articles = [a for a in articles if getattr(a, 'categorie', 'general') == categorie_filter.value]
                                
                                # Filtrer par type
                                if type_filter.value != 'tous':
                                    articles = [a for a in articles if a.type_article == type_filter.value]
                                
                                # Filtrer par recherche texte
                                if search_input.value:
                                    search_term = search_input.value.lower()
                                    articles = [a for a in articles if 
                                               search_term in a.reference.lower() or 
                                               search_term in a.designation.lower()]
                                
                                if not articles:
                                    with articles_list_container:
                                        ui.label('Aucun article trouvé').classes('text-gray-500 text-center py-8')
                                    return
                                
                                with articles_list_container:
                                    # En-tête
                                    with ui.row().classes('w-full gap-2 p-2 bg-gray-100 rounded font-bold mb-2'):
                                        ui.label('Référence').classes('w-32')
                                        ui.label('Désignation').classes('flex-1')
                                        ui.label('Type').classes('w-32')
                                        ui.label('Unité').classes('w-20')
                                        ui.label('Prix U.').classes('w-24 text-right')
                                        ui.label('Action').classes('w-24')
                                    
                                    # Lignes d'articles
                                    for article in articles:
                                        with ui.row().classes('w-full gap-2 p-2 hover:bg-gray-50 items-center border-b border-gray-100'):
                                            ui.label(article.reference).classes('w-32 font-mono text-sm')
                                            ui.label(article.designation).classes('flex-1')
                                            ui.label(article.type_article).classes('w-32 text-sm text-gray-600')
                                            ui.label(article.unite).classes('w-20 text-center')
                                            ui.label(f"{article.prix_unitaire:.2f}€").classes('w-24 text-right')
                                            
                                            def add_this_article(art=article):
                                                # Ajouter l'article comme composant
                                                comp_id = next_comp_id['value']
                                                next_comp_id['value'] += 1
                                                
                                                comp_data = {
                                                    'id': comp_id,
                                                    'designation': art.designation,
                                                    'quantite': 1.0,
                                                    'unite': art.unite,
                                                    'prix_unitaire': art.prix_unitaire
                                                }
                                                composants_list.append(comp_data)
                                                refresh_composants_display()
                                                article_dialog.close()
                                                notify_success(f'Article "{art.designation}" ajouté')
                                            
                                            ui.button('Ajouter', on_click=add_this_article).classes('themed-button').props('size=sm')
                            
                            # Événements pour le filtrage en temps réel
                            search_input.on_value_change(lambda: filter_articles())
                            categorie_filter.on_value_change(lambda: filter_articles())
                            type_filter.on_value_change(lambda: filter_articles())
                            
                            # Affichage initial
                            filter_articles()
                            
                            # Bouton fermer
                            with ui.row().classes('w-full justify-end mt-4'):
                                ui.button('Fermer', on_click=article_dialog.close).props('flat')
                        
                        article_dialog.open()
                    
                    def load_ouvrage_for_edit(ouvrage):
                        """Charger un ouvrage dans le formulaire pour édition"""
                        # Activer le mode édition
                        edit_mode['active'] = True
                        edit_mode['ouvrage_id'] = ouvrage.id
                        
                        # Remplir les champs du formulaire
                        reference_input.value = ouvrage.reference
                        designation_input.value = ouvrage.designation
                        description_input.value = ouvrage.description
                        categorie_select.set_value(ouvrage.categorie)
                        unite_select.set_value(ouvrage.unite)
                        
                        # Charger les composants
                        composants_list.clear()
                        next_comp_id['value'] = 1
                        
                        for comp in ouvrage.composants:
                            comp_data = {
                                'id': next_comp_id['value'],
                                'designation': comp.designation,
                                'quantite': comp.quantite,
                                'unite': comp.unite,
                                'prix_unitaire': comp.prix_unitaire
                            }
                            composants_list.append(comp_data)
                            next_comp_id['value'] += 1
                        
                        refresh_composants_display()
                        notify_info(f'Édition de l\'ouvrage "{ouvrage.designation}"')
                    
                    # Vérifier s'il y a un ouvrage à charger pour édition
                    if hasattr(app_instance, 'ouvrage_to_edit') and app_instance.ouvrage_to_edit:
                        load_ouvrage_for_edit(app_instance.ouvrage_to_edit)
                        app_instance.ouvrage_to_edit = None  # Nettoyer après chargement
                    
                    # Boutons d'action
                    with ui.row().classes('gap-2 mt-6 justify-end'):
                        def save_ouvrage():
                            if not reference_input.value or not designation_input.value:
                                notify_error('Veuillez remplir reference et designation')
                                return
                            
                            if edit_mode['active']:
                                # Mode édition - Modifier l'ouvrage existant
                                ouvrage = next((o for o in app_instance.dm.ouvrages if o.id == edit_mode['ouvrage_id']), None)
                                if not ouvrage:
                                    notify_error('Ouvrage introuvable')
                                    return
                                
                                # Vérifier que la référence n'est pas déjà utilisée par un autre ouvrage
                                if any(o.reference == reference_input.value and o.id != edit_mode['ouvrage_id'] for o in app_instance.dm.ouvrages):
                                    notify_error(f'La référence "{reference_input.value}" existe déjà')
                                    return
                                
                                # Mettre à jour les propriétés
                                ouvrage.reference = reference_input.value
                                ouvrage.designation = designation_input.value
                                ouvrage.description = description_input.value
                                ouvrage.categorie = categorie_select.value or 'platrerie'
                                ouvrage.unite = unite_select.value or 'm²'
                                
                                # Remplacer les composants
                                ouvrage.composants.clear()
                                for comp_data in composants_list:
                                    comp = ComposantOuvrage(
                                        article_id=comp_data['id'],
                                        designation=comp_data['designation'],
                                        quantite=comp_data['quantite'],
                                        unite=comp_data['unite'],
                                        prix_unitaire=comp_data['prix_unitaire']
                                    )
                                    ouvrage.composants.append(comp)
                                
                                app_instance.dm.save_data()
                                
                                # Réinitialiser le formulaire
                                reference_input.value = ''
                                designation_input.value = ''
                                description_input.value = ''
                                composants_list.clear()
                                composants_container.clear()
                                edit_mode['active'] = False
                                edit_mode['ouvrage_id'] = None
                                
                                notify_success('Ouvrage modifié avec succès')
                                refresh_ouvrages_by_category()
                            else:
                                # Mode création - Créer un nouvel ouvrage
                                # Vérifier que la référence n'existe pas déjà
                                if any(o.reference == reference_input.value for o in app_instance.dm.ouvrages):
                                    notify_error(f'La référence "{reference_input.value}" existe déjà')
                                    return
                                
                                # Créer l'ouvrage (sans coefficient_marge)
                                new_ouvrage = Ouvrage(
                                    id=max((o.id for o in app_instance.dm.ouvrages), default=0) + 1,
                                    reference=reference_input.value,
                                    designation=designation_input.value,
                                    description=description_input.value,
                                    categorie=categorie_select.value or 'platrerie',
                                    unite=unite_select.value or 'm²'
                                )
                                
                                # Ajouter les composants
                                for comp_data in composants_list:
                                    comp = ComposantOuvrage(
                                        article_id=comp_data['id'],  # Utiliser l'ID généré automatiquement
                                        designation=comp_data['designation'],
                                        quantite=comp_data['quantite'],
                                        unite=comp_data['unite'],
                                        prix_unitaire=comp_data['prix_unitaire']
                                    )
                                    new_ouvrage.composants.append(comp)
                                
                                # Ajouter à la liste et sauvegarder
                                app_instance.dm.ouvrages.append(new_ouvrage)
                                app_instance.dm.save_data()
                                
                                # Réinitialiser le formulaire
                                reference_input.value = ''
                                designation_input.value = ''
                                description_input.value = ''
                                composants_list.clear()
                                composants_container.clear()
                                
                                notify_success('Ouvrage créé avec succès')
                    
                # Bouton Enregistrer en dehors du cadre des composants
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Enregistrer', on_click=save_ouvrage).classes('themed-button')
