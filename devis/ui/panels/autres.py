"""
Panels supplémentaires

Contient: liste des devis, dashboard et gestion de l'organisation.
"""

from nicegui import ui
from pathlib import Path
from devis.config.theme import get_theme, set_accent_color, THEME_PRESETS
from devis.ui.components import create_edit_dialog
from devis.ui.utils import notify_success, notify_error


def create_liste_devis_panel(app_instance):
    """Crée le panneau de liste des devis
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        ui.label('Liste des Devis').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Conteneur du tableau
        table_container = ui.column().classes('w-full gap-0')
        
        def display_table():
            """Affiche le tableau des devis"""
            app_instance.dm.load_data()
            table_container.clear()
            
            if not app_instance.dm.devis_list:
                with table_container:
                    ui.label('Aucun devis trouvé').classes('text-gray-500 text-center py-8')
                return
            
            with table_container:
                # Headers
                with ui.row().classes('w-full gap-2 font-bold bg-gray-100 px-2 py-0.5 rounded text-sm'):
                    ui.label('').classes('w-6 text-center')
                    ui.label('Numéro').classes('w-32 font-semibold text-center')
                    ui.label('Date').classes('w-20 font-semibold text-center')
                    ui.label('Client').classes('flex-1 font-semibold')
                    ui.label('Statut').classes('w-24 font-semibold text-center')
                    ui.label('Total HT').classes('w-20 text-right font-semibold')
                    ui.label('Total TTC').classes('w-20 text-right font-semibold')
                    ui.label('Actions').classes('w-32 text-center')
                
                # Rows
                for idx, devis in enumerate(app_instance.dm.devis_list):
                    # Créer une copie locale de devis pour éviter les problèmes de closure
                    current_devis = devis
                    client = app_instance.dm.get_client_by_id(current_devis.client_id)
                    client_name = f"{client.prenom} {client.nom}" if client else "Client inconnu"
                    
                    with ui.row().classes('w-full gap-2 px-2 py-0.5 items-center hover:bg-gray-50 text-sm border-b border-gray-200'):
                        # État du bouton toggle pour chaque devis
                        toggle_state = {'expanded': False}
                        details_container = None
                        expand_btn = None
                        
                        expand_btn = ui.button('▶').props('flat size=xs').classes('w-6')
                        ui.label(current_devis.numero).classes('w-32 font-medium themed-accent')
                        ui.label(current_devis.date).classes('w-20')
                        ui.label(client_name).classes('flex-1')
                        
                        # Selecteur de statut
                        statut_options = ['en cours', 'envoyé', 'refusé', 'accepté']
                        def make_statut_handler(devis_obj):
                            def on_statut_change(e):
                                devis_obj.statut = e.value
                                app_instance.dm.save_data()
                            return on_statut_change
                        
                        ui.select(options=statut_options, value=current_devis.statut, on_change=make_statut_handler(current_devis)).classes('w-32').props('size=sm dense').style('text-align: center;')
                        
                        ui.label(f"{current_devis.total_ht:.2f} EUR").classes('w-20 text-right text-xs')
                        ui.label(f"{current_devis.total_ttc:.2f} EUR").classes('w-20 text-right font-bold text-xs')
                        
                        with ui.row().classes('gap-2 items-center w-32 justify-end'):
                            def make_modify_handler(devis_numero, devis_obj):
                                def modify_devis():
                                    # Copier les lignes du devis sélectionné
                                    app_instance.current_devis_lignes = list(devis_obj.lignes) if devis_obj.lignes else []
                                    app_instance.current_devis_coefficient = devis_obj.coefficient_marge
                                    app_instance.selected_client_id = devis_obj.client_id
                                    
                                    # Naviguer vers la section devis avec le nouveau système de menu
                                    if hasattr(app_instance, 'show_section_with_children'):
                                        # Mettre à jour la section courante
                                        app_instance.current_section['value'] = 'devis'
                                        # Naviguer vers la section Devis avec son menu horizontal
                                        app_instance.show_section_with_children('devis', ['devis', 'liste'])
                                        # Sélectionner l'onglet 'devis' dans le menu horizontal
                                        if hasattr(app_instance, 'tab_selector'):
                                            app_instance.tab_selector.value = 'devis_tab'
                                    
                                    # Attendre que le panneau soit créé, puis charger les données
                                    def load_devis_data():
                                        if hasattr(app_instance, 'numero_devis_field'):
                                            app_instance.numero_devis_field.set_value(devis_obj.numero)
                                        if hasattr(app_instance, 'date_devis_field'):
                                            app_instance.date_devis_field.set_value(devis_obj.date)
                                        if hasattr(app_instance, 'client_select'):
                                            app_instance.client_select.set_value(devis_obj.client_id)
                                        if hasattr(app_instance, 'tva_rate_field'):
                                            app_instance.tva_rate_field.set_value(devis_obj.tva)
                                        
                                        # Recalculer next_ligne_id basé sur les lignes existantes
                                        if devis_obj.lignes:
                                            app_instance.next_ligne_id = max(l.id for l in devis_obj.lignes) + 1
                                        else:
                                            app_instance.next_ligne_id = 0
                                        
                                        # Rafraîchir le tableau des lignes
                                        if hasattr(app_instance, 'refresh_devis_table'):
                                            app_instance.refresh_devis_table()
                                        app_instance.update_totals()
                                        notify_success(f'Devis {devis_numero} chargé pour modification')
                                    
                                    ui.timer(0.2, load_devis_data, once=True)
                                return modify_devis
                            
                            def make_pdf_handler(numero=current_devis.numero, client_id=current_devis.client_id, devis_obj=current_devis):
                                def generate_pdf_devis():
                                    try:
                                        from devis.services.pdf_service import generate_pdf as generate_pdf_file
                                        
                                        # Recharger le devis depuis le fichier pour avoir les modifications récentes
                                        updated_devis = app_instance.dm.get_devis_by_numero(numero)
                                        if not updated_devis:
                                            notify_error(f'Devis {numero} non trouvé')
                                            return
                                        
                                        client = app_instance.dm.get_client_by_id(client_id)
                                        client_name = f"{client.prenom}_{client.nom}" if client else "Client_inconnu"
                                        client_name = client_name.replace(" ", "_")
                                        
                                        pdf_dir = app_instance.dm.data_dir / 'pdf' / client_name
                                        pdf_dir.mkdir(parents=True, exist_ok=True)
                                        pdf_path = pdf_dir / f"{numero}.pdf"
                                        
                                        generate_pdf_file(updated_devis, app_instance.dm, pdf_path)
                                        notify_success(f'PDF généré: {pdf_path}')
                                    except Exception as e:
                                        notify_error(f'Erreur: {str(e)}')
                                return generate_pdf_devis
                            
                            def make_delete_handler(numero=current_devis.numero):
                                def delete_devis():
                                    for d in app_instance.dm.devis_list[:]:
                                        if d.numero == numero:
                                            app_instance.dm.devis_list.remove(d)
                                            app_instance.dm.save_data()
                                            display_table()
                                            notify_success(f'Devis {numero} supprimé')
                                            break
                                return delete_devis
                            
                            app_instance.material_icon_button('edit', on_click=make_modify_handler(current_devis.numero, current_devis))
                            app_instance.material_icon_button('picture_as_pdf', on_click=make_pdf_handler(), color_class='text-orange-600', hover_class='hover:bg-orange-50')
                            app_instance.material_icon_button('delete', on_click=make_delete_handler(), is_delete=True)
                        
                        details_container = ui.column().classes('w-full bg-gray-50 p-1 ml-8 hidden gap-0')
                        
                        def toggle_details(details=details_container, btn=expand_btn, state=toggle_state):
                            if state['expanded']:
                                details.classes(add='hidden')
                                btn.text = '▶'
                                state['expanded'] = False
                            else:
                                details.classes(remove='hidden')
                                btn.text = '▼'
                                state['expanded'] = True
                        
                        expand_btn.on_click(toggle_details)
                        
                        with details_container:
                            ui.label(f'Coefficient: {current_devis.coefficient_marge:.2f}').classes('text-xs font-semibold text-gray-700 m-0')
                            ui.label(f'TVA: {current_devis.tva}%').classes('text-xs text-gray-600 m-0')
                            if current_devis.notes:
                                ui.label(f'Notes: {current_devis.notes}').classes('text-xs text-gray-600 italic m-0')
                            if current_devis.conditions:
                                ui.label(f'Conditions: {current_devis.conditions}').classes('text-xs text-gray-600 italic m-0')
        
        # Afficher le tableau une première fois
        display_table()
        
        # Stocker pour les rafraîchissements
        app_instance.display_table_callback = display_table


def create_dashboard_panel(app_instance):
    """Crée le panneau du dashboard
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-width: 1200px;'):
        ui.label('Tableau de bord').classes('text-3xl font-bold text-gray-900 mb-8')
        
        # Statistiques principales
        with ui.row().classes('w-full gap-6 mb-8'):
            # Total Devis
            with ui.card().classes('flex-1 shadow-none border').style('padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'):
                ui.label(f'{len(app_instance.dm.devis_list)}').classes('text-4xl font-bold text-white mb-2')
                ui.label('Devis').classes('text-lg text-white opacity-90')
            
            # Total Clients
            with ui.card().classes('flex-1 shadow-none border').style('padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'):
                ui.label(f'{len(app_instance.dm.clients)}').classes('text-4xl font-bold text-white mb-2')
                ui.label('Clients').classes('text-lg text-white opacity-90')
            
            # Total Articles
            with ui.card().classes('flex-1 shadow-none border').style('padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'):
                ui.label(f'{len(app_instance.dm.articles)}').classes('text-4xl font-bold text-white mb-2')
                ui.label('Articles').classes('text-lg text-white opacity-90')
            
            # Total Ouvrages
            with ui.card().classes('flex-1 shadow-none border').style('padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'):
                ui.label(f'{len(app_instance.dm.ouvrages)}').classes('text-4xl font-bold text-white mb-2')
                ui.label('Ouvrages').classes('text-lg text-white opacity-90')
        
        # Montant total des devis
        total_devis_amount = sum(d.total_ttc for d in app_instance.dm.devis_list)
        with ui.card().classes('w-full shadow-none border').style('padding: 20px; background: #f8f9fa;'):
            ui.label('Montant total des devis').classes('font-semibold text-lg text-gray-700 mb-2')
            ui.label(f'{total_devis_amount:,.2f} EUR').classes('text-3xl font-bold themed-accent')
        
        # Graphique: Total HT par statut
        with ui.card().classes('w-full shadow-none border').style('padding: 20px;'):
            ui.label('Total HT par statut').classes('font-semibold text-lg text-gray-700 mb-4')
            
            # Calculer les totaux par statut
            statut_totaux = {}
            for devis in app_instance.dm.devis_list:
                statut = getattr(devis, 'statut', 'en cours')
                if statut not in statut_totaux:
                    statut_totaux[statut] = 0
                statut_totaux[statut] += devis.total_ht
            
            # Si aucune donnée, afficher un message
            if not statut_totaux:
                ui.label('Aucun devis disponible').classes('text-gray-500 text-center py-4')
            else:
                # Créer le graphique avec plotly
                try:
                    import plotly.graph_objects as go
                    
                    statuts = list(statut_totaux.keys())
                    totaux = list(statut_totaux.values())
                    
                    # Couleurs pour chaque statut
                    colors = {
                        'en cours': '#667eea',
                        'envoyé': '#f093fb',
                        'refusé': '#f5576c',
                        'accepté': '#43e97b'
                    }
                    
                    fig = go.Figure(data=[
                        go.Bar(x=statuts, y=totaux, marker_color=[colors.get(s, '#667eea') for s in statuts])
                    ])
                    
                    fig.update_layout(
                        title='',
                        xaxis_title='Statut',
                        yaxis_title='Total HT (EUR)',
                        height=400,
                        showlegend=False,
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    
                    ui.plotly(fig).classes('w-full')
                except ImportError:
                    ui.label('Plotly non installé').classes('text-gray-500 text-center py-4')


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
                                ],
                                on_save=save_organisation
                            )
                            edit_dialog.open()
                        
                        ui.button('Modifier', on_click=on_modify_click).props('color=primary')
        
        # Afficher les données
        display_organisation()
