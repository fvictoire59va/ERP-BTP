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
    
    with ui.card().classes('w-full shadow-sm').style('padding: 24px; min-height: 800px; width: 100%;'):
        ui.label('Éditeur de mise en forme du devis').classes('text-3xl font-bold text-gray-900 mb-6')
        
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
                        {'type': 'totaux', 'icon': 'calculate', 'label': 'Totaux'},
                        {'type': 'conditions', 'icon': 'gavel', 'label': 'Conditions'},
                        {'type': 'signature', 'icon': 'draw', 'label': 'Signature'},
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
                    
                    ui.separator().classes('my-4')
                    
                    # Actions
                    ui.label('Actions').classes('text-lg font-bold mb-3')
                    
                    # Variable pour mémoriser le template actuellement chargé
                    current_template_name = {'value': None}
                    
                    # Afficher le nom du template actuel
                    current_template_label = ui.label('Aucun modèle chargé').classes('text-sm text-gray-600 mb-3 italic')
                    
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
                                            current_template_label.text = f'📝 Modèle: {template_name.value}'
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
                                current_template_label.text = f'📝 Modèle: {template_data["name"]}'
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
                                        current_template_label.text = f'📝 Modèle: {template_name.value}'
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
                        current_template_label.text = 'Aucun modèle chargé'
                        ui.run_javascript('window.clearAll()')
                        notify_info('Nouveau modèle créé')
                    
                    ui.button('💾 Enregistrer', on_click=save_template).props('flat color=primary').classes('w-full justify-start')
                    ui.button('💾 Enregistrer sous...', on_click=save_as_template).props('flat color=primary').classes('w-full justify-start')
                    ui.button('📂 Charger', on_click=load_template).props('flat').classes('w-full justify-start')
                    ui.button('📄 Nouveau', on_click=new_template).props('flat').classes('w-full justify-start')
                    ui.button('🗑️ Tout effacer', on_click=lambda: ui.run_javascript('window.clearAll()')).props('flat color=negative').classes('w-full justify-start')
            
            # Colonne droite : Page A4
            with ui.column().classes('flex-1 items-center').style('background: #e5e7eb; padding: 40px; border-radius: 8px; min-height: 1100px;'):
                ui.label('📄 Page A4 - Format d\'impression').classes('text-lg font-semibold mb-4')
                
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
                            block.style.left = Math.max(0, x - 50) + 'px';
                            block.style.top = Math.max(0, y - 20) + 'px';
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
                                    content = '<div style="font-size: 10px; line-height: 1.5;"><strong>Devis N&deg;:</strong> DEV-2024-001<br><strong>Date:</strong> 15/12/2024<br><strong>Validit&eacute;:</strong> 30 jours</div>';
                                    block.style.width = '220px';
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
                            }
                            
                            block.innerHTML = content;
                            
                            const controls = document.createElement('div');
                            controls.className = 'block-controls';
                            
                            const editBtn = document.createElement('button');
                            editBtn.className = 'control-btn';
                            editBtn.title = 'Editer';
                            editBtn.textContent = '\\u270F\\uFE0F';
                            editBtn.addEventListener('click', () => {
                                alert('Edition du bloc ' + blockId + ' - Fonctionnalite a venir');
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
                        
                        window.saveTemplate = function() {
                            // Mettre a jour les positions actuelles de tous les blocs
                            const allBlocks = [];
                            document.querySelectorAll('.dropped-block').forEach(blockEl => {
                                const blockId = parseInt(blockEl.dataset.blockId);
                                const blockType = blockEl.dataset.blockType;
                                allBlocks.push({
                                    id: blockId,
                                    type: blockType,
                                    x: parseInt(blockEl.style.left),
                                    y: parseInt(blockEl.style.top),
                                    width: parseInt(blockEl.style.width),
                                    height: blockEl.offsetHeight
                                });
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
                            const x = e.clientX - rect.left;
                            const y = e.clientY - rect.top;
                            
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
