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
    
    with ui.row().classes('w-full gap-6').style('min-height: calc(100vh - 200px);'):
        # Colonne gauche: Catégories
        with ui.card().classes('w-64 shadow-none border').style('padding: 16px; height: fit-content;'):
            ui.label('Catégories').classes('font-semibold text-lg text-gray-800 mb-4')
            
            categories = {
                'platrerie': 'Plâtrerie',
                'menuiserie_int': 'Menuiserie int.',
                'menuiserie_ext': 'Menuiserie ext.',
                'faux_plafond': 'Faux plafond',
                'agencement': 'Agencement',
                'isolation': 'Isolation',
                'peinture': 'Peinture'
            }
            
            selected_category = {'value': None}  # Pour tracker la catégorie sélectionnée
            
            with ui.column().classes('w-full gap-2'):
                # Bouton "Tous"
                def select_all_categories():
                    selected_category['value'] = None
                    refresh_ouvrages_by_category()
                
                ui.button('Tous', on_click=select_all_categories).props('size=sm').classes('w-full')
                
                # Boutons pour chaque catégorie
                for cat_id, cat_label in categories.items():
                    count = len([o for o in app_instance.dm.ouvrages if o.categorie == cat_id])
                    
                    def select_category(cat=cat_id):
                        selected_category['value'] = cat
                        refresh_ouvrages_by_category()
                    
                    ui.button(f"{cat_label} ({count})", on_click=select_category).props('size=sm flat').classes('w-full text-left')
        
        # Colonne droite: Formulaire et Liste
        with ui.column().classes('flex-1'):
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
                        ui.button('+ Ajouter', on_click=lambda: add_composant()).props('color=primary flat size=sm')
                    
                    composants_list = []  # Liste pour stocker les données des composants
                    composants_container = ui.column().classes('w-full gap-2')
                    next_comp_id = {'value': 1}  # Compteur pour les IDs uniques des composants
                    
                    def refresh_composants_display():
                        """Rafraîchir l'affichage des composants"""
                        composants_container.clear()
                        with composants_container:
                            if not composants_list:
                                ui.label('Aucun composant. Ajoutez-en un ci-dessous.').classes('text-gray-500 text-center py-4')
                                return
                            
                            # En-tête
                            with ui.row().classes('w-full gap-2 p-2 bg-gray-100 rounded font-bold mb-2'):
                                ui.label('ID Article').classes('w-20')
                                ui.label('Désignation').classes('flex-1')
                                ui.label('Quantité').classes('w-20 text-right')
                                ui.label('Unité').classes('w-16 text-center')
                                ui.label('P.U.').classes('w-24 text-right')
                                ui.label('Actions').classes('w-16')
                            
                            # Composants
                            for comp_data in composants_list:
                                with ui.row().classes('w-full gap-2 p-2 bg-gray-50 rounded mb-2 items-center'):
                                    # Afficher l'ID auto-généré (non modifiable)
                                    ui.label(str(comp_data['id'])).classes('w-20 font-mono text-sm')
                                    
                                    # Créer les inputs pour les autres champs
                                    designation_input = ui.input(value=comp_data.get('designation', '')).classes('flex-1 comp-designation')
                                    quantite_input = ui.number(value=comp_data.get('quantite', 1.0), min=0.01, step=0.1).classes('w-20 comp-qte')
                                    unite_input = ui.input(value=comp_data.get('unite', 'm²')).classes('w-16 comp-unite')
                                    pu_input = ui.number(value=comp_data.get('prix_unitaire', 0.0), min=0, step=0.01).classes('w-24 comp-pu')
                                    
                                    # Mettre à jour les données quand les inputs changent
                                    def update_comp_data(comp=comp_data):
                                        comp['designation'] = designation_input.value
                                        comp['quantite'] = quantite_input.value
                                        comp['unite'] = unite_input.value
                                        comp['prix_unitaire'] = pu_input.value
                                    
                                    designation_input.on_value_change(lambda: update_comp_data())
                                    quantite_input.on_value_change(lambda: update_comp_data())
                                    unite_input.on_value_change(lambda: update_comp_data())
                                    pu_input.on_value_change(lambda: update_comp_data())
                                    
                                    def remove_this_comp(comp=comp_data):
                                        if comp in composants_list:
                                            composants_list.remove(comp)
                                        refresh_composants_display()
                                    
                                    ui.button('Retirer', on_click=remove_this_comp).props('size=sm color=negative flat')
                    
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
                    
                    # Boutons d'action
                    with ui.row().classes('gap-2 mt-6 justify-end'):
                        def save_ouvrage():
                            if not reference_input.value or not designation_input.value:
                                notify_error('Veuillez remplir reference et designation')
                                return
                            
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
                            refresh_ouvrages_by_category()
                    
                    ui.button('Enregistrer', on_click=save_ouvrage).classes('themed-button')
            
            # Section Liste des ouvrages existants
            with ui.card().classes('w-full shadow-sm').style('padding: 24px;'):
                ui.label('Ouvrages existants').classes('text-2xl font-bold text-gray-900 mb-6')
                
                ouvrages_container = ui.column().classes('w-full gap-0')
                
                def refresh_ouvrages_by_category():
                    ouvrages_container.clear()
                    
                    # Filtrer les ouvrages par catégorie sélectionnée
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
                                
                                with ui.row().classes('gap-1 w-32'):
                                    ui.button('Editer', on_click=lambda o=ouvrage: notify_info('Édition bientôt disponible')).props('size=sm color=primary flat')
                                    ui.button('Supprimer', on_click=lambda o=ouvrage: (
                                        app_instance.dm.ouvrages.remove(o),
                                        app_instance.dm.save_data(),
                                        refresh_ouvrages_by_category(),
                                        notify_success('Ouvrage supprimé')
                                    )).props('size=sm color=negative flat')
                
                refresh_ouvrages_by_category()
