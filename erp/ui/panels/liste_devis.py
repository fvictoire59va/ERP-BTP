"""
Panel de liste des devis
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error


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
                with ui.row().classes('w-full gap-2 font-bold bg-gray-100 px-2 py-2 rounded text-sm items-center'):
                    ui.label('').classes('w-8 text-center')
                    ui.label('Numéro').classes('w-36 font-semibold text-center')
                    ui.label('Date').classes('w-24 font-semibold text-center')
                    ui.label('Client').classes('flex-1 font-semibold')
                    ui.label('Statut').classes('w-32 font-semibold text-center')
                    ui.label('Total HT').classes('w-28 text-right font-semibold')
                    ui.label('Total TTC').classes('w-28 text-right font-semibold')
                    ui.label('Actions').classes('w-48 text-center font-semibold')
                
                # Rows
                for idx, devis in enumerate(app_instance.dm.devis_list):
                    # Créer une copie locale de devis pour éviter les problèmes de closure
                    current_devis = devis
                    client = app_instance.dm.get_client_by_id(current_devis.client_id)
                    client_name = f"{client.prenom} {client.nom}" if client else "Client inconnu"
                    
                    with ui.row().classes('w-full gap-2 px-2 py-2 items-center hover:bg-gray-50 text-sm border-b border-gray-200'):
                        # État du bouton toggle pour chaque devis
                        toggle_state = {'expanded': False}
                        details_container = None
                        expand_btn = None
                        
                        expand_btn = app_instance.material_icon_button('chevron_right', on_click=None)
                        expand_btn.classes('w-8')
                        ui.label(current_devis.numero).classes('w-36 font-medium themed-accent')
                        ui.label(current_devis.date).classes('w-24')
                        ui.label(client_name).classes('flex-1')
                        
                        # Selecteur de statut
                        statut_options = ['en cours', 'envoyé', 'refusé', 'accepté']
                        def make_statut_handler(devis_obj):
                            def on_statut_change(e):
                                devis_obj.statut = e.value
                                app_instance.dm.save_data()
                            return on_statut_change
                        
                        ui.select(options=statut_options, value=current_devis.statut, on_change=make_statut_handler(current_devis)).classes('w-32').props('dense borderless').style('text-align: center;')
                        
                        ui.label(f"{current_devis.total_ht:.2f} EUR").classes('w-28 text-right text-xs')
                        ui.label(f"{current_devis.total_ttc:.2f} EUR").classes('w-28 text-right font-bold text-xs')
                        
                        # Définir les handlers avant de les utiliser
                        def make_create_projet_handler(devis_obj):
                            def create_projet():
                                from erp.ui.panels.projets import create_projet_from_devis
                                create_projet_from_devis(devis_obj, app_instance, table_container)
                            return create_projet
                        
                        def make_modify_handler(devis_numero, devis_obj):
                                def modify_devis():
                                    # Marquer qu'on charge un devis existant (pas un nouveau)
                                    app_instance.devis_to_load = devis_obj
                                    app_instance.current_devis_numero = devis_numero
                                    app_instance.is_editing_existing_devis = True
                                    
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
                                        if hasattr(app_instance, 'numero_devis_field') and app_instance.numero_devis_field:
                                            app_instance.numero_devis_field.set_value(devis_numero)
                                        if hasattr(app_instance, 'date_devis_field') and app_instance.date_devis_field:
                                            app_instance.date_devis_field.set_value(devis_obj.date)
                                        if hasattr(app_instance, 'client_select') and app_instance.client_select:
                                            app_instance.client_select.set_value(devis_obj.client_id)
                                        if hasattr(app_instance, 'tva_rate_field') and app_instance.tva_rate_field:
                                            app_instance.tva_rate_field.set_value(devis_obj.tva)
                                        
                                        # Recalculer next_ligne_id basé sur les lignes existantes
                                        if devis_obj.lignes:
                                            app_instance.next_ligne_id = max(l.id for l in devis_obj.lignes) + 1
                                        else:
                                            app_instance.next_ligne_id = 0
                                        
                                        # Rafraîchir le tableau des lignes
                                        if hasattr(app_instance, 'refresh_devis_table') and app_instance.refresh_devis_table:
                                            app_instance.refresh_devis_table()
                                        app_instance.update_totals()
                                        notify_success(f'Devis {devis_numero} chargé pour modification')
                                    
                                    ui.timer(0.2, load_devis_data, once=True)
                                return modify_devis
                        
                        def make_pdf_handler(numero=current_devis.numero, client_id=current_devis.client_id, devis_obj=current_devis):
                                def generate_pdf_devis():
                                    try:
                                        from erp.services.pdf_service import generate_pdf as generate_pdf_file
                                        
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
                                    # Dialog de confirmation
                                    with ui.dialog() as confirm_dialog, ui.card():
                                        ui.label(f'Confirmer la suppression du devis {numero} ?').classes('text-lg font-semibold mb-4')
                                        ui.label('Cette action est irréversible.').classes('text-gray-600 mb-6')
                                        with ui.row().classes('gap-2 justify-end w-full'):
                                            ui.button('Annuler', on_click=confirm_dialog.close).props('flat')
                                            def confirm_delete():
                                                for d in app_instance.dm.devis_list[:]:
                                                    if d.numero == numero:
                                                        app_instance.dm.devis_list.remove(d)
                                                        app_instance.dm.save_data()
                                                        notify_success(f'Devis {numero} supprimé')
                                                        display_table()
                                                        break
                                                confirm_dialog.close()
                                            ui.button('Supprimer', on_click=confirm_delete).props('color=negative')
                                    confirm_dialog.open()
                                return delete_devis
                            
                        # Actions avec icônes (zone fixe pour alignement)
                        with ui.row().classes('gap-0 w-48 justify-center items-center'):
                            # Bouton Créer/Rattacher chantier (visible uniquement pour devis acceptés)
                            if current_devis.statut == 'accepté':
                                app_instance.material_icon_button(
                                    'engineering',
                                    make_create_projet_handler(current_devis),
                                    is_delete=False
                                ).props('title="Créer un nouveau chantier ou rattacher à un chantier existant"')
                            app_instance.material_icon_button('edit', on_click=make_modify_handler(current_devis.numero, current_devis))
                            app_instance.material_icon_button('picture_as_pdf', on_click=make_pdf_handler())
                            app_instance.material_icon_button('delete', on_click=make_delete_handler(), is_delete=True)
                        
                        details_container = ui.column().classes('w-full bg-gray-50 p-1 ml-8 hidden gap-0')
                        
                        def toggle_details(details=details_container, btn=expand_btn, state=toggle_state):
                            if state['expanded']:
                                details.classes(add='hidden')
                                btn.props('icon=chevron_right')
                                state['expanded'] = False
                            else:
                                details.classes(remove='hidden')
                                btn.props('icon=expand_more')
                                state['expanded'] = True
                        
                        expand_btn.on('click', toggle_details)
                        
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
