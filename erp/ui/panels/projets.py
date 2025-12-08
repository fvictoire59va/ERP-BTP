"""
Panel pour gérer les Chantiers (projets) avec suivi prévisionnel vs réel.
Un chantier peut être rattaché à un ou plusieurs devis.
"""
from datetime import datetime
from nicegui import ui
from erp.core.data_manager import DataManager
from erp.core.models import Projet, DepenseReelle
from erp.ui.utils import notify_success, notify_error, notify_warning


def create_projet_from_devis(devis, app_instance, container):
    """Crée un nouveau chantier à partir d'un devis accepté ou rattache à un chantier existant"""
    dm = DataManager()
    
    # Vérifier si le devis est accepté
    if devis.statut != "accepté":
        notify_warning("Seuls les devis acceptés peuvent être convertis en chantiers")
        return
    
    # Récupérer le client
    client = dm.get_client_by_id(devis.client_id)
    if not client:
        notify_error("Client introuvable")
        return
    
    adresse_chantier = f"{client.adresse}\n{client.cp} {client.ville}"
    
    # Chercher un chantier existant pour ce client et cette adresse
    chantiers_existants = [
        p for p in dm.projets 
        if p.client_id == devis.client_id 
        and p.adresse_chantier == adresse_chantier
        and p.statut in ['en attente', 'en cours']
    ]
    
    if chantiers_existants:
        # Afficher un dialogue pour choisir
        show_attach_devis_dialog(devis, chantiers_existants, app_instance, container)
    else:
        # Créer un nouveau chantier
        _create_new_projet(devis, app_instance, container)


def show_attach_devis_dialog(devis, chantiers_existants, app_instance, container):
    """Dialogue pour choisir entre rattacher à un chantier existant ou créer un nouveau"""
    dm = DataManager()
    
    with ui.dialog() as dialog, ui.card().classes('w-[600px]'):
        ui.label(f'Chantier pour le devis {devis.numero}').classes('text-lg font-bold mb-4')
        ui.label('Des chantiers existent déjà pour ce client à cette adresse.').classes('text-sm mb-4')
        
        with ui.column().classes('w-full gap-4'):
            ui.label('Choisissez une option:').classes('font-semibold')
            
            # Option 1: Rattacher à un chantier existant
            for chantier in chantiers_existants:
                with ui.card().classes('w-full p-4 cursor-pointer hover:bg-gray-50'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.column():
                            ui.label(f'Chantier {chantier.numero}').classes('font-semibold')
                            ui.label(f'Devis rattachés: {", ".join(chantier.devis_numeros)}').classes('text-sm text-gray-600')
                        ui.button('Rattacher', on_click=lambda c=chantier: attach_to_existing(devis, c, dialog, app_instance, container)).props('flat color=primary')
            
            ui.separator()
            
            # Option 2: Créer un nouveau chantier
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Créer un nouveau chantier', 
                         on_click=lambda: create_new_from_dialog(devis, dialog, app_instance, container)
                ).props('color=primary')
                ui.button('Annuler', on_click=dialog.close).props('flat')
    
    dialog.open()


def attach_to_existing(devis, chantier, dialog, app_instance, container):
    """Rattache un devis à un chantier existant"""
    dm = DataManager()
    
    # Vérifier que le devis n'est pas déjà rattaché
    if devis.numero in chantier.devis_numeros:
        notify_warning(f"Le devis {devis.numero} est déjà rattaché à ce chantier")
        dialog.close()
        return
    
    chantier.devis_numeros.append(devis.numero)
    dm.save_data()
    
    notify_success(f"Devis {devis.numero} rattaché au chantier {chantier.numero}")
    dialog.close()
    
    # Rafraîchir l'affichage
    if container:
        container.clear()
        with container:
            render_projets_panel(app_instance)


def create_new_from_dialog(devis, dialog, app_instance, container):
    """Crée un nouveau chantier depuis le dialogue"""
    dialog.close()
    _create_new_projet(devis, app_instance, container)


def _create_new_projet(devis, app_instance, container):
    """Crée un nouveau chantier (fonction interne)"""
    dm = DataManager()
    
    # Récupérer le client
    client = dm.get_client_by_id(devis.client_id)
    if not client:
        notify_error("Client introuvable")
        return
    
    # Créer le projet
    projet_id = max((p.id for p in dm.projets), default=0) + 1
    date_creation = datetime.now().strftime("%Y-%m-%d")
    
    projet = Projet(
        id=projet_id,
        numero=dm.get_next_projet_number(),
        devis_numeros=[devis.numero],  # Liste avec un seul devis initialement
        client_id=devis.client_id,
        date_creation=date_creation,
        adresse_chantier=f"{client.adresse}\n{client.cp} {client.ville}",
        statut="en attente",
        depenses_reelles=[]
    )
    
    dm.projets.append(projet)
    dm.save_data()
    
    notify_success(f"Chantier {projet.numero} créé avec succès")
    
    # Rafraîchir l'affichage
    if container:
        container.clear()
        with container:
            render_projets_panel(app_instance)


def render_projets_panel(app_instance):
    """Affiche le panel de gestion des chantiers"""
    dm = DataManager()
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px;'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Gestion des Chantiers').classes('text-2xl font-bold')
            
            # Bouton pour actualiser
            app_instance.material_icon_button(
                'refresh',
                lambda: refresh_projets_list(app_instance, projets_container),
                is_delete=False
            )
        
        # Container pour la liste des chantiers
        projets_container = ui.column().classes('w-full gap-2')
        
        # Afficher les chantiers
        with projets_container:
            if not dm.projets:
                ui.label('Aucun chantier pour le moment').classes('text-gray-500 italic')
                ui.label('Les chantiers sont créés à partir des devis acceptés').classes('text-sm text-gray-400')
            else:
                render_projets_list(dm.projets, app_instance, projets_container)


def render_projets_list(projets, app_instance, container):
    """Affiche les chantiers dans une vue type Trello avec colonnes par statut"""
    dm = DataManager()
    
    # Colonnes de statut
    statuts = [
        {'key': 'en attente', 'label': 'En attente', 'icon': 'schedule', 'color': 'yellow'},
        {'key': 'en cours', 'label': 'En cours', 'icon': 'construction', 'color': 'blue'},
        {'key': 'terminé', 'label': 'Terminé', 'icon': 'check_circle', 'color': 'green'},
        {'key': 'annulé', 'label': 'Annulé', 'icon': 'cancel', 'color': 'red'}
    ]
    
    # Grouper les projets par statut
    projets_by_statut = {s['key']: [] for s in statuts}
    for projet in projets:
        if projet.statut in projets_by_statut:
            projets_by_statut[projet.statut].append(projet)
    
    # Dictionnaire global pour stocker les colonnes et gérer l'expansion
    columns_dict = {'columns': [], 'expanded_card': None}
    
    # Afficher les colonnes
    with ui.row().classes('w-full gap-4').style('align-items: stretch;'):
        for statut_info in statuts:
            statut_key = statut_info['key']
            projets_statut = sorted(
                projets_by_statut[statut_key],
                key=lambda p: p.date_creation,
                reverse=True
            )
            
            # Couleurs de colonne
            bg_colors = {
                'yellow': 'bg-yellow-50',
                'blue': 'bg-blue-50',
                'green': 'bg-green-50',
                'red': 'bg-red-50'
            }
            border_colors = {
                'yellow': 'border-yellow-200',
                'blue': 'border-blue-200',
                'green': 'border-green-200',
                'red': 'border-red-200'
            }
            
            # Colonne
            colonne = ui.column().classes(f'flex-1 {bg_colors[statut_info["color"]]} p-4 rounded-lg border-2 {border_colors[statut_info["color"]]}').style('min-width: 300px; min-height: 600px; transition: all 0.3s ease;')
            columns_dict['columns'].append(colonne)
            
            with colonne:
                # Header de la colonne
                with ui.row().classes('w-full items-center gap-2 mb-4'):
                    ui.icon(statut_info['icon']).classes('text-xl')
                    ui.label(statut_info['label']).classes('text-lg font-bold')
                    ui.label(f'({len(projets_statut)})').classes('text-sm text-gray-500')
                
                # Cards des chantiers
                for projet in projets_statut:
                    render_projet_card(projet, dm, app_instance, container, columns_dict)


def render_projet_card(projet, dm, app_instance, container, columns_dict):
    """Affiche une card individuelle de chantier dans le style Trello"""
    client = dm.get_client_by_id(projet.client_id)
    client_name = f"{client.prenom} {client.nom}" if client else "Client inconnu"
    
    # Calculer les données
    prev = projet.get_previsionnel(dm)
    reel = projet.get_reel()
    ecarts = projet.get_ecarts(dm)
    
    # Card avec hover effect
    card_element = ui.card().classes('w-full mb-3 cursor-pointer hover:shadow-lg transition-shadow').style('background: white; transition: all 0.3s ease;')
    
    with card_element:
        projet_details = {'expanded': False, 'expand_btn': None, 'details_container': None, 'card': card_element, 'columns_dict': columns_dict}
        
        with ui.column().classes('w-full gap-2 p-2'):
            # Header avec numéro et actions
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(projet.numero).classes('text-base font-bold')
                
                with ui.row().classes('gap-1'):
                    expand_btn = ui.icon('chevron_right').classes('text-gray-600 cursor-pointer text-lg').on('click',
                        lambda p=projet, d=projet_details: toggle_projet_details(p, d, app_instance, dm)
                    )
                    projet_details['expand_btn'] = expand_btn
                    
                    app_instance.material_icon_button(
                        'edit',
                        lambda p=projet: show_edit_projet_dialog(p, app_instance, container),
                        is_delete=False
                    ).props('size=sm flat dense')
                    
                    app_instance.material_icon_button(
                        'delete',
                        lambda p=projet: delete_projet(p, app_instance, container),
                        is_delete=True
                    ).props('size=sm flat dense')
            
            # Client
            with ui.row().classes('items-center gap-1'):
                ui.icon('person').classes('text-sm text-gray-500')
                ui.label(client_name).classes('text-sm text-gray-700')
            
            # Devis avec liens cliquables
            with ui.row().classes('items-center gap-1 flex-wrap'):
                ui.icon('description').classes('text-sm text-gray-500')
                for idx, devis_num in enumerate(projet.devis_numeros):
                    if idx > 0:
                        ui.label(',').classes('text-xs text-gray-600 mr-1')
                    
                    # Créer un bouton qui ressemble à un lien
                    def make_devis_button_handler(devis_numero):
                        def on_click_handler():
                            # Récupérer le devis
                            devis_obj = dm.get_devis_by_numero(devis_numero)
                            if not devis_obj:
                                notify_error(f"Devis {devis_numero} introuvable")
                                return
                            
                            # Copier les lignes du devis sélectionné
                            app_instance.current_devis_lignes = list(devis_obj.lignes) if devis_obj.lignes else []
                            app_instance.current_devis_coefficient = devis_obj.coefficient_marge
                            app_instance.selected_client_id = devis_obj.client_id
                            
                            # Stocker le numéro de devis pour le charger après la navigation
                            app_instance.devis_to_load = devis_numero
                            
                            # Naviguer vers la section devis avec le nouveau système de menu
                            if hasattr(app_instance, 'show_section_with_children'):
                                # Mettre à jour la section courante
                                app_instance.current_section['value'] = 'devis'
                                # Naviguer vers la section Devis avec son menu horizontal
                                # Le premier onglet (devis) sera automatiquement sélectionné
                                app_instance.show_section_with_children('devis', ['devis', 'liste'])
                                # Ne pas appeler notify_success ici car le contexte est supprimé après la navigation
                        return on_click_handler
                    
                    ui.button(devis_num, on_click=make_devis_button_handler(devis_num)).props('flat dense no-caps').classes('text-xs text-blue-600 hover:text-blue-800 underline cursor-pointer p-0 min-h-0').style('text-decoration: underline; font-weight: normal;')
            
            # Indicateurs financiers
            ui.separator()
            
            with ui.column().classes('w-full gap-1 text-xs'):
                with ui.row().classes('justify-between'):
                    ui.label('Prévu:').classes('text-gray-600')
                    ui.label(f"{prev['total_ht']:.2f} €").classes('font-semibold')
                
                with ui.row().classes('justify-between'):
                    ui.label('Réel:').classes('text-gray-600')
                    ui.label(f"{reel['total_ht']:.2f} €").classes('font-bold')
                
                with ui.row().classes('justify-between'):
                    ui.label('Écart:').classes('text-gray-600')
                    ecart_color = 'text-red-600' if ecarts['total_ht']['ecart'] > 0 else 'text-green-600'
                    ui.label(f"{ecarts['total_ht']['ecart']:+.2f} € ({ecarts['total_ht']['ecart_pct']:+.1f}%)").classes(f'font-bold {ecart_color}')
        
        # Container pour les détails (masqué par défaut)
        details_container = ui.column().classes('w-full mt-2 gap-2').style('display: none')
        projet_details['details_container'] = details_container
        
        with details_container:
            render_projet_details(projet, dm, app_instance, container)


def render_projet_details(projet, dm, app_instance, container):
    """Affiche les détails d'un chantier (prévisionnel vs réel)"""
    prev = projet.get_previsionnel(dm)
    reel = projet.get_reel()
    ecarts = projet.get_ecarts(dm)
    
    with ui.tabs().classes('w-full') as tabs:
        ui.tab('Synthèse', icon='dashboard')
        ui.tab('Matériaux', icon='inventory_2')
        ui.tab('Main d\'œuvre', icon='engineering')
        ui.tab('Infos', icon='info')
    
    with ui.tab_panels(tabs, value='Synthèse').classes('w-full'):
        # Onglet Synthèse
        with ui.tab_panel('Synthèse'):
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Matériaux
                with ui.card().classes('p-4'):
                    ui.label('Matériaux').classes('text-sm font-semibold text-gray-600')
                    prev_mat = ecarts['par_type']['materiaux']['prev']
                    reel_mat = ecarts['par_type']['materiaux']['reel']
                    ecart_mat = ecarts['par_type']['materiaux']['ecart']
                    ecart_pct_mat = ecarts['par_type']['materiaux']['ecart_pct']
                    ui.label(f"{prev_mat:.2f} €").classes('text-lg text-gray-500')
                    ui.label(f"{reel_mat:.2f} €").classes('text-2xl font-bold')
                    ecart_color = 'text-red-600' if ecart_mat > 0 else 'text-green-600'
                    ui.label(f"{ecart_mat:+.2f} € ({ecart_pct_mat:+.1f}%)").classes(f'text-sm {ecart_color}')
                
                # Main d'œuvre
                with ui.card().classes('p-4'):
                    ui.label('Main d\'œuvre').classes('text-sm font-semibold text-gray-600')
                    prev_mo = ecarts['par_type']['main_oeuvre']['prev']
                    reel_mo = ecarts['par_type']['main_oeuvre']['reel']
                    ecart_mo = ecarts['par_type']['main_oeuvre']['ecart']
                    ecart_pct_mo = ecarts['par_type']['main_oeuvre']['ecart_pct']
                    ui.label(f"{prev_mo:.2f} €").classes('text-lg text-gray-500')
                    ui.label(f"{reel_mo:.2f} €").classes('text-2xl font-bold')
                    ecart_color = 'text-red-600' if ecart_mo > 0 else 'text-green-600'
                    ui.label(f"{ecart_mo:+.2f} € ({ecart_pct_mo:+.1f}%)").classes(f'text-sm {ecart_color}')
                    
                    # Heures
                    ui.label(f"Heures: {prev['total_heures_mo']:.1f}h / {reel['total_heures_mo']:.1f}h").classes('text-xs text-gray-500 mt-2')
            
            # Ligne Total HT
            ui.separator().classes('my-4')
            with ui.card().classes('p-4'):
                ui.label('Total HT').classes('text-lg font-bold text-gray-700')
                with ui.row().classes('w-full justify-between items-center'):
                    with ui.column():
                        ui.label('Prévu').classes('text-sm text-gray-600')
                        ui.label(f"{prev['total_ht']:.2f} €").classes('text-xl text-gray-500')
                    with ui.column():
                        ui.label('Réel').classes('text-sm text-gray-600')
                        ui.label(f"{reel['total_ht']:.2f} €").classes('text-2xl font-bold')
                    with ui.column():
                        ui.label('Écart').classes('text-sm text-gray-600')
                        ecart_color = 'text-red-600' if ecarts['total_ht']['ecart'] > 0 else 'text-green-600'
                        ui.label(f"{ecarts['total_ht']['ecart']:+.2f} € ({ecarts['total_ht']['ecart_pct']:+.1f}%)").classes(f'text-xl font-bold {ecart_color}')
        
        # Onglets détaillés par type
        for type_key, type_label in [('materiaux', 'Matériaux'), ('main_oeuvre', 'Main d\'œuvre')]:
            with ui.tab_panel(type_label):
                render_comparison_table(prev[type_key], reel[type_key], type_label)
        
        # Onglet Infos
        with ui.tab_panel('Infos'):
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Colonne gauche
                with ui.column().classes('gap-2'):
                    ui.label('Informations générales').classes('font-semibold text-sm')
                    ui.label(f"Date de création: {projet.date_creation}").classes('text-sm')
                    if projet.date_debut:
                        ui.label(f"Date de début: {projet.date_debut}").classes('text-sm')
                    if projet.date_fin_prevue:
                        ui.label(f"Date de fin prévue: {projet.date_fin_prevue}").classes('text-sm')
                    if projet.date_fin_reelle:
                        ui.label(f"Date de fin réelle: {projet.date_fin_reelle}").classes('text-sm')
                    
                    ui.label('Adresse du chantier').classes('font-semibold text-sm mt-2')
                    ui.label(projet.adresse_chantier or "Non renseignée").classes('text-sm whitespace-pre-wrap')
                
                # Colonne droite
                with ui.column().classes('gap-2'):
                    if projet.notes:
                        ui.label('Notes').classes('font-semibold text-sm')
                        ui.label(projet.notes).classes('text-sm whitespace-pre-wrap')


def render_comparison_table(prev_items, reel_items, type_label):
    """Affiche un tableau comparatif prévisionnel vs réel"""
    if not prev_items and not reel_items:
        ui.label(f'Aucune donnée pour {type_label}').classes('text-gray-500 italic')
        return
    
    # Merger les items par designation
    merged = {}
    for item in prev_items:
        key = item['designation']
        merged[key] = {'prev': item, 'reel': None}
    
    for item in reel_items:
        key = item['designation']
        if key in merged:
            merged[key]['reel'] = item
        else:
            merged[key] = {'prev': None, 'reel': item}
    
    # Tableau
    with ui.column().classes('w-full gap-2'):
        # Headers
        with ui.row().classes('w-full gap-2 font-bold bg-gray-100 px-2 py-1 rounded text-sm'):
            ui.label('Désignation').classes('flex-1 font-semibold')
            ui.label('Prévu Qté').classes('w-24 text-right font-semibold')
            ui.label('Réel Qté').classes('w-24 text-right font-semibold')
            ui.label('Prévu €').classes('w-28 text-right font-semibold')
            ui.label('Réel €').classes('w-28 text-right font-semibold')
            ui.label('Écart €').classes('w-28 text-right font-semibold')
        
        # Rows
        for designation, data in sorted(merged.items()):
            prev_item = data['prev']
            reel_item = data['reel']
            
            prev_qte = prev_item['quantite'] if prev_item else 0
            reel_qte = reel_item['quantite'] if reel_item else 0
            prev_total = prev_item['prix_total'] if prev_item else 0
            reel_total = reel_item['prix_total'] if reel_item else 0
            ecart = reel_total - prev_total
            
            unite = (prev_item or reel_item)['unite']
            
            with ui.row().classes('w-full gap-2 px-2 py-1 items-center hover:bg-gray-50 text-sm border-b border-gray-200'):
                ui.label(designation).classes('flex-1')
                ui.label(f"{prev_qte:.2f} {unite}").classes('w-24 text-right text-gray-500')
                ui.label(f"{reel_qte:.2f} {unite}").classes('w-24 text-right font-semibold')
                ui.label(f"{prev_total:.2f} €").classes('w-28 text-right text-gray-500')
                ui.label(f"{reel_total:.2f} €").classes('w-28 text-right font-semibold')
                ecart_color = 'text-red-600' if ecart > 0 else 'text-green-600' if ecart < 0 else 'text-gray-600'
                ui.label(f"{ecart:+.2f} €").classes(f'w-28 text-right {ecart_color} font-semibold')


def render_depenses_list(projet, app_instance, container):
    """Affiche la liste des dépenses réelles"""
    if not projet.depenses_reelles:
        ui.label('Aucune dépense enregistrée').classes('text-gray-500 italic')
        return
    
    # Trier par date décroissante
    depenses_sorted = sorted(projet.depenses_reelles, key=lambda d: d.date, reverse=True)
    
    with ui.column().classes('w-full gap-2'):
        # Headers
        with ui.row().classes('w-full gap-2 font-bold bg-gray-100 px-2 py-1 rounded text-sm'):
            ui.label('Date').classes('w-24 font-semibold')
            ui.label('Type').classes('w-32 font-semibold')
            ui.label('Désignation').classes('flex-1 font-semibold')
            ui.label('Quantité').classes('w-24 text-right font-semibold')
            ui.label('PU').classes('w-24 text-right font-semibold')
            ui.label('Total').classes('w-28 text-right font-semibold')
            ui.label('Actions').classes('w-16 text-center')
        
        # Rows
        for depense in depenses_sorted:
            with ui.row().classes('w-full gap-2 px-2 py-1 items-center hover:bg-gray-50 text-sm border-b border-gray-200'):
                ui.label(depense.date).classes('w-24')
                
                type_colors = {
                    'materiau': 'bg-blue-100 text-blue-800',
                    'main_oeuvre': 'bg-green-100 text-green-800'
                }
                color_class = type_colors.get(depense.type_depense, 'bg-gray-100 text-gray-800')
                ui.label(depense.type_depense).classes(f'w-32 px-2 py-1 rounded text-xs {color_class}')
                
                ui.label(depense.designation).classes('flex-1')
                ui.label(f"{depense.quantite:.2f} {depense.unite}").classes('w-24 text-right')
                ui.label(f"{depense.prix_unitaire:.2f} €").classes('w-24 text-right')
                ui.label(f"{depense.prix_total:.2f} €").classes('w-28 text-right font-bold')
                
                with ui.row().classes('w-16 justify-center'):
                    app_instance.material_icon_button(
                        'delete',
                        lambda p=projet, d=depense: delete_depense(p, d, app_instance, container),
                        is_delete=True
                    )


def toggle_projet_details(projet, details_dict, app_instance, dm):
    """Toggle l'affichage des détails d'un chantier avec gestion des colonnes"""
    expanded = details_dict['expanded']
    btn = details_dict['expand_btn']
    container = details_dict['details_container']
    card = details_dict['card']
    columns_dict = details_dict['columns_dict']
    
    # Vérifier que le container existe
    if not container:
        return
    
    if expanded:
        # Collapse - restaurer toutes les colonnes
        btn.props('icon=chevron_right')
        container.style('display: none')
        card.style('background: white; transition: all 0.3s ease;')
        details_dict['expanded'] = False
        columns_dict['expanded_card'] = None
        
        # Restaurer toutes les colonnes à leur taille normale
        for col in columns_dict['columns']:
            col.style('min-width: 300px; flex: 1; transition: all 0.3s ease;')
    else:
        # Collapse toutes les autres cards si une est ouverte
        if columns_dict['expanded_card'] and columns_dict['expanded_card'] != details_dict:
            old_expanded = columns_dict['expanded_card']
            if old_expanded.get('expand_btn'):
                old_expanded['expand_btn'].props('icon=chevron_right')
            if old_expanded.get('details_container'):
                old_expanded['details_container'].style('display: none')
            if old_expanded.get('card'):
                old_expanded['card'].style('background: white; transition: all 0.3s ease;')
            old_expanded['expanded'] = False
        
        # Expand - rafraîchir les données
        container.clear()
        with container:
            render_projet_details(projet, dm, app_instance, None)
        btn.props('icon=expand_more')
        container.style('display: block')
        card.style('background: white; transition: all 0.3s ease;')
        details_dict['expanded'] = True
        columns_dict['expanded_card'] = details_dict
        
        # Réduire les autres colonnes et élargir celle qui contient la card active
        current_column = None
        for col in columns_dict['columns']:
            # Détecter si cette colonne contient la card active (vérifier si card est dans cette colonne)
            if card.parent_slot and card.parent_slot.parent == col:
                current_column = col
                break
        
        for col in columns_dict['columns']:
            if col == current_column:
                # Élargir la colonne active
                col.style('min-width: 900px; flex: 3; transition: all 0.3s ease;')
            else:
                # Réduire les autres colonnes
                col.style('min-width: 80px; max-width: 100px; flex: 0; transition: all 0.3s ease;')


def delete_depense(projet, depense, app_instance, container):
    """Supprime une dépense après confirmation"""
    def confirm_delete():
        dm = DataManager()
        projet_obj = dm.get_projet_by_id(projet.id)
        if projet_obj:
            projet_obj.depenses_reelles = [d for d in projet_obj.depenses_reelles if d.id != depense.id]
            dm.save_data()
            notify_success("Dépense supprimée")
            dialog.close()
            refresh_projets_list(app_instance, container)
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Confirmer la suppression de la dépense "{depense.designation}" ?').classes('text-lg')
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Annuler', on_click=dialog.close).props('flat')
            ui.button('Supprimer', on_click=confirm_delete).props('color=negative')
    
    dialog.open()


def show_edit_projet_dialog(projet, app_instance, container):
    """Affiche le dialogue d'édition d'un chantier"""
    dm = DataManager()
    
    with ui.dialog() as dialog, ui.card().classes('w-[600px]'):
        ui.label(f'Modifier le chantier {projet.numero}').classes('text-lg font-bold mb-4')
        
        with ui.column().classes('w-full gap-4'):
            # Devis rattachés
            with ui.column().classes('w-full gap-2'):
                ui.label('Devis rattachés').classes('font-semibold')
                
                # Liste des devis actuels
                devis_container = ui.column().classes('w-full gap-2')
                
                def refresh_devis_list():
                    devis_container.clear()
                    with devis_container:
                        if not projet.devis_numeros:
                            ui.label('Aucun devis rattaché').classes('text-sm text-gray-500 italic')
                        else:
                            for devis_num in projet.devis_numeros:
                                devis_obj = dm.get_devis_by_numero(devis_num)
                                if devis_obj:
                                    with ui.row().classes('w-full items-center justify-between p-2 bg-gray-50 rounded'):
                                        with ui.column().classes('gap-1'):
                                            ui.label(devis_num).classes('font-semibold')
                                            ui.label(f'{devis_obj.total_ht:.2f} € HT').classes('text-sm text-gray-600')
                                        
                                        app_instance.material_icon_button(
                                            'close',
                                            lambda dn=devis_num: remove_devis_from_projet(projet, dn, dm, dialog, app_instance, container),
                                            is_delete=True
                                        ).props('size=sm flat dense')
                
                refresh_devis_list()
                
                # Sélecteur pour ajouter un nouveau devis
                devis_acceptes = [d for d in dm.devis_list if d.statut == 'accepté' and d.numero not in projet.devis_numeros]
                
                if devis_acceptes:
                    with ui.row().classes('w-full gap-2 items-end'):
                        devis_options = {f"{d.numero} - {dm.get_client_by_id(d.client_id).nom if dm.get_client_by_id(d.client_id) else 'Client inconnu'} ({d.total_ht:.2f} €)": d.numero for d in devis_acceptes}
                        
                        devis_select = ui.select(
                            options=list(devis_options.keys()),
                            label='Ajouter un devis',
                            with_input=True
                        ).classes('flex-1')
                        
                        ui.button(
                            'Ajouter',
                            on_click=lambda: add_devis_to_projet(projet, devis_options.get(devis_select.value), dm, refresh_devis_list, app_instance, container)
                        ).props('color=primary icon=add')
                else:
                    ui.label('Aucun devis accepté disponible').classes('text-sm text-gray-500 italic')
            
            ui.separator()
            
            # Statut
            with ui.row().classes('w-full items-center gap-2'):
                statut_select = ui.select(
                    ['en attente', 'en cours', 'terminé', 'annulé'],
                    label='Statut',
                    value=projet.statut
                ).classes('flex-1')
                
                ui.icon('info').classes('text-gray-400 cursor-help').props('size=sm').tooltip(
                    'en attente: Chantier créé mais pas démarré\n'
                    'en cours: Travaux en cours de réalisation\n'
                    'terminé: Chantier achevé\n'
                    'annulé: Chantier annulé'
                )
            
            # Dates
            date_debut_input = ui.input(
                label='Date de début',
                value=projet.date_debut,
                placeholder='YYYY-MM-DD'
            ).classes('w-full')
            
            date_fin_prevue_input = ui.input(
                label='Date de fin prévue',
                value=projet.date_fin_prevue,
                placeholder='YYYY-MM-DD'
            ).classes('w-full')
            
            date_fin_reelle_input = ui.input(
                label='Date de fin réelle',
                value=projet.date_fin_reelle,
                placeholder='YYYY-MM-DD'
            ).classes('w-full')
            
            # Adresse
            adresse_input = ui.textarea(
                label='Adresse du chantier',
                value=projet.adresse_chantier
            ).classes('w-full')
            
            # Notes
            notes_input = ui.textarea(
                label='Notes',
                value=projet.notes
            ).classes('w-full')
            
            # Boutons
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                ui.button(
                    'Enregistrer',
                    on_click=lambda: save_projet_changes(
                        projet,
                        statut_select.value,
                        date_debut_input.value,
                        date_fin_prevue_input.value,
                        date_fin_reelle_input.value,
                        adresse_input.value,
                        notes_input.value,
                        dialog,
                        app_instance,
                        container
                    )
                ).props('color=primary')
    
    dialog.open()


def add_devis_to_projet(projet, devis_numero, dm, refresh_callback, app_instance, container):
    """Ajoute un devis au chantier"""
    if not devis_numero:
        notify_warning("Veuillez sélectionner un devis")
        return
    
    if devis_numero in projet.devis_numeros:
        notify_warning("Ce devis est déjà rattaché à ce chantier")
        return
    
    projet_obj = dm.get_projet_by_id(projet.id)
    if projet_obj:
        projet_obj.devis_numeros.append(devis_numero)
        dm.save_data()
        notify_success(f"Devis {devis_numero} ajouté au chantier")
        refresh_callback()
        refresh_projets_list(app_instance, container)


def remove_devis_from_projet(projet, devis_numero, dm, dialog, app_instance, container):
    """Retire un devis du chantier après confirmation"""
    def confirm_remove():
        projet_obj = dm.get_projet_by_id(projet.id)
        if projet_obj:
            if len(projet_obj.devis_numeros) <= 1:
                notify_error("Un chantier doit avoir au moins un devis rattaché")
                confirm_dialog.close()
                return
            
            projet_obj.devis_numeros = [d for d in projet_obj.devis_numeros if d != devis_numero]
            dm.save_data()
            notify_success(f"Devis {devis_numero} retiré du chantier")
            confirm_dialog.close()
            dialog.close()
            refresh_projets_list(app_instance, container)
    
    with ui.dialog() as confirm_dialog, ui.card():
        ui.label(f'Retirer le devis {devis_numero} du chantier ?').classes('text-lg')
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Annuler', on_click=confirm_dialog.close).props('flat')
            ui.button('Retirer', on_click=confirm_remove).props('color=negative')
    
    confirm_dialog.open()


def save_projet_changes(projet, statut, date_debut, date_fin_prevue, date_fin_reelle, adresse, notes, dialog, app_instance, container):
    """Enregistre les modifications d'un chantier"""
    dm = DataManager()
    
    # Trouver le projet dans la liste
    projet_obj = dm.get_projet_by_id(projet.id)
    if not projet_obj:
        notify_error("Chantier introuvable")
        dialog.close()
        return
    
    # Mettre à jour les champs
    projet_obj.statut = statut
    projet_obj.date_debut = date_debut
    projet_obj.date_fin_prevue = date_fin_prevue
    projet_obj.date_fin_reelle = date_fin_reelle
    projet_obj.adresse_chantier = adresse
    projet_obj.notes = notes
    
    dm.save_data()
    notify_success("Chantier mis à jour avec succès")
    dialog.close()
    
    # Rafraîchir l'affichage
    refresh_projets_list(app_instance, container)


def delete_projet(projet, app_instance, container):
    """Supprime un chantier après confirmation"""
    def confirm_delete():
        dm = DataManager()
        dm.projets = [p for p in dm.projets if p.id != projet.id]
        dm.save_data()
        notify_success(f"Chantier {projet.numero} supprimé")
        dialog.close()
        refresh_projets_list(app_instance, container)
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Confirmer la suppression du chantier {projet.numero} ?').classes('text-lg')
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Annuler', on_click=dialog.close).props('flat')
            ui.button('Supprimer', on_click=confirm_delete).props('color=negative')
    
    dialog.open()


def refresh_projets_list(app_instance, container):
    """Rafraîchit la liste des chantiers"""
    dm = DataManager()
    container.clear()
    with container:
        if not dm.projets:
            ui.label('Aucun chantier pour le moment').classes('text-gray-500 italic')
            ui.label('Les chantiers sont créés à partir des devis acceptés').classes('text-sm text-gray-400')
        else:
            render_projets_list(dm.projets, app_instance, container)
