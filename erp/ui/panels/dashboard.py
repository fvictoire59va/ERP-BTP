"""
Panel du dashboard avec Pygwalker
"""

from nicegui import ui
from pathlib import Path


def create_dashboard_panel(app_instance):
    """Crée le panneau du dashboard avec Pygwalker
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    import pandas as pd
    import pygwalker as pyg
    
    with ui.column().classes('w-full').style('padding: 0; margin: 0;'):
        ui.label('Tableau de bord - Analyse des données').classes('text-3xl font-bold text-gray-900 mb-6').style('padding: 24px 24px 0 24px;')
        
        # Charger les données JSON depuis le dossier data
        data_dir = Path(app_instance.dm.data_dir)
        
        # Préparer les DataFrames
        dataframes = {}
        
        # Charger les devis
        try:
            devis_data = []
            for devis in app_instance.dm.devis_list:
                devis_dict = {
                    'numero': devis.numero,
                    'date': devis.date,
                    'client_id': devis.client_id,
                    'statut': devis.statut,
                    'total_ht': devis.total_ht,
                    'total_ttc': devis.total_ttc,
                    'tva': devis.tva,
                    'coefficient_marge': devis.coefficient_marge,
                    'nb_lignes': len(devis.lignes) if devis.lignes else 0
                }
                devis_data.append(devis_dict)
            if devis_data:
                dataframes['Devis'] = pd.DataFrame(devis_data)
        except Exception as e:
            ui.label(f'Erreur chargement devis: {e}').classes('text-red-500')
        
        # Charger les clients
        try:
            clients_data = []
            for client in app_instance.dm.clients:
                client_dict = {
                    'id': client.id,
                    'nom': client.nom,
                    'prenom': client.prenom,
                    'entreprise': client.entreprise,
                    'ville': client.ville,
                    'cp': client.cp
                }
                clients_data.append(client_dict)
            if clients_data:
                dataframes['Clients'] = pd.DataFrame(clients_data)
        except Exception as e:
            ui.label(f'Erreur chargement clients: {e}').classes('text-red-500')
        
        # Charger les chantiers
        try:
            projets_data = []
            for projet in app_instance.dm.projets:
                projet_dict = {
                    'numero': projet.numero,
                    'client_id': projet.client_id,
                    'date_creation': projet.date_creation,
                    'statut': projet.statut,
                    'nb_devis': len(projet.devis_numeros)
                }
                projets_data.append(projet_dict)
            if projets_data:
                dataframes['Chantiers'] = pd.DataFrame(projets_data)
        except Exception as e:
            ui.label(f'Erreur chargement chantiers: {e}').classes('text-red-500')
        
        # Combiner tous les DataFrames
        if dataframes:
            # Créer un DataFrame combiné principal avec les devis
            df_principal = dataframes.get('Devis', pd.DataFrame())
            
            if not df_principal.empty:
                # Afficher Pygwalker avec thème clair
                try:
                    # Utiliser to_html pour l'intégration web avec thème clair
                    pyg_html = pyg.to_html(
                        df_principal, 
                        spec="", 
                        use_kernel_calc=True,
                        default_tab='data',
                        appearance='light'
                    )
                    ui.html(pyg_html, sanitize=False).style('width: 100%; height: 1200px; overflow: auto; padding: 0 24px;')
                except Exception as e:
                    ui.label(f'Erreur Pygwalker: {e}').classes('text-red-500 text-center py-4')
            else:
                ui.label('Aucune donnée disponible pour l\'analyse').classes('text-gray-500 text-center py-8')
        else:
            ui.label('Aucune donnée disponible').classes('text-gray-500 text-center py-8')
