"""
Panel de gestion des clients

Contient tous les composants pour consulter, éditer et gérer les clients.
"""

from nicegui import ui
from erp.ui.components import create_edit_dialog
from erp.ui.utils import notify_success, notify_error


def create_clients_panel(app_instance):
    """Crée le panneau de gestion des clients
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 48px; min-height: 600px; min-width: 1200px; width: 100%;'):
        ui.label('Clients').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Conteneur du tableau
        table_container = ui.column().classes('w-full gap-0')
        
        def display_clients():
            """Affiche le tableau des clients"""
            app_instance.dm.load_data()
            table_container.clear()
            
            if not app_instance.dm.clients:
                with table_container:
                    ui.label('Aucun client trouvé').classes('text-gray-500 text-center py-8')
                return
            
            with table_container:
                # Headers
                with ui.row().classes('w-full gap-2 font-bold bg-gray-100 p-2 rounded text-sm'):
                    ui.label('Nom').classes('w-40 font-semibold')
                    ui.label('Prenom').classes('w-40 font-semibold')
                    ui.label('Entreprise').classes('flex-1 font-semibold')
                    ui.label('Email').classes('w-40 font-semibold')
                    ui.label('Telephone').classes('w-32 font-semibold')
                    ui.label('Actions').classes('w-32')
                
                # Rows
                for idx, client in enumerate(app_instance.dm.clients):
                    with ui.row().classes('w-full gap-2 p-1 items-center hover:bg-gray-50 text-sm border-b border-gray-100'):
                        ui.label(client.nom).classes('w-40')
                        ui.label(client.prenom).classes('w-40')
                        ui.label(client.entreprise).classes('flex-1')
                        ui.label(client.email).classes('w-40 text-xs')
                        ui.label(client.telephone).classes('w-32')
                        
                        with ui.row().classes('gap-2 items-center'):
                            def make_modify_handler(client_id):
                                """Factory function pour créer le handler de modification"""
                                def on_modify_click():
                                    # Trouver le client dans les données actuelles
                                    client = next((c for c in app_instance.dm.clients if c.id == client_id), None)
                                    if not client:
                                        notify_error('Client non trouvé')
                                        return
                                    
                                    def save_client(values):
                                        # Recharger le client au cas où il aurait changé
                                        client_updated = next((c for c in app_instance.dm.clients if c.id == client_id), None)
                                        if not client_updated:
                                            return
                                        
                                        # Mettre à jour le client
                                        client_updated.nom = values.get('nom', '')
                                        client_updated.prenom = values.get('prenom', '')
                                        client_updated.entreprise = values.get('entreprise', '')
                                        client_updated.email = values.get('email', '')
                                        client_updated.telephone = values.get('telephone', '')
                                        client_updated.adresse = values.get('adresse', '')
                                        
                                        app_instance.dm.save_data()
                                        display_clients()
                                        notify_success('Client modifié avec succès')
                                    
                                    # Créer la dialog avec create_edit_dialog
                                    edit_dialog = create_edit_dialog(
                                        'Modifier le client',
                                        fields=[
                                            {'type': 'input', 'label': 'Nom', 'value': client.nom, 'key': 'nom'},
                                            {'type': 'input', 'label': 'Prenom', 'value': client.prenom, 'key': 'prenom'},
                                            {'type': 'input', 'label': 'Entreprise', 'value': client.entreprise, 'key': 'entreprise'},
                                            {'type': 'input', 'label': 'Email', 'value': client.email, 'key': 'email'},
                                            {'type': 'input', 'label': 'Telephone', 'value': client.telephone, 'key': 'telephone'},
                                            {'type': 'input', 'label': 'Adresse', 'value': client.adresse, 'key': 'adresse'},
                                        ],
                                        on_save=save_client
                                    )
                                    edit_dialog.open()
                                
                                return on_modify_click
                            
                            def make_delete_handler(client_id):
                                def delete_client():
                                    notify_success(f'Client supprimé')
                                    app_instance.dm.clients = [c for c in app_instance.dm.clients if c.id != client_id]
                                    app_instance.dm.save_data()
                                    display_clients()
                                return delete_client
                            
                            with ui.button(on_click=make_modify_handler(client.id)).props('flat').classes('themed-link hover:bg-gray-100'):
                                ui.icon('edit').classes('text-xl')
                            with ui.button(on_click=make_delete_handler(client.id)).props('flat').classes('text-red-600 hover:bg-red-50'):
                                ui.icon('delete').classes('text-xl')
        
        # Afficher le tableau une première fois
        display_clients()
