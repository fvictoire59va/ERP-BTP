"""
Panel de gestion des devis

Contient tous les composants pour créer, éditer et gérer les devis.
"""

from nicegui import ui
from datetime import datetime
from pathlib import Path

from erp.core.models import LigneDevis, Devis
from erp.ui.utils import notify_success, notify_error, notify_warning, notify_info
from erp.services.pdf_service import generate_pdf as generate_pdf_file


def create_devis_panel(app_instance):
    """Crée le panneau de gestion des devis
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Vérifier s'il y a un devis à charger depuis la navigation
    devis_to_load = getattr(app_instance, 'devis_to_load', None)
    
    # Nettoyer immédiatement pour éviter les doubles chargements
    if devis_to_load:
        app_instance.devis_to_load = None
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        # Titre et bouton Nouveau en haut
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label('Devis').classes('text-3xl font-bold text-gray-900')
            
            def new_devis():
                app_instance.current_devis_lignes = []
                app_instance.current_devis_coefficient = 1.35
                app_instance.selected_client_id = None
                numero_devis.value = get_next_unique_devis_number()
                date_devis.value = datetime.now().strftime('%Y-%m-%d')
                client_select.value = app_instance.dm.clients[0].id if app_instance.dm.clients else None
                refresh_table()
                notify_success('Nouveau devis créé')
            
            app_instance.create_themed_button('+ Ajouter un devis', on_click=new_devis).props('color=positive')
        
        # Fonction helper pour générer un numéro unique
        def get_next_unique_devis_number():
            next_num = app_instance.dm.get_next_devis_number()
            # Vérifier que ce numéro n'existe pas déjà, sinon incrémenter
            while any(d.numero == next_num for d in app_instance.dm.devis_list):
                # Extraire le numéro et l'incrémenter
                parts = next_num.rsplit('-', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    next_num = f"{parts[0]}-{int(parts[1]) + 1:04d}"
                else:
                    break
            return next_num
        
        # Section Informations generales - créer les champs EN PREMIER
        with ui.row().classes('w-full gap-6'):
            with ui.card().classes('flex-1 shadow-none border').style('padding: 16px;'):
                ui.label('Informations generales').classes('font-semibold text-lg text-gray-800 mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    # Si un devis doit être chargé, ne pas initialiser avec un nouveau numéro
                    initial_numero = devis_to_load if devis_to_load else get_next_unique_devis_number()
                    numero_devis = ui.input('Numero de devis', 
                                          value=initial_numero).props('readonly borderless').classes('w-40 numero-input').style('box-shadow: none !important;')
                    app_instance.numero_devis_field = numero_devis
                    
                    # Initialiser selected_client_id - utiliser le client du devis si chargement
                    if devis_to_load:
                        devis_obj_temp = app_instance.dm.get_devis_by_numero(devis_to_load)
                        initial_client_id = devis_obj_temp.client_id if devis_obj_temp else (app_instance.dm.clients[0].id if app_instance.dm.clients else None)
                    else:
                        # Pour un nouveau devis, utiliser selected_client_id existant ou le premier client
                        if not hasattr(app_instance, 'selected_client_id') or app_instance.selected_client_id is None:
                            initial_client_id = app_instance.dm.clients[0].id if app_instance.dm.clients else None
                        else:
                            initial_client_id = app_instance.selected_client_id
                    
                    app_instance.selected_client_id = initial_client_id
                    
                    client_select = ui.select(
                        label='Client',
                        options={c.id: f"{c.nom} {c.prenom} - {c.entreprise}" 
                                for c in app_instance.dm.clients},
                        value=initial_client_id
                    ).classes('flex-1')
                    
                    app_instance.client_select = client_select
                    
                    # Mettre à jour selected_client_id quand le client change
                    def on_client_change(e):
                        app_instance.selected_client_id = e.value
                    client_select.on_value_change(on_client_change)
                    
                    # Initialiser la date - utiliser la date du devis si chargement, sinon date du jour
                    if devis_to_load:
                        devis_obj_temp = app_instance.dm.get_devis_by_numero(devis_to_load)
                        initial_date = devis_obj_temp.date if devis_obj_temp else datetime.now().strftime('%Y-%m-%d')
                    else:
                        initial_date = datetime.now().strftime('%Y-%m-%d')
                    
                    date_devis = ui.input('Date', 
                                        value=initial_date).props('type=date').classes('w-40 date-input')
                    app_instance.date_devis_field = date_devis

        # Section Lignes du devis
        with ui.card().classes('w-full mt-6').style('min-width: 100%; display: block;'):
            ui.label('Lignes').classes('font-bold text-xl mb-4')
            
            # Controles pour ajouter des lignes (EN PREMIER, avant le tableau)
            with ui.row().classes('w-full gap-2 items-end mb-4'):
                type_select = ui.select(
                    label='Type',
                    options={'chapitre': 'Chapitre', 'texte': 'Texte', 'ouvrage': 'Ouvrage'},
                    value='ouvrage'
                ).classes('w-32')
                
                chapitre_input = ui.input('Titre chapitre').classes('flex-1')
                texte_input = ui.textarea('Texte').classes('flex-1').props('rows=1')
                ouvrage_select = ui.select(
                    label='Ouvrage',
                    options={o.id: f"{o.reference} - {o.designation}" for o in app_instance.dm.ouvrages}
                ).classes('flex-1')
                quantite_input = ui.number('Quantite', value=1, min=0.01, step=0.5).classes('w-24')
                
                def update_inputs():
                    chapitre_input.visible = type_select.value == 'chapitre'
                    texte_input.visible = type_select.value == 'texte'
                    ouvrage_select.visible = type_select.value == 'ouvrage'
                    quantite_input.visible = type_select.value == 'ouvrage'
                
                type_select.on_value_change(update_inputs)
                update_inputs()
                
                def add_ligne():
                    if type_select.value == 'chapitre' and chapitre_input.value:
                        ligne = LigneDevis(type='chapitre', id=app_instance.next_ligne_id, titre=chapitre_input.value)
                        app_instance.next_ligne_id += 1
                        app_instance.current_devis_lignes.append(ligne)
                        chapitre_input.value = ''
                        refresh_table()
                        notify_success('Chapitre ajoute')
                    elif type_select.value == 'texte' and texte_input.value:
                        ligne = LigneDevis(type='texte', id=app_instance.next_ligne_id, texte=texte_input.value)
                        app_instance.next_ligne_id += 1
                        app_instance.current_devis_lignes.append(ligne)
                        texte_input.value = ''
                        refresh_table()
                        notify_success('Texte ajoute')
                    elif type_select.value == 'ouvrage' and ouvrage_select.value and quantite_input.value:
                        app_instance.add_ligne_devis(ouvrage_select.value, quantite_input.value)
                        quantite_input.value = 1
                        refresh_table()
                        notify_success('Ouvrage ajoute')
                
                app_instance.create_themed_button('Ajouter', on_click=add_ligne)
            
            # Créer le conteneur du tableau (APRÈS les contrôles)
            with ui.column().classes('w-full'):
                lines_container = ui.column().classes('w-full').style('min-width: 100%; min-height: 100px;')
                
                # ===== DÉFINIR TOUTES LES FONCTIONS INTERNES EN PREMIER =====
                
                def refresh_table():
                    """Rafraîchit l'affichage du tableau des lignes"""
                    lines_container.clear()
                    
                    if not app_instance.current_devis_lignes:
                        with lines_container:
                            ui.label('Aucune ligne. Ajoutez-en une ci-dessus.').classes('text-gray-500 text-center py-8')
                        return
                    
                    with lines_container:
                        # Headers
                        with ui.row().classes('w-full gap-2 font-bold bg-gray-100 p-2 rounded'):
                            ui.label('Type').classes('w-20')
                            ui.label('Contenu').classes('flex-1')
                            ui.label('Qte').classes('w-16 text-right')
                            ui.label('P.U. HT').classes('w-20 text-right')
                            ui.label('Total HT').classes('w-24 text-right')
                            ui.label('Actions').classes('w-40')
                        
                        # Rows
                        for idx, ligne in enumerate(app_instance.current_devis_lignes):
                            with ui.column().classes('w-full border-b'):
                                toggle_state = {'expanded': False}
                                expand_btn = None
                                
                                with ui.row().classes('w-full gap-2 p-2 items-center'):
                                    if ligne.type == 'chapitre':
                                        ui.label('').classes('w-6')
                                        ui.label('Chapitre').classes('w-20 text-sm')
                                        ui.label(ligne.titre).classes('flex-1 font-semibold')
                                        ui.label('').classes('w-16')
                                        ui.label('').classes('w-20')
                                        ui.label('').classes('w-24')
                                    elif ligne.type == 'texte':
                                        ui.label('').classes('w-6')
                                        ui.label('Texte').classes('w-20 text-sm')
                                        ui.label(ligne.texte).classes('flex-1 italic text-gray-600')
                                        ui.label('').classes('w-16')
                                        ui.label('').classes('w-20')
                                        ui.label('').classes('w-24')
                                    else:  # ouvrage
                                        if ligne.composants:
                                            expand_btn = app_instance.material_icon_button('chevron_right', on_click=None)
                                            expand_btn.classes('w-6')
                                        else:
                                            expand_btn = None
                                            ui.label('').classes('w-6')
                                        ui.label('Ouvrage').classes('w-20 text-sm')
                                        ui.label(ligne.description if ligne.description else ligne.designation).classes('flex-1').style('white-space: pre-wrap;')
                                        ui.label(f"{ligne.quantite:.2f}").classes('w-16 text-right')
                                        ui.label(f"{ligne.prix_unitaire:.2f}").classes('w-20 text-right')
                                        ui.label(f"{ligne.prix_ht:.2f}").classes('w-24 text-right font-bold')
                                    
                                    # Boutons d'action
                                    with ui.row().classes('gap-2 items-center'):
                                        def edit_ligne(i=idx):
                                            show_edit_dialog(i)
                                        
                                        if idx > 0:
                                            app_instance.material_icon_button('arrow_upward', on_click=lambda i=idx: move_up(i))
                                        if idx < len(app_instance.current_devis_lignes) - 1:
                                            app_instance.material_icon_button('arrow_downward', on_click=lambda i=idx: move_down(i))
                                        app_instance.material_icon_button('edit', on_click=edit_ligne)
                                        app_instance.material_icon_button('delete', on_click=lambda i=idx: delete_ligne(i), is_delete=True)
                                
                                # Afficher les composants si c'est un ouvrage
                                if ligne.type == 'ouvrage' and hasattr(ligne, 'composants') and ligne.composants:
                                    composants_container = ui.column().classes('themed-card-header p-3 ml-6 mr-6 rounded hidden').style('width: calc(100% - 48px);')
                                    
                                    if expand_btn:
                                        def toggle_composants(details=composants_container, btn=expand_btn, state=toggle_state):
                                            if state['expanded']:
                                                details.classes(add='hidden')
                                                btn.props('icon=chevron_right')
                                                state['expanded'] = False
                                            else:
                                                details.classes(remove='hidden')
                                                btn.props('icon=expand_more')
                                                state['expanded'] = True
                                        
                                        expand_btn.on('click', toggle_composants)
                                    
                                    with composants_container:
                                        ui.label('Composants').classes('text-xs font-bold themed-accent mb-1')
                                        
                                        with ui.row().classes('w-full gap-1 text-xs font-semibold text-gray-600 mb-1'):
                                            ui.label('Article').classes('flex-1')
                                            ui.label('Qte').classes('w-20 text-right')
                                            ui.label('P.U.').classes('w-20 text-right')
                                            ui.label('Total').classes('w-20 text-right')
                                            ui.label('').classes('w-12')
                                        
                                        for comp_idx, comp in enumerate(ligne.composants):
                                            with ui.row().classes('w-full gap-1 text-xs items-center'):
                                                ui.label(f"{comp.designation} ({comp.unite})").classes('flex-1')
                                                
                                                qte_input = ui.number(value=comp.quantite, min=0.01, step=0.01).classes('w-20 text-right').props('dense borderless')
                                                pu_input = ui.number(value=comp.prix_unitaire, min=0, step=0.01).classes('w-20 text-right').props('dense borderless')
                                                total_label = ui.label(f"{comp.prix_total():.2f}").classes('w-20 text-right font-bold')
                                                
                                                def update_composant(c=comp, q=qte_input, p=pu_input, t=total_label, l=ligne):
                                                    c.quantite = q.value or 0
                                                    c.prix_unitaire = p.value or 0
                                                    t.text = f"{c.prix_total():.2f}"
                                                    # Recalculer le prix de l'ouvrage
                                                    l.prix_unitaire = sum(comp.prix_total() for comp in l.composants)
                                                    refresh_table()
                                                    app_instance.update_totals()
                                                
                                                qte_input.on('keydown.enter', lambda e, c=comp, q=qte_input, p=pu_input, t=total_label, l=ligne: update_composant(c, q, p, t, l))
                                                pu_input.on('keydown.enter', lambda e, c=comp, q=qte_input, p=pu_input, t=total_label, l=ligne: update_composant(c, q, p, t, l))
                                                
                                                # Mise à jour du total en temps réel sans refresh complet
                                                def update_display_only(q=qte_input, p=pu_input, t=total_label):
                                                    try:
                                                        qte_val = float(q.value or 0)
                                                        pu_val = float(p.value or 0)
                                                        t.text = f"{qte_val * pu_val:.2f}"
                                                    except:
                                                        pass
                                                
                                                qte_input.on_value_change(lambda e, q=qte_input, p=pu_input, t=total_label: update_display_only(q, p, t))
                                                pu_input.on_value_change(lambda e, q=qte_input, p=pu_input, t=total_label: update_display_only(q, p, t))
                                                
                                                def edit_comp(comp=comp, ligne=ligne, comp_idx=comp_idx):
                                                    with ui.dialog() as comp_dialog, ui.card().classes('w-full max-w-md'):
                                                        ui.label(f"Modifier le composant").classes('text-lg font-bold mb-4')
                                                        
                                                        designation_edit = ui.input('Désignation', value=comp.designation).classes('w-full')
                                                        unite_edit = ui.input('Unité', value=comp.unite).classes('w-full')
                                                        
                                                        with ui.row().classes('gap-2 mt-4 justify-end'):
                                                            def save_comp():
                                                                comp.designation = designation_edit.value
                                                                comp.unite = unite_edit.value
                                                                refresh_table()
                                                                comp_dialog.close()
                                                            
                                                            ui.button('Enregistrer', on_click=save_comp).classes('themed-button')
                                                            ui.button('Annuler', on_click=comp_dialog.close).props('flat')
                                                    
                                                    comp_dialog.open()
                                                
                                                app_instance.material_icon_button('edit', on_click=lambda c=comp, l=ligne, ci=comp_idx: edit_comp(c, l, ci)).props('size=xs')
                
                def show_edit_dialog(idx):
                    """Affiche la dialog d'édition pour une ligne"""
                    ligne = app_instance.current_devis_lignes[idx]
                    
                    with ui.dialog() as dialog:
                        with ui.card().classes('w-full max-w-2xl'):
                            if ligne.type == 'chapitre':
                                ui.label(ligne.titre[:50]).classes('text-lg font-bold mb-6')
                                titre = ui.input('Titre', value=ligne.titre).classes('w-full')
                                
                                with ui.row().classes('gap-2 mt-6 justify-end'):
                                    def save():
                                        ligne.titre = titre.value
                                        refresh_table()
                                        app_instance.update_totals()
                                        dialog.close()
                                    
                                    ui.button('Enregistrer', on_click=save).classes('themed-button')
                                    ui.button('Annuler', on_click=dialog.close).props('flat')
                            
                            elif ligne.type == 'texte':
                                ui.label(ligne.texte[:50]).classes('text-lg font-bold mb-6')
                                texte = ui.textarea('Texte', value=ligne.texte).classes('w-full').props('rows=3')
                                
                                with ui.row().classes('gap-2 mt-6 justify-end'):
                                    def save():
                                        ligne.texte = texte.value
                                        refresh_table()
                                        app_instance.update_totals()
                                        dialog.close()
                                    
                                    ui.button('Enregistrer', on_click=save).classes('themed-button')
                                    ui.button('Annuler', on_click=dialog.close).props('flat')
                            
                            else:  # ouvrage
                                ui.label(f"Modifier l'ouvrage : {ligne.designation}").classes('text-lg font-bold mb-6')
                                
                                with ui.column().classes('w-full gap-4'):
                                    designation = ui.input('Désignation', value=ligne.designation).classes('w-full')
                                    description = ui.textarea('Description', value=ligne.description).classes('w-full').props('rows=3')
                                    quantite = ui.number('Quantité', value=ligne.quantite, min=0.01, step=0.01).classes('w-full')
                                    prix_unitaire = ui.number('Prix unitaire (€)', value=ligne.prix_unitaire, min=0, step=0.01).classes('w-full')
                                    total_label = ui.label(f"Total HT : {ligne.quantite * ligne.prix_unitaire:.2f} €").classes('text-lg font-semibold mt-2')
                                    
                                    # Mise à jour du total en temps réel
                                    def update_total():
                                        try:
                                            qte = float(quantite.value or 0)
                                            pu = float(prix_unitaire.value or 0)
                                            total_label.text = f"Total HT : {qte * pu:.2f} €"
                                        except:
                                            total_label.text = "Total HT : 0.00 €"
                                    
                                    quantite.on_value_change(lambda: update_total())
                                    prix_unitaire.on_value_change(lambda: update_total())
                                
                                with ui.row().classes('gap-2 mt-6 justify-end'):
                                    def save():
                                        ligne.designation = designation.value
                                        ligne.description = description.value
                                        ligne.quantite = quantite.value
                                        ligne.prix_unitaire = prix_unitaire.value
                                        refresh_table()
                                        app_instance.update_totals()
                                        dialog.close()
                                    
                                    ui.button('Enregistrer', on_click=save).classes('themed-button')
                                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    
                    dialog.open()
                
                def move_up(idx):
                    if idx > 0:
                        app_instance.current_devis_lignes[idx], app_instance.current_devis_lignes[idx-1] = \
                            app_instance.current_devis_lignes[idx-1], app_instance.current_devis_lignes[idx]
                        refresh_table()
                        app_instance.update_totals()
                
                def move_down(idx):
                    if idx < len(app_instance.current_devis_lignes) - 1:
                        app_instance.current_devis_lignes[idx], app_instance.current_devis_lignes[idx+1] = \
                            app_instance.current_devis_lignes[idx+1], app_instance.current_devis_lignes[idx]
                        refresh_table()
                        app_instance.update_totals()
                
                def delete_ligne(idx):
                    app_instance.current_devis_lignes.pop(idx)
                    refresh_table()
                    app_instance.update_totals()
                
                # Appeler refresh_table pour afficher le tableau initial
                refresh_table()
        
        # Stocker pour l'utiliser lors du chargement d'un devis
        app_instance.refresh_devis_table = refresh_table
        
        # Section Informations generales
        with ui.row().classes('w-full mt-6 gap-6'):
            with ui.card().classes('flex-1 shadow-sm').style('padding: 24px;'):
                ui.label('Récapitulatif').classes('text-xl font-bold text-gray-900 mb-4')
                
                with ui.column().classes('w-full gap-3'):
                    with ui.row().classes('w-full justify-end items-center gap-4'):
                        ui.label('Total HT').classes('text-base font-medium text-gray-700')
                        app_instance.total_ht_label = ui.label('0.00 EUR').classes('text-lg font-bold text-gray-900 w-28 text-right')
                    
                    with ui.row().classes('w-full justify-end items-center gap-4'):
                        ui.label('TVA').classes('text-base font-medium text-gray-700')
                        app_instance.tva_rate_field = ui.number(value=20, min=0, max=100).classes('tva-input').style('width: 80px !important;')
                        ui.label('%').classes('text-base font-medium text-gray-700')
                        app_instance.total_tva_label = ui.label('0.00 EUR').classes('text-lg font-bold text-gray-900 w-28 text-right')
                    
                    with ui.row().classes('w-full justify-end items-center gap-4'):
                        ui.label('Total TTC').classes('text-lg font-bold text-gray-900')
                        app_instance.total_ttc_label = ui.label('0.00 EUR').classes('text-lg font-bold text-gray-900 w-28 text-right')
        
        # Boutons d'action Enregistrer et Générer PDF
        with ui.row().classes('w-full gap-3 mt-8'):
            def save_devis():
                try:
                    if not app_instance.current_devis_lignes:
                        notify_warning('Veuillez ajouter au moins une ligne')
                        return
                    if not app_instance.selected_client_id:
                        notify_warning('Veuillez sélectionner un client')
                        return
                    
                    numero = numero_devis.value
                    existing_devis = next((d for d in app_instance.dm.devis_list if d.numero == numero), None)
                    
                    if existing_devis:
                        existing_devis.date = date_devis.value
                        existing_devis.client_id = app_instance.selected_client_id
                        existing_devis.lignes = app_instance.current_devis_lignes
                        existing_devis.coefficient_marge = app_instance.current_devis_coefficient
                        existing_devis.tva = app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                        
                        app_instance.dm.save_data()
                        notify_success(f'Devis {numero} mis à jour')
                    else:
                        devis = Devis(
                            numero=numero,
                            date=date_devis.value,
                            client_id=app_instance.selected_client_id,
                            lignes=app_instance.current_devis_lignes,
                            coefficient_marge=app_instance.current_devis_coefficient,
                            tva=app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                        )
                        
                        app_instance.dm.devis_list.append(devis)
                        app_instance.dm.save_data()
                        notify_success(f'Devis {numero} créé')
                    
                    # Rafraîchir la liste des devis si callback disponible
                    if hasattr(app_instance, 'display_table_callback'):
                        app_instance.display_table_callback()
                    
                except Exception as e:
                    notify_error(f'Erreur: {str(e)}')
            
            def generate_pdf():
                try:
                    devis = Devis(
                        numero=numero_devis.value,
                        date=date_devis.value,
                        client_id=app_instance.selected_client_id,
                        lignes=app_instance.current_devis_lignes,
                        coefficient_marge=app_instance.current_devis_coefficient,
                        tva=app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                    )
                    
                    client = app_instance.dm.get_client_by_id(app_instance.selected_client_id)
                    client_name = f"{client.prenom}_{client.nom}" if client else "Client_inconnu"
                    client_name = client_name.replace(" ", "_")
                    
                    pdf_dir = app_instance.dm.data_dir / 'pdf' / client_name
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    pdf_path = pdf_dir / f"{devis.numero}.pdf"
                    
                    generate_pdf_file(devis, app_instance.dm, pdf_path)
                    
                    notify_success(f'PDF généré: {pdf_path}')
                except Exception as e:
                    notify_error(f'Erreur: {str(e)}')
            
            # Charger le devis si demandé depuis la navigation
            if devis_to_load:
                devis_obj = app_instance.dm.get_devis_by_numero(devis_to_load)
                if devis_obj:
                    # Forcer la mise à jour de tous les champs
                    numero_devis.set_value(devis_to_load)
                    date_devis.set_value(devis_obj.date)
                    client_select.set_value(devis_obj.client_id)
                    app_instance.selected_client_id = devis_obj.client_id
                    if hasattr(app_instance, 'tva_rate_field') and app_instance.tva_rate_field:
                        app_instance.tva_rate_field.set_value(devis_obj.tva)
                    
                    if devis_obj.lignes:
                        app_instance.next_ligne_id = max(l.id for l in devis_obj.lignes) + 1
                    else:
                        app_instance.next_ligne_id = 0
                    
                    refresh_table()
                    app_instance.update_totals()
                    notify_success(f'Devis {devis_to_load} chargé pour modification')
            
            ui.button('Enregistrer', on_click=save_devis).classes('themed-button')
            app_instance.create_themed_button('Generer PDF', on_click=generate_pdf)
