"""
Panel éditeur de mise en forme des devis avec drag and drop
"""

from nicegui import ui, app
from erp.ui.utils import notify_success, notify_error, notify_info
import json
from pathlib import Path


def create_editeur_devis_panel(app_instance):
    """Crée le panneau d'éditeur de mise en forme des devis avec drag and drop
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Fichier de sauvegarde persistant
    templates_file = Path(__file__).parent.parent.parent / 'data' / 'devis_templates.json'
    
    def load_templates_from_file():
        """Charger les templates depuis le fichier JSON"""
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des templates: {e}")
        return {}
    
    def save_templates_to_file(templates):
        """Sauvegarder les templates dans le fichier JSON"""
        try:
            templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des templates: {e}")
            return False
    
    # Ajouter les styles CSS pour la page A4 et le drag and drop
    ui.add_head_html('''
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
    <style>
        .a4-page {
            width: 210mm;
            height: 297mm;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
            margin: 0 auto;
        }
        
        .palette-block {
            transition: all 0.2s;
        }
        
        .palette-block:hover {
            background: #e8e8e8 !important;
            border-color: #999 !important;
            transform: translateX(4px);
        }
        
        .palette-block:active {
            cursor: grabbing !important;
        }
        
        .palette-block.dragging {
            opacity: 0.5;
        }
        
        .dropped-block {
            position: absolute;
            background: white;
            border: 2px solid #ddd;
            padding: 12px;
            cursor: move;
            min-width: 100px;
            min-height: 40px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            border-radius: 4px;
            z-index: 10;
            pointer-events: auto;
        }
        
        .dropped-block:hover {
            border-color: #666;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        
        .dropped-block.selected {
            border-color: #c84c3c;
            box-shadow: 0 0 0 3px rgba(200,76,60,0.2);
        }
        
        .block-controls {
            position: absolute;
            top: -36px;
            right: 0;
            display: none;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 6px;
            gap: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        
        .dropped-block:hover .block-controls,
        .dropped-block.selected .block-controls {
            display: flex;
        }
        
        .control-btn {
            border: none;
            background: #f5f5f5;
            cursor: pointer;
            padding: 6px 10px;
            border-radius: 3px;
            font-size: 14px;
        }
        
        .control-btn:hover {
            background: #e0e0e0;
        }
        
        .resize-handle {
            position: absolute;
            bottom: 0;
            right: 0;
            width: 12px;
            height: 12px;
            background: #c84c3c;
            cursor: se-resize;
            border-radius: 0 0 2px 0;
        }
    </style>
    ''')
    
    # Variable pour mémoriser le template actuellement chargé (déclarée en dehors)
    current_template_name = {'value': None}
    current_template_label_ref = {'label': None}
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; width: 100%;'):
        ui.label('Éditeur de mise en forme du devis').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Barre d'actions en haut
        with ui.row().classes('w-full items-center justify-between mb-6 p-4').style('background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;'):
            # Indicateur de modèle actuel à gauche
            with ui.row().classes('items-center gap-2'):
                ui.icon('label', size='sm').classes('text-gray-500')
                current_template_label_ref['label'] = ui.label('Aucun modèle chargé').classes('text-sm text-gray-600 italic')
            
            # Placeholder pour les boutons (seront ajoutés après définition des fonctions)
            actions_row = ui.row().classes('gap-2')
        
        # Conteneur principal avec 2 colonnes
        with ui.row().classes('w-full gap-6').style('min-height: 700px; align-items: flex-start;'):
            # Colonne gauche : Palette de blocs
            with ui.column().classes('w-72').style('min-width: 280px;'):
                with ui.card().classes('w-full shadow-sm').style('padding: 20px;'):
                    ui.label('Blocs disponibles').classes('text-xl font-bold mb-2')
                    ui.label('Glissez-déposez sur la page A4').classes('text-sm text-gray-600 mb-4')
                    
                    # Palette de blocs avec drag and drop HTML natif
                    palette_blocks = [
                        {'type': 'adresse_entreprise', 'icon': 'business', 'label': 'Adresse entreprise'},
                        {'type': 'titre', 'icon': 'title', 'label': 'Titre'},
                        {'type': 'texte', 'icon': 'text_fields', 'label': 'Texte libre'},
                        {'type': 'client', 'icon': 'person', 'label': 'Adresse client'},
                        {'type': 'infos_devis', 'icon': 'info', 'label': 'Infos devis'},
                        {'type': 'tableau_ouvrages', 'icon': 'table_chart', 'label': 'Tableau ouvrages'},
                        {'type': 'objet', 'icon': 'subject', 'label': 'Objet'},
                        {'type': 'totaux', 'icon': 'calculate', 'label': 'Totaux'},
                        {'type': 'conditions', 'icon': 'gavel', 'label': 'Conditions'},
                        {'type': 'signature', 'icon': 'draw', 'label': 'Signature'},
                        {'type': 'logo', 'icon': 'image', 'label': 'Logo'},
                    ]
                    
                    palette_container = ui.element('div').classes('w-full').style('display: flex; flex-direction: column; gap: 8px; user-select: none;')
                    
                    # Injecter le HTML de la palette directement
                    palette_html = ''
                    for pb in palette_blocks:
                        palette_html += f'''
                            <div class="palette-block" 
                                 draggable="true" 
                                 data-block-type="{pb['type']}"
                                 style="padding: 12px; background: #f5f5f5; border: 2px solid #ddd; border-radius: 4px; cursor: grab; display: flex; align-items: center; gap: 12px; transition: all 0.2s;">
                                <span class="material-icons" style="color: #666;">{pb['icon']}</span>
                                <span style="font-size: 14px; font-weight: 500;">{pb['label']}</span>
                            </div>
                        '''
                    
                    with palette_container:
                        ui.html(palette_html, sanitize=False)
                    
                    # Définir les fonctions pour les actions
                    async def save_template():
                        """Sauvegarder la présentation du devis"""
                        result = await ui.run_javascript('window.saveTemplate()', timeout=5)
                        if result and 'blocks' in result:
                            # Si un template est déjà chargé, proposer de le mettre à jour
                            if current_template_name['value']:
                                # Mise à jour directe du template existant
                                templates = load_templates_from_file()
                                
                                templates[current_template_name['value']] = {
                                    'blocks': result['blocks'],
                                    'timestamp': result['timestamp'],
                                    'name': current_template_name['value']
                                }
                                
                                if save_templates_to_file(templates):
                                    app.storage.user['devis_templates'] = templates
                                    notify_success(f'Présentation "{current_template_name["value"]}" mise à jour ! ({len(result["blocks"])} blocs)')
                                else:
                                    notify_error('Erreur lors de la mise à jour')
                            else:
                                # Nouveau template - demander le nom
                                with ui.dialog() as save_dialog, ui.card():
                                    ui.label('Nom de la présentation').classes('text-lg font-bold mb-2')
                                    template_name = ui.input('Nom', placeholder='Ex: Devis standard').classes('w-full')
                                    
                                    async def do_save():
                                        if not template_name.value:
                                            notify_error('Veuillez saisir un nom')
                                            return
                                        
                                        # Récupérer les templates existants (fichier JSON prioritaire)
                                        templates = load_templates_from_file()
                                        
                                        # Ajouter le nouveau template
                                        templates[template_name.value] = {
                                            'blocks': result['blocks'],
                                            'timestamp': result['timestamp'],
                                            'name': template_name.value
                                        }
                                        
                                        # Sauvegarder dans le fichier JSON (persistant)
                                        if save_templates_to_file(templates):
                                            # Synchroniser avec app.storage pour compatibilité
                                            app.storage.user['devis_templates'] = templates
                                            current_template_name['value'] = template_name.value
                                            current_template_label_ref['label'].text = f'Modèle: {template_name.value}'
                                            notify_success(f'Présentation "{template_name.value}" sauvegardée ! ({len(result["blocks"])} blocs)')
                                        else:
                                            notify_error('Erreur lors de la sauvegarde')
                                        save_dialog.close()
                                    
                                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                                        ui.button('Annuler', on_click=save_dialog.close).props('flat')
                                        ui.button('Enregistrer', on_click=do_save).props('color=primary')
                                
                                save_dialog.open()
                        else:
                            notify_error('Erreur lors de la sauvegarde')
                    
                    async def load_template():
                        """Charger une présentation sauvegardée"""
                        # Charger depuis le fichier JSON (persistant)
                        templates = load_templates_from_file()
                        
                        # Synchroniser avec app.storage
                        if templates:
                            app.storage.user['devis_templates'] = templates
                        
                        if not templates:
                            notify_info('Aucune présentation sauvegardée')
                            return
                        
                        # Dialog pour choisir le template
                        with ui.dialog() as load_dialog, ui.card().classes('w-96'):
                            ui.label('Choisir une présentation').classes('text-lg font-bold mb-4')
                            
                            import json
                            from datetime import datetime
                            
                            async def do_load(template_data):
                                await ui.run_javascript(f'window.loadTemplate({json.dumps(template_data)})', timeout=5)
                                # Mémoriser le template chargé
                                current_template_name['value'] = template_data['name']
                                current_template_label_ref['label'].text = f'Modèle: {template_data["name"]}'
                                notify_success(f'Présentation "{template_data["name"]}" chargée ! ({len(template_data["blocks"])} blocs)')
                                load_dialog.close()
                            
                            async def do_delete(template_name):
                                templates = load_templates_from_file()
                                if template_name in templates:
                                    del templates[template_name]
                                    if save_templates_to_file(templates):
                                        app.storage.user['devis_templates'] = templates
                                        notify_success(f'Présentation "{template_name}" supprimée')
                                    else:
                                        notify_error('Erreur lors de la suppression')
                                    load_dialog.close()
                            
                            # Liste des templates
                            for name, template_data in templates.items():
                                with ui.card().classes('w-full mb-2 hover:bg-gray-100 cursor-pointer'):
                                    with ui.row().classes('w-full items-center justify-between'):
                                        with ui.column().classes('flex-1'):
                                            ui.label(name).classes('font-bold')
                                            timestamp_str = template_data.get('timestamp', '')
                                            if timestamp_str:
                                                try:
                                                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                                    ui.label(dt.strftime('%d/%m/%Y %H:%M')).classes('text-sm text-gray-600')
                                                except:
                                                    pass
                                            ui.label(f"{len(template_data['blocks'])} blocs").classes('text-sm text-gray-500')
                                        
                                        with ui.row().classes('gap-1'):
                                            ui.button(icon='download', on_click=lambda td=template_data: do_load(td)).props('flat round size=sm color=primary')
                                            ui.button(icon='delete', on_click=lambda n=name: do_delete(n)).props('flat round size=sm color=negative')
                            
                            ui.button('Annuler', on_click=load_dialog.close).props('flat').classes('w-full mt-4')
                        
                        load_dialog.open()
                    
                    async def save_as_template():
                        """Enregistrer sous un nouveau nom"""
                        result = await ui.run_javascript('window.saveTemplate()', timeout=5)
                        if result and 'blocks' in result:
                            with ui.dialog() as save_dialog, ui.card():
                                ui.label('Enregistrer sous...').classes('text-lg font-bold mb-2')
                                template_name = ui.input('Nom', placeholder='Ex: Devis standard').classes('w-full')
                                
                                # Pré-remplir avec le nom actuel + " (copie)" si un template est chargé
                                if current_template_name['value']:
                                    template_name.value = f"{current_template_name['value']} (copie)"
                                
                                async def do_save():
                                    if not template_name.value:
                                        notify_error('Veuillez saisir un nom')
                                        return
                                    
                                    templates = load_templates_from_file()
                                    templates[template_name.value] = {
                                        'blocks': result['blocks'],
                                        'timestamp': result['timestamp'],
                                        'name': template_name.value
                                    }
                                    
                                    if save_templates_to_file(templates):
                                        app.storage.user['devis_templates'] = templates
                                        current_template_name['value'] = template_name.value
                                        current_template_label_ref['label'].text = f'Modèle: {template_name.value}'
                                        notify_success(f'Présentation "{template_name.value}" sauvegardée ! ({len(result["blocks"])} blocs)')
                                    else:
                                        notify_error('Erreur lors de la sauvegarde')
                                    save_dialog.close()
                                
                                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                                    ui.button('Annuler', on_click=save_dialog.close).props('flat')
                                    ui.button('Enregistrer', on_click=do_save).props('color=primary')
                            
                            save_dialog.open()
                    
                    def new_template():
                        """Créer un nouveau modèle (efface le lien avec le modèle actuel)"""
                        current_template_name['value'] = None
                        current_template_label_ref['label'].text = 'Aucun modèle chargé'
                        ui.run_javascript('window.clearAll()')
                        notify_info('Nouveau modèle créé')
                    
                    async def select_logo_for_block(block_id: str):
                        """Sélectionner un fichier PNG depuis le dossier static"""
                        from pathlib import Path
                        import os
                        
                        # Lister les fichiers PNG dans static
                        static_dir = Path('static')
                        png_files = []
                        if static_dir.exists():
                            png_files = [f.name for f in static_dir.glob('*.png')]
                        
                        if not png_files:
                            notify_error('Aucun fichier PNG trouvé dans le dossier static')
                            return
                        
                        # Dialog pour sélectionner l'image
                        with ui.dialog() as logo_dialog, ui.card().classes('w-96'):
                            ui.label('Sélectionner un logo').classes('text-lg font-bold mb-4')
                            
                            selected_file = {'value': None}
                            
                            with ui.column().classes('w-full gap-2'):
                                for png_file in sorted(png_files):
                                    file_path = f'/static/{png_file}'
                                    with ui.row().classes('w-full items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer rounded').style('border: 1px solid #e5e7eb;'):
                                        # Miniature de l'image
                                        ui.image(file_path).classes('w-16 h-16 object-contain')
                                        ui.label(png_file).classes('flex-1')
                                        ui.button(
                                            icon='check',
                                            on_click=lambda f=file_path: [
                                                selected_file.update({'value': f}),
                                                logo_dialog.close()
                                            ]
                                        ).props('flat color=primary size=sm')
                            
                            ui.button('Annuler', on_click=logo_dialog.close).props('flat').classes('mt-4')
                        
                        logo_dialog.open()
                        await logo_dialog
                        
                        # Appliquer l'image au bloc
                        if selected_file['value']:
                            ui.run_javascript(f'''
                                const block = document.querySelector('[data-block-id="{block_id}"]');
                                if (block) {{
                                    block.dataset.logoPath = '{selected_file["value"]}';
                                    block.innerHTML = '<img src="{selected_file["value"]}" style="width: 100%; height: 100%; object-fit: contain;" />';
                                }}
                            ''')
                            notify_success(f'Logo appliqué : {selected_file["value"].split("/")[-1]}')
                    
                    # Exposer la fonction pour JavaScript
                    ui.on('select_logo_for_block', lambda e: select_logo_for_block(e.args))
                    
                    async def preview_pdf():
                        """Générer un aperçu PDF du devis avec données de démo"""
                        # Capturer l'état actuel des blocs
                        result = await ui.run_javascript('window.saveTemplate()', timeout=5)
                        
                        if not result or not result.get('blocks'):
                            notify_error('Aucun bloc à prévisualiser')
                            return
                        
                        # Utiliser des données de démo
                        org = app_instance.dm.organisation
                        demo_client = app_instance.dm.clients[0] if app_instance.dm.clients else None
                        demo_devis = app_instance.dm.devis_list[0] if app_instance.dm.devis_list else None
                        
                        # Obtenir le client associé au devis
                        client = None
                        if demo_devis:
                            client = app_instance.dm.get_client_by_id(demo_devis.client_id)
                        elif demo_client:
                            client = demo_client
                        
                        async def generate_pdf_with_demo():
                            """Générer le PDF avec le premier devis disponible ou des données de démo"""
                            from reportlab.lib.pagesizes import A4
                            from reportlab.lib.units import mm
                            from reportlab.pdfgen import canvas
                            from reportlab.lib import colors
                            from datetime import datetime
                            from pathlib import Path
                            import os
                            
                            # Utiliser le premier devis disponible ou créer des données de démo
                            if demo_devis:
                                selected = demo_devis
                                pdf_client = app_instance.dm.get_client_by_id(selected.client_id)
                            else:
                                # Créer un objet de démo
                                from erp.core.models import Devis
                                selected = Devis(
                                    numero="DEV-2025-DEMO",
                                    date=datetime.now().strftime('%Y-%m-%d'),
                                    client_id=demo_client.id if demo_client else 0,
                                    objet="Travaux de rénovation",
                                    lignes=[],
                                    coefficient_marge=1.35,
                                    tva=20.0,
                                    validite=30
                                )
                                pdf_client = demo_client
                            
                            # Créer le dossier pour le client
                            pdf_dir = Path(__file__).parent.parent.parent / 'pdf'
                            if pdf_client:
                                client_dir = pdf_dir / pdf_client.nom.replace(' ', '_')
                            else:
                                client_dir = pdf_dir / 'Inconnu'
                            client_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Nom du fichier PDF
                            pdf_filename = f"Devis_{selected.numero.replace('/', '_')}.pdf"
                            pdf_path = client_dir / pdf_filename
                            
                            try:
                                # Créer le PDF avec ReportLab
                                c = canvas.Canvas(str(pdf_path), pagesize=A4)
                                width, height = A4
                                
                                # Parcourir tous les blocs du template
                                for block in result['blocks']:
                                    block_type = block.get('type', '')
                                    # Convertir les coordonnées (origin en haut à gauche en HTML -> bas à gauche en PDF)
                                    x_mm = block.get('x', 0) * mm / 3.78  # Conversion px to mm approximative
                                    y_mm = (height - block.get('y', 0) * mm / 3.78)  # Inverser Y
                                    w_mm = block.get('width', 200) * mm / 3.78
                                    
                                    c.saveState()
                                    
                                    # Générer le contenu selon le type
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
                                        if pdf_client:
                                            c.drawString(x_mm, y_mm, f"{pdf_client.prenom or ''} {pdf_client.nom or ''}")
                                            y_mm -= 12
                                            if pdf_client.entreprise:
                                                c.drawString(x_mm, y_mm, pdf_client.entreprise)
                                                y_mm -= 12
                                            c.drawString(x_mm, y_mm, pdf_client.adresse or "")
                                            y_mm -= 12
                                            c.drawString(x_mm, y_mm, f"{pdf_client.cp or ''} {pdf_client.ville or ''}")
                                    
                                    elif block_type == 'infos_devis':
                                        c.setFont("Helvetica-Bold", 9)
                                        c.drawString(x_mm, y_mm, f"Ref:")
                                        c.setFont("Helvetica", 9)
                                        c.drawString(x_mm + 40, y_mm, selected.numero)
                                        y_mm -= 12
                                        c.setFont("Helvetica-Bold", 9)
                                        c.drawString(x_mm, y_mm, f"Date:")
                                        c.setFont("Helvetica", 9)
                                        c.drawString(x_mm + 40, y_mm, selected.date)
                                    
                                    elif block_type == 'objet':
                                        c.setFont("Helvetica-Bold", 12)
                                        objet_text = selected.objet if selected.objet else "Description des travaux"
                                        c.drawString(x_mm, y_mm, f"Objet: {objet_text}")
                                    
                                    elif block_type == 'tableau_ouvrages':
                                        from reportlab.platypus import Table, TableStyle
                                        c.setFont("Helvetica-Bold", 10)
                                        c.drawString(x_mm, y_mm, "DÉTAIL DES OUVRAGES")
                                        y_mm -= 20
                                        
                                        # Créer les données du tableau
                                        data = [['Réf', 'Désignation', 'Qté', 'P.U.', 'Total']]
                                        for ligne in selected.lignes:
                                            if ligne.type == 'ouvrage':
                                                ouvrage = app_instance.dm.get_ouvrage_by_id(ligne.ouvrage_id)
                                                data.append([
                                                    str(ligne.ouvrage_id),
                                                    ouvrage.designation if ouvrage else '',
                                                    str(ligne.quantite),
                                                    f"{ligne.prix_unitaire:.2f}€",
                                                    f"{ligne.prix_ht:.2f}€"
                                                ])
                                        
                                        # Dessiner le tableau manuellement (simplifié)
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
                                        totals = selected.calculate_totals()
                                        c.setFont("Helvetica-Bold", 10)
                                        c.drawRightString(x_mm + w_mm, y_mm, f"Total HT: {totals['ht']:.2f}€")
                                        y_mm -= 15
                                        c.drawRightString(x_mm + w_mm, y_mm, f"TVA ({selected.tva}%): {totals['tva']:.2f}€")
                                        y_mm -= 18
                                        c.setFont("Helvetica-Bold", 12)
                                        c.drawRightString(x_mm + w_mm, y_mm, f"Total TTC: {totals['ttc']:.2f}€")
                                    
                                    elif block_type == 'conditions':
                                        c.setFont("Helvetica-Bold", 9)
                                        c.drawString(x_mm, y_mm, "CONDITIONS GÉNÉRALES")
                                        c.setFont("Helvetica", 8)
                                        y_mm -= 15
                                        conditions_lines = selected.conditions.split('\n') if selected.conditions else []
                                        for line in conditions_lines[:5]:  # Limiter à 5 lignes
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
                                        # Dessiner le logo
                                        logo_relative = block.get('logoPath', '').lstrip('/')
                                        
                                        if not logo_relative:
                                            # Pas de logo configuré, afficher un placeholder
                                            c.setStrokeColor(colors.grey)
                                            c.setFillColor(colors.lightgrey)
                                            h_mm = block.get('height', 150) * mm / 3.78
                                            c.rect(x_mm, y_mm - h_mm, w_mm, h_mm, fill=1)
                                            c.setFillColor(colors.black)
                                            c.setFont("Helvetica", 8)
                                            c.drawString(x_mm + 5, y_mm - h_mm/2, "Logo non configuré")
                                        else:
                                            # Le chemin est /static/xxx.png, construire le chemin absolu
                                            # __file__ est dans erp/ui/panels/, on remonte de 3 niveaux pour arriver à erp/, puis encore 1 pour la racine
                                            base_path = Path(__file__).parent.parent.parent.parent
                                            # logo_relative peut être "static/logo.png" ou "/static/logo.png"
                                            if logo_relative.startswith('static/'):
                                                logo_path = base_path / logo_relative
                                            else:
                                                # Enlever le / initial s'il existe
                                                logo_path = base_path / logo_relative.lstrip('/')
                                            
                                            if logo_path.exists():
                                                try:
                                                    # Récupérer la hauteur du bloc (convertie depuis HTML)
                                                    h_mm = block.get('height', 150) * mm / 3.78
                                                    # Dessiner l'image (y_mm est déjà inversé, on descend de la hauteur)
                                                    c.drawImage(str(logo_path), x_mm, y_mm - h_mm, width=w_mm, height=h_mm, preserveAspectRatio=True, mask='auto')
                                                except Exception as e:
                                                    # En cas d'erreur, dessiner un rectangle pour montrer où devrait être le logo
                                                    c.setStrokeColor(colors.red)
                                                    h_mm = block.get('height', 150) * mm / 3.78
                                                    c.rect(x_mm, y_mm - h_mm, w_mm, h_mm)
                                                    c.setFont("Helvetica", 8)
                                                    c.drawString(x_mm + 5, y_mm - h_mm/2, f"Erreur: {str(e)[:40]}")
                                            else:
                                                # Fichier non trouvé - afficher le chemin complet pour debug
                                                c.setStrokeColor(colors.orange)
                                                h_mm = block.get('height', 150) * mm / 3.78
                                                c.rect(x_mm, y_mm - h_mm, w_mm, h_mm)
                                                c.setFont("Helvetica", 6)
                                                c.drawString(x_mm + 2, y_mm - h_mm/2 + 5, f"Introuvable:")
                                                c.drawString(x_mm + 2, y_mm - h_mm/2 - 5, str(logo_path)[:50])
                                    
                                    c.restoreState()
                                
                                c.save()
                                notify_success(f'PDF généré : {pdf_path.name}')
                                
                                # Ouvrir le PDF
                                os.startfile(str(pdf_path))
                            except Exception as e:
                                notify_error(f'Erreur lors de la génération du PDF : {str(e)}')
                        
                        # Créer une fenêtre de prévisualisation
                        with ui.dialog() as preview_dialog, ui.card().style('width: 900px; max-width: 95vw; padding: 20px;'):
                            # En-tête avec titre et boutons
                            with ui.row().classes('w-full items-center justify-between mb-4'):
                                ui.label('Aperçu PDF').classes('text-2xl font-bold')
                                with ui.row().classes('gap-2'):
                                    ui.button('Fermer', icon='close', on_click=preview_dialog.close).props('flat')
                                    ui.button('Générer PDF', icon='picture_as_pdf', on_click=generate_pdf_with_demo).props('color=primary')
                            
                            # Conteneur pour l'aperçu
                            with ui.column().classes('w-full').style('background: white; border: 1px solid #ddd;'):
                                # Créer le HTML de l'aperçu avec les blocs positionnés
                                preview_html = '''
                                <div style="width: 794px; height: 1123px; position: relative; background: white; margin: 0 auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                                '''
                                
                                for block in result['blocks']:
                                    block_type = block.get('type', '')
                                    x = block.get('x', 0)
                                    y = block.get('y', 0)
                                    width = block.get('width', 200)
                                    
                                    # Générer le contenu selon le type de bloc avec vraies données
                                    content = ''
                                    if block_type == 'adresse_entreprise':
                                        content = f'<div style="font-size: 11px; line-height: 1.4;"><strong>{org.nom or "MON ENTREPRISE"}</strong><br>{org.adresse or ""}<br>{org.cp or ""} {org.ville or ""}<br>Tél: {org.telephone or ""}<br>Email: {org.email or ""}</div>'
                                    elif block_type == 'titre':
                                        content = '<div style="font-size: 28px; font-weight: bold; text-align: center; color: #333;">DEVIS</div>'
                                    elif block_type == 'texte':
                                        content = '<div style="font-size: 11px; line-height: 1.5;">Texte libre à personnaliser...</div>'
                                    elif block_type == 'client':
                                        if client:
                                            content = f'<div style="font-size: 11px; line-height: 1.4;">{client.prenom or ""} {client.nom or ""}<br>{client.entreprise or ""}<br>{client.adresse or ""}<br>{client.cp or ""} {client.ville or ""}</div>'
                                        else:
                                            content = '<div style="font-size: 11px; line-height: 1.4;">Client<br>Nom du client<br>Adresse<br>Code postal Ville</div>'
                                    elif block_type == 'infos_devis':
                                        if demo_devis or selected:
                                            devis_data = demo_devis or selected
                                            content = f'<div style="font-size: 10px; line-height: 1.5;"><strong>Ref:</strong> {devis_data.numero}<br><strong>Date:</strong> {devis_data.date}</div>'
                                        else:
                                            content = '<div style="font-size: 10px; line-height: 1.5;"><strong>Ref:</strong> DEV-2025-XXXX<br><strong>Date:</strong> 15/12/2025</div>'
                                    elif block_type == 'objet':
                                        if demo_devis and demo_devis.objet:
                                            content = f'<div style="font-size: 12px; font-weight: bold;">Objet: {demo_devis.objet}</div>'
                                        else:
                                            content = '<div style="font-size: 12px; font-weight: bold;">Objet: Description des travaux</div>'
                                    elif block_type == 'tableau_ouvrages':
                                        content = '<div style="font-size: 9px; border: 1px solid #ddd; padding: 8px; background: #fafafa;"><strong>DÉTAIL DES OUVRAGES</strong><br><br>Réf | Désignation | Qté | P.U. | Total<br>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br>[Les lignes du devis]</div>'
                                    elif block_type == 'totaux':
                                        if demo_devis:
                                            totals = demo_devis.calculate_totals()
                                            content = f'<div style="font-size: 11px; text-align: right; line-height: 1.8;"><div style="border-top: 1px solid #ddd; padding-top: 8px;"><strong>Total HT:</strong> {totals["ht"]:.2f} €<br><strong>TVA ({demo_devis.tva}%):</strong> {totals["tva"]:.2f} €<br><div style="font-size: 14px; margin-top: 4px;"><strong>Total TTC:</strong> {totals["ttc"]:.2f} €</div></div></div>'
                                        else:
                                            content = '<div style="font-size: 11px; text-align: right; line-height: 1.8;"><div style="border-top: 1px solid #ddd; padding-top: 8px;"><strong>Total HT:</strong> 0.00 €<br><strong>TVA (20%):</strong> 0.00 €<br><div style="font-size: 14px; margin-top: 4px;"><strong>Total TTC:</strong> 0.00 €</div></div></div>'
                                    elif block_type == 'conditions':
                                        if demo_devis and demo_devis.conditions:
                                            content = f'<div style="font-size: 9px; line-height: 1.5;"><strong>CONDITIONS GÉNÉRALES</strong><br><br>{demo_devis.conditions[:200]}</div>'
                                        else:
                                            content = '<div style="font-size: 9px; line-height: 1.5;"><strong>CONDITIONS GÉNÉRALES</strong><br><br>Paiement: 30% à la commande, 40% à mi-parcours, 30% à la livraison<br>Délai de validité: 30 jours<br>Délai d\'exécution: à définir</div>'
                                    elif block_type == 'signature':
                                        content = '<div style="font-size: 10px; display: flex; justify-content: space-between; gap: 40px;"><div style="text-align: center;"><strong>Signature du client</strong><br><br>Date: ___________<br><br>________________</div><div style="text-align: center;"><strong>Signature entreprise</strong><br><br>Date: ___________<br><br>________________</div></div>'
                                    elif block_type == 'logo' and block.get('logoPath'):
                                        content = f'<img src="{block["logoPath"]}" style="width: 100%; height: 100%; object-fit: contain;" />'
                                    
                                    preview_html += f'''
                                    <div style="position: absolute; left: {x}px; top: {y}px; width: {width}px; border: 1px solid #e0e0e0; padding: 8px; background: white;">
                                        {content}
                                    </div>
                                    '''
                                
                                preview_html += '</div>'
                                
                                ui.html(preview_html, sanitize=False)
                        
                        preview_dialog.open()
                    
                    # Ajouter les boutons dans la barre d'actions
                    with actions_row:
                        ui.button('Nouveau', icon='add', on_click=new_template).props('flat')
                        ui.button('Charger', icon='folder_open', on_click=load_template).props('flat')
                        ui.button('Enregistrer', icon='save', on_click=save_template).props('flat color=primary')
                        ui.button('Enregistrer sous...', icon='save_as', on_click=save_as_template).props('flat')
                        ui.button('Aperçu PDF', icon='preview', on_click=preview_pdf).props('flat color=secondary')
                        ui.button('Tout effacer', icon='delete', on_click=lambda: ui.run_javascript('window.clearAll()')).props('flat color=negative')
            
            # Colonne droite : Page A4
            with ui.column().classes('flex-1 items-center').style('background: #e5e7eb; padding: 40px; border-radius: 8px; min-height: 1100px;'):
                with ui.row().classes('items-center gap-2 mb-4'):
                    ui.icon('description', size='md').classes('text-gray-700')
                    ui.label('Page A4 - Format d\'impression').classes('text-lg font-semibold')
                
                # Page A4 avec drag and drop - utiliser HTML brut pour éviter les problèmes NiceGUI
                a4_page = ui.html('''
                    <div class="a4-page" id="a4-canvas" style="width: 210mm; height: 297mm; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); position: relative; overflow: visible; margin: 0 auto;">
                        <div style="position: absolute; top: 10px; left: 10px; font-size: 12px; color: #999;">Glissez les blocs ici</div>
                    </div>
                ''', sanitize=False)
                
                # Définir d'abord les fonctions globales (avant l'initialisation)
                ui.timer(0.3, lambda: ui.run_javascript('''
                    if (!window.editorFunctionsLoaded) {
                        window.editorFunctionsLoaded = true;
                        window.draggedBlockType = null;
                        window.blocks = [];
                        window.blockIdCounter = 0;
                        
                        window.createBlock = function(type, x, y) {
                            const blockId = window.blockIdCounter++;
                            const page = document.getElementById('a4-canvas');
                            if (!page) {
                                console.error('❌ Cannot create block - page not found');
                                return;
                            }
                            
                            console.log('🔨 Creating block', blockId, 'type:', type);
                            
                            const block = document.createElement('div');
                            block.className = 'dropped-block';
                            block.dataset.blockId = blockId;
                            block.dataset.blockType = type;
                            // Utiliser directement x et y (l'offset est appliqué uniquement lors du drop, pas lors du chargement)
                            block.style.left = Math.max(0, x) + 'px';
                            block.style.top = Math.max(0, y) + 'px';
                            block.style.width = '200px';
                            
                            let content = '';
                            switch(type) {
                                case 'adresse_entreprise':
                                    content = '<div style="font-size: 11px; line-height: 1.4;"><strong>Mon Entreprise</strong><br>123 rue Example<br>75001 Paris<br>T&eacute;l: 01 23 45 67 89<br>contact@entreprise.fr</div>';
                                    block.style.width = '250px';
                                    break;
                                case 'titre':
                                    content = '<div style="font-size: 28px; font-weight: bold; text-align: center; color: #333;">DEVIS</div>';
                                    block.style.width = '500px';
                                    break;
                                case 'texte':
                                    content = '<div style="font-size: 11px; line-height: 1.5;">Texte libre &agrave; personnaliser...</div>';
                                    block.style.width = '400px';
                                    break;
                                case 'client':
                                    content = '<div style="font-size: 11px; line-height: 1.4;"><strong>Client</strong><br>Nom du client<br>Adresse<br>Code postal Ville</div>';
                                    block.style.width = '250px';
                                    break;
                                case 'infos_devis':
                                    content = '<div style="font-size: 10px; line-height: 1.5;"><strong>R&eacute;f&eacute;rence:</strong> DEV-2024-001<br><strong>Date:</strong> 15/12/2024</div>';
                                    block.style.width = '220px';
                                    break;
                                case 'objet':
                                    content = '<div style="font-size: 12px; font-weight: bold;">Objet: Description des travaux</div>';
                                    block.style.width = '600px';
                                    break;
                                case 'tableau_ouvrages':
                                    content = '<div style="font-size: 9px; border: 1px solid #ddd; padding: 8px; background: #fafafa;"><strong>D&Eacute;TAIL DES OUVRAGES</strong><br><br>R&eacute;f | D&eacute;signation | Qt&eacute; | P.U. | Total<br>&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;<br>[Les lignes seront ins&eacute;r&eacute;es ici]</div>';
                                    block.style.width = '650px';
                                    block.style.minHeight = '200px';
                                    break;
                                case 'totaux':
                                    content = '<div style="font-size: 11px; text-align: right; line-height: 1.8;"><div style="border-top: 1px solid #ddd; padding-top: 8px;"><strong>Total HT:</strong> 0.00 &euro;<br><strong>TVA (20%):</strong> 0.00 &euro;<br><div style="font-size: 14px; margin-top: 4px;"><strong>Total TTC:</strong> 0.00 &euro;</div></div></div>';
                                    block.style.width = '250px';
                                    break;
                                case 'conditions':
                                    content = '<div style="font-size: 9px; line-height: 1.5;"><strong>CONDITIONS G&Eacute;N&Eacute;RALES</strong><br><br>Paiement: 30% &agrave; la commande, 40% &agrave; mi-parcours, 30% &agrave; la livraison<br>D&eacute;lai de validit&eacute;: 30 jours<br>D&eacute;lai d&apos;ex&eacute;cution: &agrave; d&eacute;finir</div>';
                                    block.style.width = '500px';
                                    break;
                                case 'signature':
                                    content = '<div style="font-size: 10px; display: flex; justify-content: space-between; gap: 40px;"><div style="text-align: center;"><strong>Signature du client</strong><br><br>Date: ___________<br><br>________________</div><div style="text-align: center;"><strong>Signature entreprise</strong><br><br>Date: ___________<br><br>________________</div></div>';
                                    block.style.width = '500px';
                                    break;
                                case 'logo':
                                    content = '<div style="text-align: center; padding: 20px; border: 2px dashed #ccc; background: #fafafa;"><span class="material-icons" style="font-size: 48px; color: #999;">image</span><br><span style="font-size: 11px; color: #666;">Cliquez pour s&eacute;lectionner un logo</span></div>';
                                    block.style.width = '200px';
                                    block.style.height = '150px';
                                    block.dataset.logoPath = '';
                                    break;
                            }
                            
                            block.innerHTML = content;
                            
                            const controls = document.createElement('div');
                            controls.className = 'block-controls';
                            
                            const editBtn = document.createElement('button');
                            editBtn.className = 'control-btn';
                            editBtn.title = 'Editer';
                            editBtn.textContent = '\\u270F\\uFE0F';
                            editBtn.addEventListener('click', () => {
                                if (type === 'logo') {
                                    // Pour le logo, ouvrir le sélecteur de fichier
                                    window.selectLogoFile(blockId);
                                } else {
                                    alert('Edition du bloc ' + blockId + ' - Fonctionnalite a venir');
                                }
                            });
                            
                            const deleteBtn = document.createElement('button');
                            deleteBtn.className = 'control-btn';
                            deleteBtn.title = 'Supprimer';
                            deleteBtn.textContent = '\\uD83D\\uDDD1\\uFE0F';
                            deleteBtn.addEventListener('click', () => {
                                if (confirm('Supprimer ce bloc ?')) {
                                    block.remove();
                                    window.blocks = window.blocks.filter(b => b.id !== blockId);
                                }
                            });
                            
                            controls.appendChild(editBtn);
                            controls.appendChild(deleteBtn);
                            block.appendChild(controls);
                            
                            const resizeHandle = document.createElement('div');
                            resizeHandle.className = 'resize-handle';
                            block.appendChild(resizeHandle);
                            
                            window.makeDraggable(block);
                            window.makeResizable(block, resizeHandle);
                            
                            page.appendChild(block);
                            
                            window.blocks.push({
                                id: blockId,
                                type: type,
                                x: parseInt(block.style.left),
                                y: parseInt(block.style.top),
                                width: parseInt(block.style.width)
                            });
                            
                            console.log('✅ Block', blockId, 'created at', block.style.left, block.style.top);
                            console.log('📊 Total blocks:', window.blocks.length);
                        };
                        
                        window.makeDraggable = function(element) {
                            let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
                            
                            element.onmousedown = function dragMouseDown(e) {
                                if (e.target.className === 'resize-handle' || e.target.className === 'control-btn') return;
                                e.preventDefault();
                                pos3 = e.clientX;
                                pos4 = e.clientY;
                                document.onmouseup = closeDragElement;
                                document.onmousemove = elementDrag;
                                
                                document.querySelectorAll('.dropped-block').forEach(b => b.classList.remove('selected'));
                                element.classList.add('selected');
                            };
                            
                            function elementDrag(e) {
                                e.preventDefault();
                                pos1 = pos3 - e.clientX;
                                pos2 = pos4 - e.clientY;
                                pos3 = e.clientX;
                                pos4 = e.clientY;
                                
                                const newTop = element.offsetTop - pos2;
                                const newLeft = element.offsetLeft - pos1;
                                
                                const page = document.getElementById('a4-canvas');
                                const maxTop = page.clientHeight - element.offsetHeight;
                                const maxLeft = page.clientWidth - element.offsetWidth;
                                
                                element.style.top = Math.max(0, Math.min(newTop, maxTop)) + "px";
                                element.style.left = Math.max(0, Math.min(newLeft, maxLeft)) + "px";
                            }
                            
                            function closeDragElement() {
                                document.onmouseup = null;
                                document.onmousemove = null;
                                
                                // Mettre a jour la position dans window.blocks
                                const blockId = parseInt(element.dataset.blockId);
                                const blockData = window.blocks.find(b => b.id === blockId);
                                if (blockData) {
                                    blockData.x = parseInt(element.style.left);
                                    blockData.y = parseInt(element.style.top);
                                }
                            }
                        };
                        
                        window.makeResizable = function(element, handle) {
                            let startX, startWidth;
                            
                            handle.onmousedown = function initResize(e) {
                                e.stopPropagation();
                                e.preventDefault();
                                startX = e.clientX;
                                startWidth = parseInt(element.style.width);
                                document.onmousemove = doResize;
                                document.onmouseup = stopResize;
                            };
                            
                            function doResize(e) {
                                const newWidth = startWidth + (e.clientX - startX);
                                element.style.width = Math.max(100, newWidth) + 'px';
                            }
                            
                            function stopResize() {
                                document.onmousemove = null;
                                document.onmouseup = null;
                                
                                // Mettre a jour la largeur dans window.blocks
                                const blockId = parseInt(element.dataset.blockId);
                                const blockData = window.blocks.find(b => b.id === blockId);
                                if (blockData) {
                                    blockData.width = parseInt(element.style.width);
                                }
                            }
                        };
                        
                        window.selectLogoFile = function(blockId) {
                            // Appeler la fonction Python pour ouvrir le dialogue
                            emitEvent('select_logo_for_block', blockId);
                        };
                        
                        window.saveTemplate = function() {
                            // Mettre a jour les positions actuelles de tous les blocs
                            const allBlocks = [];
                            document.querySelectorAll('.dropped-block').forEach(blockEl => {
                                const blockId = parseInt(blockEl.dataset.blockId);
                                const blockType = blockEl.dataset.blockType;
                                const blockInfo = {
                                    id: blockId,
                                    type: blockType,
                                    x: parseInt(blockEl.style.left),
                                    y: parseInt(blockEl.style.top),
                                    width: parseInt(blockEl.style.width),
                                    height: blockEl.offsetHeight
                                };
                                // Sauvegarder le logo si c'est un bloc logo
                                if (blockType === 'logo' && blockEl.dataset.logoPath) {
                                    blockInfo.logoPath = blockEl.dataset.logoPath;
                                }
                                allBlocks.push(blockInfo);
                            });
                            
                            window.blocks = allBlocks;
                            console.log('Template saved:', allBlocks);
                            
                            // Retourner les donnees pour Python
                            return {
                                blocks: allBlocks,
                                timestamp: new Date().toISOString()
                            };
                        };
                        
                        window.loadTemplate = function(templateData) {
                            // Effacer tous les blocs existants
                            document.querySelectorAll('.dropped-block').forEach(b => b.remove());
                            window.blocks = [];
                            window.blockIdCounter = 0;
                            
                            // Recreer les blocs depuis le template
                            if (templateData && templateData.blocks) {
                                templateData.blocks.forEach(blockData => {
                                    window.createBlock(blockData.type, blockData.x, blockData.y);
                                    // Ajuster la largeur si specifiee
                                    const lastBlock = document.querySelector('[data-block-id="' + (window.blockIdCounter - 1) + '"]');
                                    if (lastBlock && blockData.width) {
                                        lastBlock.style.width = blockData.width + 'px';
                                    }
                                    // Restaurer le logo si c'est un bloc logo
                                    if (blockData.type === 'logo' && blockData.logoPath && lastBlock) {
                                        lastBlock.dataset.logoPath = blockData.logoPath;
                                        lastBlock.innerHTML = '<img src="' + blockData.logoPath + '" style="width: 100%; height: 100%; object-fit: contain;" />';
                                    }
                                });
                                console.log('Template loaded:', templateData.blocks.length, 'blocks');
                            }
                        };
                        
                        window.clearAll = function() {
                            if (confirm('Effacer tous les blocs ?')) {
                                document.querySelectorAll('.dropped-block').forEach(b => b.remove());
                                window.blocks = [];
                                window.blockIdCounter = 0;
                            }
                        };
                    }
                '''), once=True)
                
                # Initialiser le drag and drop après avoir défini les fonctions
                ui.timer(0.6, lambda: ui.run_javascript('''
                    if (!window.editorInitialized && window.createBlock) {
                        window.editorInitialized = true;
                        
                        const paletteBlocks = document.querySelectorAll('.palette-block');
                        const page = document.getElementById('a4-canvas');
                        
                        if (!page) {
                            console.error('A4 page not found');
                            return;
                        }
                        
                        console.log('Found', paletteBlocks.length, 'palette blocks and page');
                        
                        // Setup drag pour chaque bloc de palette
                        paletteBlocks.forEach(block => {
                            block.addEventListener('dragstart', (e) => {
                                window.draggedBlockType = block.getAttribute('data-block-type');
                                block.classList.add('dragging');
                                e.dataTransfer.effectAllowed = 'copy';
                                e.dataTransfer.setData('text/plain', window.draggedBlockType);
                                console.log('Drag started:', window.draggedBlockType);
                            });
                            
                            block.addEventListener('dragend', (e) => {
                                block.classList.remove('dragging');
                            });
                        });
                        
                        // Setup drop zone sur la page A4
                        page.addEventListener('dragover', (e) => {
                            e.preventDefault();
                            e.dataTransfer.dropEffect = 'copy';
                            page.style.backgroundColor = '#f9f9f9';
                        });
                        
                        page.addEventListener('dragleave', (e) => {
                            page.style.backgroundColor = 'white';
                        });
                        
                        page.addEventListener('drop', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            page.style.backgroundColor = 'white';
                            
                            const blockType = e.dataTransfer.getData('text/plain') || window.draggedBlockType;
                            
                            if (!blockType) {
                                console.log('No block type found');
                                return;
                            }
                            
                            const rect = page.getBoundingClientRect();
                            const rawX = e.clientX - rect.left;
                            const rawY = e.clientY - rect.top;
                            
                            // Appliquer l'offset pour centrer le bloc sous le curseur
                            const x = Math.max(0, rawX - 50);
                            const y = Math.max(0, rawY - 20);
                            
                            console.log('Drop at', x, y, 'type:', blockType);
                            window.createBlock(blockType, x, y);
                            
                            window.draggedBlockType = null;
                        });
                        
                        console.log('Drag and drop initialized');
                        
                        // Creer un bloc de test automatiquement
                        console.log('Creating test block...');
                        window.createBlock('titre', 150, 50);
                    }
                '''), once=True)
