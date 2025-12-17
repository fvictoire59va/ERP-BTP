"""
Panel de gestion des catégories et sous-catégories en arbre

Permet de créer, modifier et supprimer les catégories et sous-catégories d'articles.
Structure en arbre: catégories mères -> sous-catégories filles
"""

from nicegui import ui
from erp.ui.utils import notify_success, notify_error
import json
from pathlib import Path


def create_categories_panel(app_instance):
    """Crée le panneau de gestion des catégories et sous-catégories
    
    Args:
        app_instance: Instance de DevisApp contenant dm et autres état
    """
    
    # Fichier pour stocker les catégories
    categories_file = Path('data') / 'categories.json'
    
    def load_categories():
        """Charge les catégories depuis le fichier"""
        if categories_file.exists():
            with open(categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Structure par défaut en arbre
            return [
                {
                    'id': 'general',
                    'label': 'Général',
                    'children': []
                },
                {
                    'id': 'platrerie',
                    'label': 'Plâtrerie',
                    'children': []
                },
                {
                    'id': 'menuiserie_int',
                    'label': 'Menuiserie Intérieure',
                    'children': []
                },
                {
                    'id': 'menuiserie_ext',
                    'label': 'Menuiserie Extérieure',
                    'children': []
                },
                {
                    'id': 'isolation',
                    'label': 'Isolation',
                    'children': []
                },
                {
                    'id': 'peinture',
                    'label': 'Peinture',
                    'children': []
                }
            ]
    
    def save_categories(categories_data):
        """Sauvegarde les catégories dans le fichier"""
        categories_file.parent.mkdir(exist_ok=True)
        with open(categories_file, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, ensure_ascii=False, indent=2)
    
    categories_data = load_categories()
    selected_node = {'value': None}
    tree_widget = {'ref': None}
    
    def find_node_by_id(nodes, node_id):
        """Trouve un nœud dans l'arbre par son ID"""
        for node in nodes:
            if node['id'] == node_id:
                return node
            if node.get('children'):
                found = find_node_by_id(node['children'], node_id)
                if found:
                    return found
        return None
    
    def find_parent_node(nodes, child_id, parent=None):
        """Trouve le parent d'un nœud"""
        for node in nodes:
            if node.get('children'):
                for child in node['children']:
                    if child['id'] == child_id:
                        return node
                found = find_parent_node(node['children'], child_id, node)
                if found:
                    return found
        return None
    
    def build_tree_structure():
        """Construit la structure pour ui.tree"""
        tree_nodes = []
        for cat in categories_data:
            tree_nodes.append({
                'id': cat['id'],
                'label': cat['label'],
                'children': cat.get('children', [])
            })
        return tree_nodes
    
    def refresh_tree():
        """Rafraîchit l'affichage de l'arbre"""
        nonlocal tree_widget
        if tree_widget['ref']:
            tree_widget['ref'].delete()
        
        with tree_container:
            tree_widget['ref'] = ui.tree(
                build_tree_structure(),
                label_key='label',
                on_select=lambda e: on_node_select(e.value)
            ).classes('w-full')
    
    def on_node_select(node_id):
        """Gère la sélection d'un nœud"""
        selected_node['value'] = node_id
        node_data = find_node_by_id(categories_data, node_id)
        
        if node_data:
            detail_container.clear()
            with detail_container:
                with ui.card().classes('w-full p-4'):
                    ui.label('Détails de la catégorie').classes('text-xl font-bold mb-4')
                    
                    with ui.column().classes('gap-3 w-full'):
                        ui.label(f"Nom: {node_data['label']}").classes('text-lg font-medium')
                        ui.label(f"ID: {node_data['id']}").classes('text-sm text-gray-500')
                        
                        parent = find_parent_node(categories_data, node_id)
                        if parent:
                            ui.label(f"Catégorie parente: {parent['label']}").classes('text-sm text-gray-600')
                        
                        with ui.row().classes('gap-2 mt-4'):
                            def on_modify_click():
                                def save_category_update(values):
                                    node = find_node_by_id(categories_data, node_id)
                                    if node:
                                        node['label'] = values.get('nom', '')
                                        save_categories(categories_data)
                                        notify_success('Catégorie mise à jour')
                                        refresh_tree()
                                        on_node_select(node_id)
                                
                                from erp.ui.components import create_edit_dialog
                                edit_dialog = create_edit_dialog(
                                    'Modifier la catégorie',
                                    fields=[
                                        {'type': 'input', 'label': 'Nom', 'value': node_data['label'], 'key': 'nom'},
                                    ],
                                    on_save=save_category_update
                                )
                                edit_dialog.open()
                            
                            ui.button('Modifier', on_click=on_modify_click).props('color=primary icon=edit')
                            ui.button('Supprimer', on_click=lambda: delete_node(node_id)).props('color=negative icon=delete')
                
                # Section pour ajouter une sous-catégorie (uniquement si c'est une catégorie principale)
                if not parent:
                    with ui.card().classes('w-full p-4 mt-4'):
                        ui.label('Ajouter une sous-catégorie').classes('text-lg font-bold mb-3')
                        with ui.row().classes('w-full gap-2 items-end'):
                            subcat_input = ui.input('Nom de la sous-catégorie', placeholder='Ex: Plaques de plâtre...').classes('flex-1')
                            
                            def add_subcategory():
                                if not subcat_input.value:
                                    notify_error('Veuillez saisir un nom')
                                    return
                                
                                # Générer un ID unique
                                subcat_id = subcat_input.value.lower().replace(' ', '_').replace('é', 'e').replace('è', 'e').replace('à', 'a')
                                
                                # Vérifier si l'ID existe déjà
                                if find_node_by_id(categories_data, subcat_id):
                                    notify_error('Cette sous-catégorie existe déjà')
                                    return
                                
                                # Ajouter la sous-catégorie
                                if 'children' not in node_data:
                                    node_data['children'] = []
                                node_data['children'].append({
                                    'id': subcat_id,
                                    'label': subcat_input.value,
                                    'children': []
                                })
                                
                                save_categories(categories_data)
                                notify_success(f'Sous-catégorie "{subcat_input.value}" ajoutée')
                                subcat_input.value = ''
                                refresh_tree()
                            
                            ui.button('Ajouter', on_click=add_subcategory).props('color=primary')
    
    def add_category():
        """Ajoute une nouvelle catégorie"""
        name = new_cat_input.value
        if not name:
            notify_error('Veuillez saisir un nom')
            return
        
        # Générer un ID unique
        cat_id = name.lower().replace(' ', '_').replace('é', 'e').replace('è', 'e').replace('à', 'a')
        
        # Vérifier si l'ID existe déjà
        if find_node_by_id(categories_data, cat_id):
            notify_error('Cette catégorie existe déjà')
            return
        
        if selected_node['value']:
            # Ajouter comme sous-catégorie
            parent_node = find_node_by_id(categories_data, selected_node['value'])
            if parent_node:
                if 'children' not in parent_node:
                    parent_node['children'] = []
                parent_node['children'].append({
                    'id': cat_id,
                    'label': name,
                    'children': []
                })
                notify_success(f'Sous-catégorie "{name}" ajoutée')
        else:
            # Ajouter comme catégorie principale
            categories_data.append({
                'id': cat_id,
                'label': name,
                'children': []
            })
            notify_success(f'Catégorie "{name}" ajoutée')
        
        save_categories(categories_data)
        new_cat_input.value = ''
        refresh_tree()
    
    def update_node(node_id, new_label):
        """Met à jour un nœud"""
        node = find_node_by_id(categories_data, node_id)
        if node:
            node['label'] = new_label
            save_categories(categories_data)
            notify_success('Catégorie mise à jour')
            refresh_tree()
    
    def delete_node(node_id):
        """Supprime un nœud"""
        def remove_from_list(nodes, target_id):
            for i, node in enumerate(nodes):
                if node['id'] == target_id:
                    nodes.pop(i)
                    return True
                if node.get('children'):
                    if remove_from_list(node['children'], target_id):
                        return True
            return False
        
        if remove_from_list(categories_data, node_id):
            save_categories(categories_data)
            notify_success('Catégorie supprimée')
            selected_node['value'] = None
            refresh_tree()
            detail_container.clear()
        else:
            notify_error('Impossible de supprimer la catégorie')
    
    # Interface utilisateur
    with ui.card().classes('w-full shadow-sm').style('padding: 48px; min-height: 600px;'):
        ui.label('Gestion des Catégories').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Layout principal avec arbre et détails
        with ui.row().classes('w-full gap-6').style('min-height: 400px;'):
            # Arbre des catégories
            with ui.card().classes('shadow-sm').style('padding: 24px; flex: 1;'):
                ui.label('Arborescence').classes('text-xl font-bold mb-4')
                tree_container = ui.column().classes('w-full')
                
            # Détails de la catégorie sélectionnée
            detail_container = ui.column().classes('w-full').style('flex: 1;')
        
        # Initialiser l'arbre
        refresh_tree()
