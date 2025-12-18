"""
Panel de gestion des devis

Contient tous les composants pour créer, éditer et gérer les devis.
"""

from nicegui import ui
from datetime import datetime
from pathlib import Path
import json

from erp.core.models import LigneDevis, Devis
from erp.ui.utils import notify_success, notify_error, notify_warning, notify_info
from erp.services.pdf_service import generate_pdf as generate_pdf_file


def create_devis_panel(app_instance):
    """Crée le panneau de gestion des devis
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Vérifier s'il y a un devis à charger depuis la navigation
    # devis_to_load contient maintenant un objet Devis complet, pas un numéro
    devis_to_load = getattr(app_instance, 'devis_to_load', None)
    is_editing_existing = getattr(app_instance, 'is_editing_existing_devis', False)
    
    # Nettoyer immédiatement pour éviter les doubles chargements
    if devis_to_load:
        app_instance.devis_to_load = None
    if hasattr(app_instance, 'is_editing_existing_devis'):
        app_instance.is_editing_existing_devis = False
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; min-width: 1200px; width: 100%;'):
        # Titre et boutons d'action en haut
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label('Devis').classes('text-3xl font-bold text-gray-900')
            
            # Conteneur pour les boutons d'action (sera rempli après création des fonctions)
            action_buttons_row = ui.row().classes('gap-2')
        
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
                    # Si on édite un devis existant, utiliser son numéro, sinon générer un nouveau
                    if devis_to_load and hasattr(devis_to_load, 'numero'):
                        initial_numero = devis_to_load.numero
                    elif is_editing_existing and hasattr(app_instance, 'current_devis_numero'):
                        initial_numero = app_instance.current_devis_numero
                    else:
                        initial_numero = get_next_unique_devis_number()
                    
                    numero_devis = ui.input('Numero de devis', 
                                          value=initial_numero).props('readonly borderless').classes('w-40 numero-input').style('box-shadow: none !important;')
                    app_instance.numero_devis_field = numero_devis
                    
                    # Initialiser selected_client_id - utiliser le client du devis si chargement
                    if devis_to_load and hasattr(devis_to_load, 'client_id'):
                        initial_client_id = devis_to_load.client_id
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
                    if devis_to_load and hasattr(devis_to_load, 'date'):
                        initial_date = devis_to_load.date
                    else:
                        initial_date = datetime.now().strftime('%Y-%m-%d')
                    
                    date_devis = ui.input('Date', 
                                        value=initial_date).props('type=date').classes('w-40 date-input')
                    app_instance.date_devis_field = date_devis
                
                # Champ objet du devis
                with ui.row().classes('w-full mt-4'):
                    # Initialiser l'objet - utiliser l'objet du devis si chargement
                    if devis_to_load and hasattr(devis_to_load, 'objet'):
                        initial_objet = devis_to_load.objet
                    else:
                        initial_objet = ""
                    
                    objet_devis = ui.input('Objet', 
                                          value=initial_objet,
                                          placeholder='Description des travaux').classes('flex-1')
                    app_instance.objet_devis_field = objet_devis

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
                
                niveau_select = ui.select(
                    label='Niveau',
                    options={1: 'Niveau 1', 2: 'Niveau 2', 3: 'Niveau 3'},
                    value=1
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
                    # Masquer le sélecteur de niveau pour les ouvrages
                    niveau_select.visible = type_select.value != 'ouvrage'
                
                type_select.on_value_change(update_inputs)
                update_inputs()
                
                def add_ligne():
                    niveau = niveau_select.value
                    if type_select.value == 'chapitre' and chapitre_input.value:
                        ligne = LigneDevis(type='chapitre', id=app_instance.next_ligne_id, titre=chapitre_input.value, niveau=niveau)
                        app_instance.next_ligne_id += 1
                        app_instance.current_devis_lignes.append(ligne)
                        chapitre_input.value = ''
                        refresh_table()
                        notify_success('Chapitre ajoute')
                    elif type_select.value == 'texte' and texte_input.value:
                        ligne = LigneDevis(type='texte', id=app_instance.next_ligne_id, texte=texte_input.value, niveau=niveau)
                        app_instance.next_ligne_id += 1
                        app_instance.current_devis_lignes.append(ligne)
                        texte_input.value = ''
                        refresh_table()
                        notify_success('Texte ajoute')
                    elif type_select.value == 'ouvrage' and ouvrage_select.value and quantite_input.value:
                        # Trouver le niveau du dernier chapitre au-dessus
                        niveau_ouvrage = 1  # Niveau par défaut
                        for ligne_existante in reversed(app_instance.current_devis_lignes):
                            if ligne_existante.type == 'chapitre':
                                niveau_ouvrage = getattr(ligne_existante, 'niveau', 1)
                                break
                        
                        ouvrage = app_instance.dm.get_ouvrage_by_id(ouvrage_select.value)
                        if ouvrage:
                            ligne = LigneDevis(
                                type='ouvrage',
                                id=app_instance.next_ligne_id,
                                ouvrage_id=ouvrage.id,
                                designation=ouvrage.designation,
                                description=ouvrage.description,
                                quantite=quantite_input.value,
                                unite=ouvrage.unite,
                                prix_unitaire=ouvrage.calculate_prix_vente(),
                                composants=ouvrage.composants.copy(),
                                niveau=niveau_ouvrage
                            )
                            app_instance.next_ligne_id += 1
                            app_instance.current_devis_lignes.append(ligne)
                        quantite_input.value = 1
                        refresh_table()
                        notify_success('Ouvrage ajoute')
                
                app_instance.create_themed_button('Ajouter', on_click=add_ligne)
            
            # Créer le conteneur du tableau (APRÈS les contrôles)
            with ui.column().classes('w-full gap-0'):
                lines_container = ui.column().classes('w-full gap-0').style('min-width: 100%; min-height: 100px;')
                
                # ===== DÉFINIR TOUTES LES FONCTIONS INTERNES EN PREMIER =====
                
                def refresh_table():
                    """Rafraîchit l'affichage du tableau des lignes avec totaux par niveau"""
                    lines_container.clear()
                    
                    if not app_instance.current_devis_lignes:
                        with lines_container:
                            ui.label('Aucune ligne. Ajoutez-en une ci-dessus.').classes('text-gray-500 text-center py-8')
                        return
                    
                    with lines_container:
                        # Headers
                        with ui.row().classes('w-full font-bold bg-gray-100 px-1 rounded'):
                            ui.label('Niv').classes('w-12 px-2 border-r-2 border-gray-400')
                            ui.label('').classes('w-6')
                            ui.label('').classes('w-16 px-1 text-center border-r-2 border-gray-400')
                            ui.label('Contenu').classes('flex-1 px-2 border-r-2 border-gray-400')
                            ui.label('Qte').classes('w-24 px-2 text-right border-r-2 border-gray-400')
                            ui.label('P.U. HT').classes('w-32 px-2 text-right border-r-2 border-gray-400')
                            ui.label('Total HT').classes('w-32 px-2 text-right border-r-2 border-gray-400')
                            ui.label('Actions').classes('w-32 px-2')
                        
                        # Calculer les totaux hiérarchiques par section
                        def calculate_hierarchical_totals():
                            """Calcule les totaux cumulés pour chaque section de chapitre (incluant sous-chapitres)"""
                            section_totals = {}
                            chapter_stack = []  # Stack de (idx, niveau, total_cumule)
                            
                            for idx, ligne in enumerate(app_instance.current_devis_lignes):
                                niveau = getattr(ligne, 'niveau', 1)
                                
                                if ligne.type == 'chapitre':
                                    # Fermer tous les chapitres de niveau >= au niveau actuel
                                    while chapter_stack and chapter_stack[-1][1] >= niveau:
                                        closed_idx, closed_niveau, closed_total = chapter_stack.pop()
                                        section_totals[closed_idx] = (closed_niveau, closed_total)
                                    
                                    # Commencer un nouveau chapitre
                                    chapter_stack.append([idx, niveau, 0.0])
                                
                                elif ligne.type == 'ouvrage':
                                    # Ajouter le prix aux totaux de tous les chapitres ouverts
                                    for chapter_info in chapter_stack:
                                        chapter_info[2] += ligne.prix_ht
                            
                            # Fermer tous les chapitres restants
                            while chapter_stack:
                                closed_idx, closed_niveau, closed_total = chapter_stack.pop()
                                section_totals[closed_idx] = (closed_niveau, closed_total)
                            
                            return section_totals
                        
                        section_totals_map = calculate_hierarchical_totals()
                        
                        # Grouper les lignes par sections de chapitres avec calcul des totaux par section
                        sections = []  # Liste de (start_idx, end_idx, niveau, total_section)
                        current_section_start = None
                        current_section_niveau = None
                        
                        for idx, ligne in enumerate(app_instance.current_devis_lignes):
                            niveau = getattr(ligne, 'niveau', 1)
                            
                            if ligne.type == 'chapitre':
                                # Sauvegarder la section précédente
                                if current_section_start is not None:
                                    sections.append((current_section_start, idx - 1, current_section_niveau))
                                current_section_start = idx
                                current_section_niveau = niveau
                        
                        # Ajouter la dernière section
                        if current_section_start is not None:
                            sections.append((current_section_start, len(app_instance.current_devis_lignes) - 1, current_section_niveau))
                        
                        # Calculer le total de chaque section
                        section_totals = {}
                        for start_idx, end_idx, section_niveau in sections:
                            total = 0.0
                            for i in range(start_idx, end_idx + 1):
                                ligne = app_instance.current_devis_lignes[i]
                                if ligne.type == 'ouvrage':
                                    total += ligne.prix_ht
                            section_totals[(start_idx, section_niveau)] = total
                        
                        # Afficher les lignes et gérer l'affichage des totaux hiérarchiques
                        for idx, ligne in enumerate(app_instance.current_devis_lignes):
                            niveau = getattr(ligne, 'niveau', 1)
                            
                            # Vérifier si on doit afficher un total avant cette ligne
                            # (quand on rencontre un nouveau chapitre après une section)
                            if idx > 0 and ligne.type == 'chapitre':
                                # Trouver tous les chapitres qui doivent être fermés
                                chapters_to_close = []
                                for j in range(idx - 1, -1, -1):
                                    if app_instance.current_devis_lignes[j].type == 'chapitre':
                                        chapter_niveau = getattr(app_instance.current_devis_lignes[j], 'niveau', 1)
                                        # Fermer ce chapitre si son niveau >= niveau actuel
                                        if chapter_niveau >= niveau and j in section_totals_map:
                                            chapters_to_close.append((j, chapter_niveau, section_totals_map[j][1]))
                                        # Si on trouve un chapitre de niveau inférieur, on arrête
                                        if chapter_niveau < niveau:
                                            break
                                
                                # Afficher les sous-totaux du plus profond au plus haut
                                for chapter_idx, chapter_niveau, chapter_total in reversed(chapters_to_close):
                                    chapter_titre = app_instance.current_devis_lignes[chapter_idx].titre
                                    if chapter_niveau == 3:
                                        with ui.row().classes('w-full px-1 bg-purple-50 border-t-2 border-purple-300'):
                                            ui.label('').classes('w-12 px-2')
                                            ui.label('').classes('w-6')
                                            ui.label('').classes('w-16 px-1')
                                            ui.label(f'Sous-total - {chapter_titre}').classes('flex-1 px-2 font-bold text-purple-800')
                                            ui.label('').classes('w-24 px-2')
                                            ui.label('').classes('w-32 px-2')
                                            ui.label(f"{chapter_total:.2f} €").classes('w-32 px-2 text-right font-bold text-purple-800')
                                            ui.label('').classes('w-32 px-2')
                                    elif chapter_niveau == 2:
                                        with ui.row().classes('w-full px-1 bg-green-50 border-t-2 border-green-300'):
                                            ui.label('').classes('w-12 px-2')
                                            ui.label('').classes('w-6')
                                            ui.label('').classes('w-16 px-1')
                                            ui.label(f'Sous-total - {chapter_titre}').classes('flex-1 px-2 font-bold text-green-800')
                                            ui.label('').classes('w-24 px-2')
                                            ui.label('').classes('w-32 px-2')
                                            ui.label(f"{chapter_total:.2f} €").classes('w-32 px-2 text-right font-bold text-green-800')
                                            ui.label('').classes('w-32 px-2')
                            
                            with ui.column().classes('w-full'):
                                toggle_state = {'expanded': False}
                                expand_btn = None
                                
                                with ui.row().classes('w-full px-1 items-center hover:bg-gray-50 cursor-pointer transition-colors'):
                                    # Colonne niveau
                                    ui.label(f'{niveau}').classes('w-12 px-2 text-center font-semibold text-gray-600 border-r-2 border-gray-300')
                                    
                                    if ligne.type == 'chapitre':
                                        # Déterminer la taille de police selon le niveau (pour la colonne Contenu uniquement)
                                        if niveau == 1:
                                            text_size = 'text-lg'  # +2
                                        elif niveau == 2:
                                            text_size = 'text-base'  # +1
                                        else:  # niveau 3
                                            text_size = 'text-sm'  # standard
                                        
                                        with ui.column().classes('w-6'):
                                            ui.label('')
                                        with ui.row().classes('w-16 gap-0 items-center justify-center border-r-2 border-gray-300').style('flex-wrap: nowrap; min-height: 32px;'):
                                            if idx > 0:
                                                app_instance.material_icon_button('arrow_upward', on_click=lambda i=idx: move_up(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                            if idx < len(app_instance.current_devis_lignes) - 1:
                                                app_instance.material_icon_button('arrow_downward', on_click=lambda i=idx: move_down(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                        ui.label(ligne.titre).classes(f'flex-1 px-2 font-semibold {text_size} overflow-hidden text-ellipsis border-r-2 border-gray-300')
                                        ui.label('').classes('w-24 px-2 border-r-2 border-gray-300')
                                        ui.label('').classes('w-32 px-2 border-r-2 border-gray-300')
                                        ui.label('').classes('w-32 px-2 border-r-2 border-gray-300')
                                    elif ligne.type == 'texte':
                                        with ui.column().classes('w-6'):
                                            ui.label('')
                                        with ui.row().classes('w-16 gap-0 items-center justify-center border-r-2 border-gray-300').style('flex-wrap: nowrap; min-height: 32px;'):
                                            if idx > 0:
                                                app_instance.material_icon_button('arrow_upward', on_click=lambda i=idx: move_up(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                            if idx < len(app_instance.current_devis_lignes) - 1:
                                                app_instance.material_icon_button('arrow_downward', on_click=lambda i=idx: move_down(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                        ui.label(ligne.texte).classes('flex-1 px-2 italic text-gray-600 overflow-hidden text-ellipsis border-r-2 border-gray-300')
                                        ui.label('').classes('w-24 px-2 border-r-2 border-gray-300')
                                        ui.label('').classes('w-32 px-2 border-r-2 border-gray-300')
                                        ui.label('').classes('w-32 px-2 border-r-2 border-gray-300')
                                    else:  # ouvrage
                                        with ui.column().classes('w-6'):
                                            if ligne.composants:
                                                expand_btn = app_instance.material_icon_button('chevron_right', on_click=None)
                                            else:
                                                expand_btn = None
                                                ui.label('')
                                        with ui.row().classes('w-16 gap-0 items-center justify-center border-r-2 border-gray-300').style('flex-wrap: nowrap; min-height: 32px;'):
                                            if idx > 0:
                                                app_instance.material_icon_button('arrow_upward', on_click=lambda i=idx: move_up(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                            if idx < len(app_instance.current_devis_lignes) - 1:
                                                app_instance.material_icon_button('arrow_downward', on_click=lambda i=idx: move_down(i)).style('padding: 2px; min-width: 20px;').props('size=xs dense flat')
                                        ui.label(ligne.description if ligne.description else ligne.designation).classes('flex-1 px-2 overflow-hidden text-ellipsis border-r-2 border-gray-300')
                                        ui.label(f"{ligne.quantite:.2f}").classes('w-24 px-2 text-right overflow-hidden border-r-2 border-gray-300')
                                        ui.label(f"{ligne.prix_unitaire:.2f}").classes('w-32 px-2 text-right overflow-hidden border-r-2 border-gray-300')
                                        ui.label(f"{ligne.prix_ht:.2f}").classes('w-32 px-2 text-right font-bold overflow-hidden border-r-2 border-gray-300')
                                    
                                    # Boutons d'action
                                    with ui.row().classes('w-32 px-2 gap-1 items-center flex-nowrap'):
                                        def edit_ligne(i=idx):
                                            show_edit_dialog(i)
                                        
                                        app_instance.material_icon_button('content_copy', on_click=lambda i=idx: duplicate_ligne(i))
                                        app_instance.material_icon_button('edit', on_click=edit_ligne)
                                        app_instance.material_icon_button('delete', on_click=lambda i=idx: delete_ligne(i), is_delete=True)
                                
                                # Afficher les composants si c'est un ouvrage
                                if ligne.type == 'ouvrage' and hasattr(ligne, 'composants') and ligne.composants:
                                    composants_container = ui.column().classes('themed-card-header ml-6 mr-6 rounded hidden').style('width: calc(100% - 48px); padding: 4px 0 !important; gap: 0 !important;')
                                    
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
                                        with ui.row().classes('w-full text-xs font-semibold text-gray-600 bg-gray-100').style('padding: 2px 8px !important; gap: 4px; margin: 0 !important; min-height: 20px !important;'):
                                            ui.label('Composants').classes('flex-1').style('margin: 0; padding: 0; line-height: 1.2;')
                                            ui.label('Qte').classes('w-20 text-right').style('margin: 0; padding: 0; line-height: 1.2;')
                                            ui.label('P.U.').classes('w-20 text-right').style('margin: 0; padding: 0; line-height: 1.2;')
                                            ui.label('Total').classes('w-20 text-right').style('margin: 0; padding: 0; line-height: 1.2;')
                                            ui.label('').classes('w-12').style('margin: 0; padding: 0;')
                                        
                                        for comp_idx, comp in enumerate(ligne.composants):
                                            with ui.row().classes('w-full text-xs items-center hover:bg-gray-100 transition-colors').style('min-height: 18px !important; padding: 1px 8px !important; margin: 0 !important; gap: 4px;'):
                                                ui.label(f"{comp.designation} ({comp.unite})").classes('flex-1').style('line-height: 1.1; margin: 0; padding: 0; font-size: 11px;')
                                                
                                                qte_input = ui.input(value=f"{comp.quantite:.2f}").classes('w-20 text-right').props('dense borderless type=text inputmode=decimal')
                                                pu_input = ui.input(value=f"{comp.prix_unitaire:.2f}").classes('w-20 text-right').props('dense borderless type=text inputmode=decimal')
                                                total_label = ui.label(f"{comp.prix_total():.2f}").classes('w-20 text-right font-bold')
                                                
                                                def update_composant(c=comp, q=qte_input, p=pu_input, t=total_label, l=ligne):
                                                    try:
                                                        c.quantite = float(q.value.replace(',', '.')) if q.value else 0
                                                        c.prix_unitaire = float(p.value.replace(',', '.')) if p.value else 0
                                                    except (ValueError, AttributeError):
                                                        c.quantite = 0
                                                        c.prix_unitaire = 0
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
                        
                        # Afficher les sous-totaux de tous les chapitres ouverts à la fin
                        if app_instance.current_devis_lignes:
                            # Trouver tous les chapitres ouverts à la fin (en remontant la hiérarchie)
                            open_chapters = []
                            for i in range(len(app_instance.current_devis_lignes) - 1, -1, -1):
                                if app_instance.current_devis_lignes[i].type == 'chapitre':
                                    chapter_niveau = getattr(app_instance.current_devis_lignes[i], 'niveau', 1)
                                    if i in section_totals_map:
                                        # Ajouter ce chapitre s'il n'est pas déjà fermé par un chapitre de même niveau
                                        if not any(niv == chapter_niveau for idx, niv, tot in open_chapters):
                                            open_chapters.append((i, chapter_niveau, section_totals_map[i][1]))
                            
                            # Afficher les sous-totaux du plus profond au plus haut (3 -> 2 -> 1)
                            for chapter_idx, chapter_niveau, chapter_total in sorted(open_chapters, key=lambda x: -x[1]):
                                chapter_titre = app_instance.current_devis_lignes[chapter_idx].titre
                                if chapter_niveau == 3:
                                    with ui.row().classes('w-full px-1 bg-purple-50 border-t-2 border-purple-300'):
                                        ui.label('').classes('w-12 px-2')
                                        ui.label('').classes('w-6')
                                        ui.label('').classes('w-20 px-2')
                                        ui.label(f'Sous-total - {chapter_titre}').classes('flex-1 px-2 font-bold text-purple-800')
                                        ui.label('').classes('w-24 px-2')
                                        ui.label('').classes('w-32 px-2')
                                        ui.label(f"{chapter_total:.2f} €").classes('w-32 px-2 text-right font-bold text-purple-800')
                                        ui.label('').classes('w-56 px-2')
                                elif chapter_niveau == 2:
                                    with ui.row().classes('w-full px-1 bg-green-50 border-t-2 border-green-300'):
                                        ui.label('').classes('w-12 px-2')
                                        ui.label('').classes('w-6')
                                        ui.label('').classes('w-20 px-2')
                                        ui.label(f'Sous-total - {chapter_titre}').classes('flex-1 px-2 font-bold text-green-800')
                                        ui.label('').classes('w-24 px-2')
                                        ui.label('').classes('w-32 px-2')
                                        ui.label(f"{chapter_total:.2f} €").classes('w-32 px-2 text-right font-bold text-green-800')
                                        ui.label('').classes('w-56 px-2')
                            
                            # Afficher le sous-total du dernier chapitre de niveau 1
                            # Trouver le dernier chapitre de niveau 1
                            last_niveau_1_idx = None
                            for i in range(len(app_instance.current_devis_lignes) - 1, -1, -1):
                                if app_instance.current_devis_lignes[i].type == 'chapitre':
                                    chapter_niveau = getattr(app_instance.current_devis_lignes[i], 'niveau', 1)
                                    if chapter_niveau == 1:
                                        last_niveau_1_idx = i
                                        break
                            
                            total_general = sum(ligne.prix_ht for ligne in app_instance.current_devis_lignes if ligne.type == 'ouvrage')
                            if last_niveau_1_idx is not None:
                                niveau_1_titre = app_instance.current_devis_lignes[last_niveau_1_idx].titre
                                with ui.row().classes('w-full px-1 bg-blue-50 border-t-2 border-blue-300'):
                                    ui.label('').classes('w-12 px-2')
                                    ui.label('').classes('w-6')
                                    ui.label('').classes('w-20 px-2')
                                    ui.label(f'Sous-total - {niveau_1_titre}').classes('flex-1 px-2 font-bold text-blue-800')
                                    ui.label('').classes('w-24 px-2')
                                    ui.label('').classes('w-32 px-2')
                                    ui.label(f"{total_general:.2f} €").classes('w-32 px-2 text-right font-bold text-blue-800')
                                    ui.label('').classes('w-56 px-2')
                            else:
                                with ui.row().classes('w-full px-1 bg-blue-50 border-t-2 border-blue-300'):
                                    ui.label('').classes('w-12 px-2')
                                    ui.label('').classes('w-6')
                                    ui.label('').classes('w-20 px-2')
                                    ui.label(f'Total général').classes('flex-1 px-2 font-bold text-blue-800')
                                    ui.label('').classes('w-24 px-2')
                                    ui.label('').classes('w-32 px-2')
                                    ui.label(f"{total_general:.2f} €").classes('w-32 px-2 text-right font-bold text-blue-800')
                                    ui.label('').classes('w-56 px-2')
                
                def show_edit_dialog(idx):
                    """Affiche la dialog d'édition pour une ligne"""
                    ligne = app_instance.current_devis_lignes[idx]
                    
                    with ui.dialog() as dialog:
                        with ui.card().classes('w-full max-w-2xl'):
                            if ligne.type == 'chapitre':
                                ui.label(ligne.titre[:50]).classes('text-lg font-bold mb-6')
                                titre = ui.input('Titre', value=ligne.titre).classes('w-full')
                                niveau = ui.select(
                                    label='Niveau',
                                    options={1: 'Niveau 1', 2: 'Niveau 2', 3: 'Niveau 3'},
                                    value=getattr(ligne, 'niveau', 1)
                                ).classes('w-full mt-4')
                                
                                with ui.row().classes('gap-2 mt-6 justify-end'):
                                    def save():
                                        ligne.titre = titre.value
                                        ligne.niveau = niveau.value
                                        recalculate_ouvrage_niveaux()
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
                                    
                                    # Prix unitaire en lecture seule (calculé depuis les composants)
                                    ui.input('Prix unitaire (€)', value=f"{ligne.prix_unitaire:.2f}").classes('w-full').props('readonly')
                                    total_label = ui.label(f"Total HT : {ligne.quantite * ligne.prix_unitaire:.2f} €").classes('text-lg font-semibold mt-2')
                                    
                                    # Mise à jour du total en temps réel
                                    def update_total():
                                        try:
                                            qte = float(quantite.value or 0)
                                            pu = ligne.prix_unitaire
                                            total_label.text = f"Total HT : {qte * pu:.2f} €"
                                        except:
                                            total_label.text = "Total HT : 0.00 €"
                                    
                                    quantite.on_value_change(lambda: update_total())
                                
                                with ui.row().classes('gap-2 mt-6 justify-end'):
                                    def save():
                                        ligne.designation = designation.value
                                        ligne.description = description.value
                                        ligne.quantite = quantite.value
                                        # Ne pas modifier le prix_unitaire - il vient des composants
                                        refresh_table()
                                        app_instance.update_totals()
                                        dialog.close()
                                    
                                    ui.button('Enregistrer', on_click=save).classes('themed-button')
                                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    
                    dialog.open()
                
                def recalculate_ouvrage_niveaux():
                    """Recalcule les niveaux des ouvrages en fonction des chapitres au-dessus"""
                    current_niveau = 1
                    for ligne in app_instance.current_devis_lignes:
                        if ligne.type == 'chapitre':
                            current_niveau = getattr(ligne, 'niveau', 1)
                        elif ligne.type == 'ouvrage':
                            ligne.niveau = current_niveau
                
                def move_up(idx):
                    if idx > 0:
                        app_instance.current_devis_lignes[idx], app_instance.current_devis_lignes[idx-1] = \
                            app_instance.current_devis_lignes[idx-1], app_instance.current_devis_lignes[idx]
                        recalculate_ouvrage_niveaux()
                        refresh_table()
                        app_instance.update_totals()
                
                def move_down(idx):
                    if idx < len(app_instance.current_devis_lignes) - 1:
                        app_instance.current_devis_lignes[idx], app_instance.current_devis_lignes[idx+1] = \
                            app_instance.current_devis_lignes[idx+1], app_instance.current_devis_lignes[idx]
                        recalculate_ouvrage_niveaux()
                        refresh_table()
                        app_instance.update_totals()
                
                def delete_ligne(idx):
                    app_instance.current_devis_lignes.pop(idx)
                    refresh_table()
                    app_instance.update_totals()
                
                def duplicate_ligne(idx):
                    """Duplique une ligne à la position suivante"""
                    ligne_originale = app_instance.current_devis_lignes[idx]
                    
                    # Créer une copie de la ligne
                    if ligne_originale.type == 'chapitre':
                        nouvelle_ligne = LigneDevis(
                            type='chapitre',
                            id=app_instance.next_ligne_id,
                            titre=ligne_originale.titre + ' (copie)',
                            niveau=getattr(ligne_originale, 'niveau', 1)
                        )
                    elif ligne_originale.type == 'texte':
                        nouvelle_ligne = LigneDevis(
                            type='texte',
                            id=app_instance.next_ligne_id,
                            texte=ligne_originale.texte,
                            niveau=getattr(ligne_originale, 'niveau', 1)
                        )
                    else:  # ouvrage
                        nouvelle_ligne = LigneDevis(
                            type='ouvrage',
                            id=app_instance.next_ligne_id,
                            ouvrage_id=ligne_originale.ouvrage_id,
                            designation=ligne_originale.designation,
                            description=ligne_originale.description,
                            quantite=ligne_originale.quantite,
                            unite=ligne_originale.unite,
                            prix_unitaire=ligne_originale.prix_unitaire,
                            composants=ligne_originale.composants.copy() if hasattr(ligne_originale, 'composants') else [],
                            niveau=getattr(ligne_originale, 'niveau', 1)
                        )
                    
                    app_instance.next_ligne_id += 1
                    # Insérer la nouvelle ligne juste après l'originale
                    app_instance.current_devis_lignes.insert(idx + 1, nouvelle_ligne)
                    notify_success('Ligne dupliquée')
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
        
        # Définir les fonctions de sauvegarde et génération PDF
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
                        existing_devis.objet = objet_devis.value
                        existing_devis.lignes = app_instance.current_devis_lignes
                        existing_devis.coefficient_marge = app_instance.current_devis_coefficient
                        existing_devis.tva = app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                        
                        app_instance.dm.update_devis(existing_devis)
                        notify_success(f'Devis {numero} mis à jour')
                    else:
                        devis = Devis(
                            numero=numero,
                            date=date_devis.value,
                            client_id=app_instance.selected_client_id,
                            objet=objet_devis.value,
                            lignes=app_instance.current_devis_lignes,
                            coefficient_marge=app_instance.current_devis_coefficient,
                            tva=app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                        )
                        
                        app_instance.dm.add_devis(devis)
                        notify_success(f'Devis {numero} créé')
                    
                    # Rafraîchir la liste des devis si callback disponible
                    if hasattr(app_instance, 'display_table_callback'):
                        app_instance.display_table_callback()
                    
                except Exception as e:
                    notify_error(f'Erreur: {str(e)}')
        
        # Sauvegarde automatique toutes les 5 minutes
        autosave_timer = ui.timer(300, lambda: save_devis() if app_instance.current_devis_lignes else None)
        
        def generate_pdf():
            """Générer un PDF du devis avec choix du modèle"""
            # Charger les templates disponibles
            templates_file = Path(__file__).parent.parent.parent / 'data' / 'devis_templates.json'
            
            def load_templates():
                if templates_file.exists():
                    try:
                        with open(templates_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except:
                        return {}
                return {}
            
            templates = load_templates()
            
            if not templates:
                notify_warning('Aucun modèle de devis disponible. Créez-en un dans l\'éditeur.')
                return
            
            # Dialog pour choisir le template
            with ui.dialog() as template_dialog, ui.card().classes('w-96'):
                ui.label('Choisir un modèle').classes('text-lg font-bold mb-4')
                
                def generate_with_template(template_data):
                    try:
                        from reportlab.lib.pagesizes import A4
                        from reportlab.lib.units import mm
                        from reportlab.pdfgen import canvas
                        from reportlab.lib import colors
                        import os
                        
                        # Créer le devis
                        devis = Devis(
                            numero=numero_devis.value,
                            date=date_devis.value,
                            client_id=app_instance.selected_client_id,
                            objet=objet_devis.value,
                            lignes=app_instance.current_devis_lignes,
                            coefficient_marge=app_instance.current_devis_coefficient,
                            tva=app_instance.tva_rate_field.value if app_instance.tva_rate_field else 20.0
                        )
                        
                        client = app_instance.dm.get_client_by_id(app_instance.selected_client_id)
                        org = app_instance.dm.organisation
                        
                        # Créer le dossier PDF
                        client_name = f"{client.prenom}_{client.nom}" if client else "Client_inconnu"
                        client_name = client_name.replace(" ", "_")
                        pdf_dir = app_instance.dm.data_dir / 'pdf' / client_name
                        pdf_dir.mkdir(parents=True, exist_ok=True)
                        pdf_path = pdf_dir / f"{devis.numero}.pdf"
                        
                        # Générer le PDF avec le template
                        c = canvas.Canvas(str(pdf_path), pagesize=A4)
                        width, height = A4
                        
                        # Parcourir tous les blocs du template
                        for block in template_data['blocks']:
                            block_type = block.get('type', '')
                            x_mm = block.get('x', 0) * mm / 3.78
                            y_mm = (height - block.get('y', 0) * mm / 3.78)
                            w_mm = block.get('width', 200) * mm / 3.78
                            
                            c.saveState()
                            
                            # Générer le contenu selon le type (code similaire à editeur_devis.py)
                            if block_type == 'adresse_entreprise':
                                c.setFont("Helvetica-Bold", 11)
                                c.drawString(x_mm, y_mm, org.nom or "MON ENTREPRISE BTP")
                                c.setFont("Helvetica", 9)
                                y_mm -= 12
                                c.drawString(x_mm, y_mm, org.adresse or "")
                                y_mm -= 10
                                c.drawString(x_mm, y_mm, f"{org.cp or ''} {org.ville or ''}")
                                y_mm -= 10
                                c.drawString(x_mm, y_mm, f"Tél: {org.telephone or ''}")
                                y_mm -= 10
                                c.drawString(x_mm, y_mm, f"Email: {org.email or ''}")
                            
                            elif block_type == 'titre':
                                c.setFont("Helvetica-Bold", 28)
                                c.drawCentredString(x_mm + w_mm/2, y_mm, "DEVIS")
                            
                            elif block_type == 'client':
                                c.setFont("Helvetica", 10)
                                if client:
                                    c.drawString(x_mm, y_mm, f"{client.prenom or ''} {client.nom or ''}")
                                    y_mm -= 12
                                    if client.entreprise:
                                        c.drawString(x_mm, y_mm, client.entreprise)
                                        y_mm -= 12
                                    c.drawString(x_mm, y_mm, client.adresse or "")
                                    y_mm -= 12
                                    c.drawString(x_mm, y_mm, f"{client.cp or ''} {client.ville or ''}")
                            
                            elif block_type == 'infos_devis':
                                c.setFont("Helvetica-Bold", 9)
                                c.drawString(x_mm, y_mm, f"Ref:")
                                c.setFont("Helvetica", 9)
                                c.drawString(x_mm + 40, y_mm, devis.numero)
                                y_mm -= 12
                                c.setFont("Helvetica-Bold", 9)
                                c.drawString(x_mm, y_mm, f"Date:")
                                c.setFont("Helvetica", 9)
                                c.drawString(x_mm + 40, y_mm, devis.date)
                            
                            elif block_type == 'objet':
                                c.setFont("Helvetica-Bold", 12)
                                objet_text = devis.objet if devis.objet else "Description des travaux"
                                c.drawString(x_mm, y_mm, f"Objet: {objet_text}")
                            
                            elif block_type == 'tableau_ouvrages':
                                c.setFont("Helvetica-Bold", 10)
                                c.drawString(x_mm, y_mm, "DÉTAIL DES OUVRAGES")
                                y_mm -= 20
                                
                                # Créer les données du tableau
                                data = [['Réf', 'Désignation', 'Qté', 'P.U.', 'Total']]
                                for ligne in devis.lignes:
                                    if ligne.type == 'ouvrage':
                                        ouvrage = app_instance.dm.get_ouvrage_by_id(ligne.ouvrage_id)
                                        data.append([
                                            str(ligne.ouvrage_id),
                                            ouvrage.designation if ouvrage else '',
                                            str(ligne.quantite),
                                            f"{ligne.prix_unitaire:.2f}€",
                                            f"{ligne.prix_ht:.2f}€"
                                        ])
                                
                                # Dessiner le tableau manuellement
                                c.setFont("Helvetica", 8)
                                row_height = 15
                                for i, row in enumerate(data):
                                    x_pos = x_mm
                                    if i == 0:
                                        c.setFont("Helvetica-Bold", 8)
                                    else:
                                        c.setFont("Helvetica", 8)
                                    
                                    for col in row:
                                        c.drawString(x_pos, y_mm - i * row_height, str(col)[:20])
                                        x_pos += 60
                            
                            elif block_type == 'totaux':
                                totals = devis.calculate_totals()
                                c.setFont("Helvetica-Bold", 10)
                                c.drawRightString(x_mm + w_mm, y_mm, f"Total HT: {totals['ht']:.2f}€")
                                y_mm -= 15
                                c.drawRightString(x_mm + w_mm, y_mm, f"TVA ({devis.tva}%): {totals['tva']:.2f}€")
                                y_mm -= 18
                                c.setFont("Helvetica-Bold", 12)
                                c.drawRightString(x_mm + w_mm, y_mm, f"Total TTC: {totals['ttc']:.2f}€")
                            
                            elif block_type == 'conditions':
                                c.setFont("Helvetica-Bold", 9)
                                c.drawString(x_mm, y_mm, "CONDITIONS GÉNÉRALES")
                                c.setFont("Helvetica", 8)
                                y_mm -= 15
                                conditions_lines = devis.conditions.split('\n') if devis.conditions else []
                                for line in conditions_lines[:5]:
                                    c.drawString(x_mm, y_mm, line[:80])
                                    y_mm -= 10
                            
                            elif block_type == 'signature':
                                c.setFont("Helvetica-Bold", 9)
                                c.drawString(x_mm, y_mm, "Signature du client")
                                c.drawString(x_mm + w_mm/2, y_mm, "Signature entreprise")
                                y_mm -= 30
                                c.setFont("Helvetica", 8)
                                c.drawString(x_mm, y_mm, "Date: ___________")
                                c.drawString(x_mm + w_mm/2, y_mm, "Date: ___________")
                            
                            elif block_type == 'logo':
                                logo_relative = block.get('logoPath', '').lstrip('/')
                                if logo_relative:
                                    base_path = Path(__file__).parent.parent.parent
                                    if logo_relative.startswith('static/'):
                                        logo_path = base_path / logo_relative
                                    else:
                                        logo_path = base_path / logo_relative.lstrip('/')
                                    
                                    if logo_path.exists():
                                        try:
                                            h_mm = block.get('height', 150) * mm / 3.78
                                            c.drawImage(str(logo_path), x_mm, y_mm - h_mm, width=w_mm, height=h_mm, preserveAspectRatio=True, mask='auto')
                                        except:
                                            pass
                            
                            c.restoreState()
                        
                        c.save()
                        template_dialog.close()
                        notify_success(f'PDF généré : {pdf_path.name}')
                        
                        # Ouvrir le PDF
                        os.startfile(str(pdf_path))
                    except Exception as e:
                        notify_error(f'Erreur lors de la génération du PDF : {str(e)}')
                
                # Afficher la liste des templates
                for name, template_data in templates.items():
                    with ui.card().classes('w-full mb-2 hover:bg-gray-100 cursor-pointer'):
                        with ui.row().classes('w-full items-center justify-between p-2').on('click', lambda t=template_data: generate_with_template(t)):
                            with ui.column().classes('flex-1'):
                                ui.label(name).classes('font-semibold')
                                nb_blocs = len(template_data.get('blocks', []))
                                ui.label(f'{nb_blocs} blocs').classes('text-xs text-gray-500')
                            ui.icon('arrow_forward').classes('text-gray-400')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Annuler', on_click=template_dialog.close).props('flat')
            
            template_dialog.open()
        
        def new_devis():
            app_instance.current_devis_lignes = []
            app_instance.current_devis_coefficient = 1.35
            app_instance.selected_client_id = None
            numero_devis.value = get_next_unique_devis_number()
            date_devis.value = datetime.now().strftime('%Y-%m-%d')
            client_select.value = app_instance.dm.clients[0].id if app_instance.dm.clients else None
            refresh_table()
            notify_success('Nouveau devis créé')
        
        # Ajouter les boutons dans la rangée d'action en haut
        with action_buttons_row:
            app_instance.create_themed_button('+ Nouveau', on_click=new_devis).props('color=positive flat')
            ui.button('Enregistrer', on_click=save_devis, icon='save').props('color=primary')
            ui.button('Générer PDF', on_click=generate_pdf, icon='picture_as_pdf').props('color=secondary')
        
        # Charger le devis si demandé depuis la navigation
        if devis_to_load:
                devis_obj = devis_to_load  # devis_to_load est déjà un objet Devis complet
                if devis_obj and hasattr(devis_obj, 'numero'):
                    # Forcer la mise à jour de tous les champs
                    numero_devis.set_value(devis_obj.numero)
                    date_devis.set_value(devis_obj.date)
                    client_select.set_value(devis_obj.client_id)
                    app_instance.selected_client_id = devis_obj.client_id
                    if hasattr(app_instance, 'tva_rate_field') and app_instance.tva_rate_field:
                        app_instance.tva_rate_field.set_value(devis_obj.tva)
                    
                    if devis_obj.lignes:
                        # S'assurer que toutes les lignes ont un niveau (pour compatibilité avec anciennes données)
                        for ligne in devis_obj.lignes:
                            if not hasattr(ligne, 'niveau') or ligne.niveau is None:
                                ligne.niveau = 1
                        app_instance.next_ligne_id = max(l.id for l in devis_obj.lignes) + 1
                    else:
                        app_instance.next_ligne_id = 0
                    
                    refresh_table()
                    app_instance.update_totals()
                    # Notification gérée par liste_devis.py, pas ici
