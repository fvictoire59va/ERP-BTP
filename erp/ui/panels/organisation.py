"""
Panel de gestion de l'organisation
"""

from nicegui import ui
from erp.ui.components import create_edit_dialog
from erp.ui.utils import notify_success


def create_company_panel(app_instance):
    """Crée le panneau de gestion de l'organisation
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Créer la card dans le contexte actuel (content_container)
    with ui.card().classes('w-full shadow-sm').style('padding: 48px; min-height: 600px; min-width: 1200px;'):
        ui.label('Informations de l\'organisation').classes('text-2xl font-bold mb-8')
        
        # Créer le conteneur DANS la card
        org_container = ui.column().classes('w-full')
        
        def display_organisation():
            """Affiche les informations de l'organisation"""
            org_container.clear()
            with org_container:
                with ui.column().classes('w-full gap-6'):
                    # Display mode
                    with ui.row().classes('w-full gap-6 p-6 bg-gray-50 rounded'):
                        with ui.column().classes('flex-1'):
                            ui.label('Nom').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.nom or '-').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label('SIRET').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.siret or '-').classes('text-lg')
                    
                    with ui.row().classes('w-full gap-6 p-6 bg-gray-50 rounded'):
                        with ui.column().classes('flex-1'):
                            ui.label('Adresse').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.adresse or '-').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label('Code Postal').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.cp or '-').classes('text-lg')
                    
                    with ui.row().classes('w-full gap-6 p-6 bg-gray-50 rounded'):
                        with ui.column().classes('flex-1'):
                            ui.label('Ville').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.ville or '-').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label('Téléphone').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.telephone or '-').classes('text-lg')
                    
                    with ui.row().classes('w-full gap-6 p-6 bg-gray-50 rounded'):
                        with ui.column().classes('flex-1'):
                            ui.label('Email').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.email or '-').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label('Site Web').classes('font-semibold text-base')
                            ui.label(app_instance.dm.organisation.site_web or '-').classes('text-lg')
                    
                    with ui.row().classes('w-full gap-6 p-6 bg-gray-50 rounded'):
                        with ui.column().classes('flex-1'):
                            ui.label('Début d\'exercice').classes('font-semibold text-base')
                            ui.label(getattr(app_instance.dm.organisation, 'date_debut_exercice', None) or '-').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label('Fin d\'exercice').classes('font-semibold text-base')
                            ui.label(getattr(app_instance.dm.organisation, 'date_fin_exercice', None) or '-').classes('text-lg')
                    
                    # Edit button
                    with ui.row().classes('gap-2 mt-8 justify-end'):
                        def on_modify_click():
                            org = app_instance.dm.organisation
                            
                            def save_organisation(values):
                                # Mettre à jour l'organisation
                                org.nom = values.get('nom', '')
                                org.siret = values.get('siret', '')
                                org.adresse = values.get('adresse', '')
                                org.cp = values.get('code_postal', '')
                                org.ville = values.get('ville', '')
                                org.telephone = values.get('téléphone', '')
                                org.email = values.get('email', '')
                                org.site_web = values.get('site_web', '')
                                org.date_debut_exercice = values.get('date_debut_exercice', '')
                                org.date_fin_exercice = values.get('date_fin_exercice', '')
                                
                                app_instance.dm.save_data()
                                display_organisation()
                                notify_success('Organisation modifiée avec succès')
                            
                            # Créer la dialog avec create_edit_dialog
                            edit_dialog = create_edit_dialog(
                                'Modifier l\'organisation',
                                fields=[
                                    {'type': 'input', 'label': 'Nom', 'value': org.nom, 'key': 'nom'},
                                    {'type': 'input', 'label': 'SIRET', 'value': org.siret, 'key': 'siret'},
                                    {'type': 'input', 'label': 'Adresse', 'value': org.adresse, 'key': 'adresse'},
                                    {'type': 'input', 'label': 'Code Postal', 'value': org.cp, 'key': 'code_postal'},
                                    {'type': 'input', 'label': 'Ville', 'value': org.ville, 'key': 'ville'},
                                    {'type': 'input', 'label': 'Téléphone', 'value': org.telephone, 'key': 'téléphone'},
                                    {'type': 'input', 'label': 'Email', 'value': org.email, 'key': 'email'},
                                    {'type': 'input', 'label': 'Site Web', 'value': org.site_web, 'key': 'site_web'},
                                    {'type': 'date', 'label': 'Début d\'exercice', 'value': getattr(org, 'date_debut_exercice', ''), 'key': 'date_debut_exercice'},
                                    {'type': 'date', 'label': 'Fin d\'exercice', 'value': getattr(org, 'date_fin_exercice', ''), 'key': 'date_fin_exercice'},
                                ],
                                on_save=save_organisation
                            )
                            edit_dialog.open()
                        
                        ui.button('Modifier', on_click=on_modify_click).classes('themed-button')
        
        # Afficher les données
        display_organisation()
