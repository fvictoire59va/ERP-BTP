"""
Menu principal stylisé avec icônes Material Design
Reprend le style de l'image fournie et le style Todoist existant
"""
from nicegui import ui
from typing import Callable, Optional
from devis.config.theme import get_theme


# Ajouter le CSS global pour les boutons du menu
ui.add_head_html('''
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,100,0,-25" />
<style>
    /* Material Symbols configuration */
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        font-variation-settings:
            'FILL' 0,
            'wght' 100,
            'GRAD' -25,
            'opsz' 20;
    }
    
    /* Override des classes Quasar/Tailwind pour aligner à gauche */
    button.q-btn.w-full.text-left {
        text-align: left !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        text-transform: none !important;
    }
    
    button.q-btn.w-full.text-left .q-btn__content {
        justify-content: flex-start !important;
        text-align: left !important;
        padding-left: 16px !important;
        padding-right: 16px !important;
        margin: 0 !important;
        text-transform: none !important;
    }
    
    button.q-btn.w-full.text-left .q-btn__content.col {
        justify-content: flex-start !important;
    }
    
    button.q-btn.w-full.text-left .q-btn__content.row {
        justify-content: flex-start !important;
    }
    
    button.q-btn.w-full.text-left .q-btn__content span {
        text-align: left !important;
        justify-content: flex-start !important;
        margin: 0 !important;
        padding: 0 !important;
        text-transform: none !important;
    }
    
    button.q-btn.w-full.text-left .q-btn__content span.block {
        text-align: left !important;
        display: block !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        text-transform: none !important;
    }
    
    button.q-btn.w-full.text-left .q-focus-helper {
        display: none !important;
    }
</style>
''')

# Couleur du fond de l'image (beige/crème clair)
MENU_BG_COLOR = '#f5f1ec'  # Beige clair

# Icônes Material Symbols pour chaque option
MENU_ICONS = {
    'Recherche': 'search',
    'Boîte de réception': 'inbox',
    "Aujourd'hui": 'today',
    'Prochainement': 'event',
    'Filtres et étiquettes': 'label',
    'Archivé': 'archive',
    'Devis': 'description',
    'Ouvrages': 'construction',
    'Catalogue': 'inventory_2',
    'Clients': 'group',
    'Paramètres': 'settings',
    'Dashboard': 'dashboard',
    'Tableau de bord': 'dashboard',
    'Organisation': 'business',
    'Articles': 'category',
}


def create_styled_menu_button(
    label: str, 
    icon_key: str,
    on_click: Optional[Callable] = None,
    selected: bool = False
) -> ui.button:
    """
    Crée un bouton de menu stylisé avec icône
    
    Args:
        label: Texte du bouton
        icon_key: Clé pour récupérer l'icône
        on_click: Fonction à appeler au clic
        selected: Si le bouton est sélectionné
    
    Returns:
        Bouton stylisé
    """
    theme = get_theme()
    
    # Formater le texte: capital (première lettre en majuscule, reste en minuscule)
    formatted_label = label.capitalize() if label else label
    
    # Récupérer le nom de l'icône Material Symbol
    icon_name = MENU_ICONS.get(icon_key, 'circle')
    
    # Créer le bouton avec icône en utilisant le format Quasar
    btn = ui.button(formatted_label, icon=icon_name, on_click=on_click).props('flat align=left no-caps').classes('w-full text-left text-sm transition justify-start')
    
    # Appliquer les styles
    if selected:
        btn.style(f'''
            background-color: rgba({int(theme.accent_color[1:3], 16)}, {int(theme.accent_color[3:5], 16)}, {int(theme.accent_color[5:7], 16)}, 0.1) !important;
            border-left: 3px solid {theme.accent_color} !important;
            color: {theme.accent_color} !important;
            padding: 12px 16px 12px 0px !important;
            font-weight: normal !important;
            text-align: left !important;
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 44px !important;
            line-height: 1.4 !important;
            white-space: normal !important;
            text-transform: none !important;
        ''')
    else:
        btn.style(f'''
            background-color: transparent !important;
            color: #2c3e50 !important;
            border-left: 3px solid transparent !important;
            padding: 12px 16px 12px 0px !important;
            font-weight: normal !important;
            text-align: left !important;
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 44px !important;
            line-height: 1.4 !important;
            white-space: normal !important;
            text-transform: none !important;
        ''')
    
    # Ajouter les effets hover
    btn.on('mouseenter', lambda: btn.style(
        f'background-color: rgba({int(theme.accent_color[1:3], 16)}, {int(theme.accent_color[3:5], 16)}, {int(theme.accent_color[5:7], 16)}, 0.1) !important;'
    ) if not selected else None)
    
    btn.on('mouseleave', lambda: (
        btn.style(
            f'background-color: rgba({int(theme.accent_color[1:3], 16)}, {int(theme.accent_color[3:5], 16)}, {int(theme.accent_color[5:7], 16)}, 0.1) !important; color: {theme.accent_color} !important;'
        ) if selected else btn.style('background-color: transparent !important; color: #2c3e50 !important;')
    ))
    
    return btn


def create_main_menu(
    on_item_selected: Optional[Callable[[str], None]] = None,
    menu_items: Optional[list] = None
) -> ui.element:
    """
    Crée un menu principal stylisé inspiré de Todoist
    
    Args:
        on_item_selected: Callback fonction appelée quand un item est sélectionné
        menu_items: Liste personnalisée d'items du menu. 
                    Format: [('label', 'icon_name'), ...]
                    Si None, utilise les items par défaut
    
    Returns:
        ui.column contenant le menu
    """
    
    # Items par défaut du menu
    default_items = [
        ('Recherche', 'Recherche'),
        ('Boîte de réception', 'Boîte de réception'),
        ("Aujourd'hui", "Aujourd'hui"),
        ('Prochainement', 'Prochainement'),
        ('Filtres et étiquettes', 'Filtres et étiquettes'),
        ('Archivé', 'Archivé'),
    ]
    
    items = menu_items if menu_items is not None else default_items
    
    # Conteneur principal du menu
    menu_container = ui.column().classes('w-64 h-screen flex flex-col gap-0')
    menu_container.style(f'background-color: {MENU_BG_COLOR}; padding: 0;')
    
    # État pour tracker l'item sélectionné
    selected_item = {'value': None}
    menu_buttons = {}
    
    with menu_container:
        # Section items du menu
        items_container = ui.column().classes('flex-1 gap-0 overflow-y-auto p-0')
        items_container.style('background-color: transparent;')
        
        def on_menu_item_click(label: str):
            """Gère le clic sur un item du menu"""
            theme = get_theme()
            
            # Désélectionner l'ancien item
            if selected_item['value'] and selected_item['value'] in menu_buttons:
                old_btn = menu_buttons[selected_item['value']]
                old_btn.style(f'''
                    background-color: transparent !important;
                    color: #2c3e50 !important;
                    border-left: 3px solid transparent !important;
                    padding: 12px 16px 12px 0px !important;
                    font-weight: normal !important;
                    text-align: left !important;
                    display: block !important;
                    width: 100% !important;
                    height: auto !important;
                    min-height: 44px !important;
                    line-height: 1.4 !important;
                    white-space: normal !important;
                    text-transform: none !important;
                ''')
            
            # Sélectionner le nouvel item
            selected_item['value'] = label
            new_btn = menu_buttons[label]
            new_btn.style(f'''
                background-color: rgba({int(theme.accent_color[1:3], 16)}, {int(theme.accent_color[3:5], 16)}, {int(theme.accent_color[5:7], 16)}, 0.1) !important;
                border-left: 3px solid {theme.accent_color} !important;
                color: {theme.accent_color} !important;
                padding: 12px 16px 12px 0px !important;
                font-weight: normal !important;
                text-align: left !important;
                display: block !important;
                width: 100% !important;
                height: auto !important;
                min-height: 44px !important;
                line-height: 1.4 !important;
                white-space: normal !important;
                text-transform: none !important;
            ''')
            
            # Appeler le callback si fourni
            if on_item_selected:
                on_item_selected(label)
        
        # Créer les items du menu
        with items_container:
            for display_label, icon_key in items:
                btn = create_styled_menu_button(
                    display_label,
                    icon_key,
                    on_click=lambda l=display_label: on_menu_item_click(l),
                    selected=False
                )
                menu_buttons[display_label] = btn
    
    return menu_container


def create_menu_with_sections(
    on_item_selected: Optional[Callable[[str], None]] = None,
    sections: Optional[dict] = None
) -> ui.element:
    """
    Crée un menu avec sections et sous-items
    
    Args:
        on_item_selected: Callback fonction
        sections: Dict avec structure:
                  {
                      'Nom Section': [
                          ('Item 1', 'icon_key'),
                          ('Item 2', 'icon_key'),
                      ]
                  }
    
    Returns:
        ui.column contenant le menu sectionnalisé
    """
    
    theme = get_theme()
    
    # Sections par défaut
    default_sections = {
        'Navigation': [
            ('Recherche', 'Recherche'),
            ('Boîte de réception', 'Boîte de réception'),
        ],
        'Vues': [
            ("Aujourd'hui", "Aujourd'hui"),
            ('Prochainement', 'Prochainement'),
            ('Filtres et étiquettes', 'Filtres et étiquettes'),
        ],
        'Archive': [
            ('Archivé', 'Archivé'),
        ],
    }
    
    sections = sections if sections is not None else default_sections
    
    # Conteneur principal
    menu_container = ui.column().classes('w-64 h-screen flex flex-col gap-0 overflow-y-auto')
    menu_container.style(f'background-color: {MENU_BG_COLOR}; padding: 0;')
    
    selected_item = {'value': None}
    menu_buttons = {}
    
    def on_menu_item_click(label: str):
        """Gère le clic"""
        theme_local = get_theme()
        
        # Désélectionner l'ancien item
        if selected_item['value'] and selected_item['value'] in menu_buttons:
            old_btn = menu_buttons[selected_item['value']]
            old_btn.style(f'''
                background-color: transparent !important;
                color: #2c3e50 !important;
                border-left: 3px solid transparent !important;
                padding: 12px 16px 12px 0px !important;
                font-weight: normal !important;
                text-align: left !important;
                display: block !important;
                width: 100% !important;
                height: auto !important;
                min-height: 44px !important;
                line-height: 1.4 !important;
                white-space: normal !important;
                text-transform: none !important;
            ''')
        
        # Sélectionner le nouvel item
        selected_item['value'] = label
        new_btn = menu_buttons[label]
        new_btn.style(f'''
            background-color: rgba({int(theme_local.accent_color[1:3], 16)}, {int(theme_local.accent_color[3:5], 16)}, {int(theme_local.accent_color[5:7], 16)}, 0.1) !important;
            border-left: 3px solid {theme_local.accent_color} !important;
            color: {theme_local.accent_color} !important;
            padding: 12px 16px 12px 0px !important;
            font-weight: normal !important;
            text-align: left !important;
            display: block !important;
            width: 100% !important;
            height: auto !important;
            min-height: 44px !important;
            line-height: 1.4 !important;
            white-space: normal !important;
            text-transform: none !important;
        ''')
        
        if on_item_selected:
            on_item_selected(label)
    
    # Créer les sections
    with menu_container:
        for section_name, items in sections.items():
            # Titre de section
            section_title = ui.label(section_name).classes('px-4 py-3 text-sm')
            section_title.style(f'color: {theme.text_secondary}; background-color: transparent;')
            
            # Items de la section
            for display_label, icon_key in items:
                btn = create_styled_menu_button(
                    display_label,
                    icon_key,
                    on_click=lambda l=display_label: on_menu_item_click(l),
                    selected=False
                )
                menu_buttons[display_label] = btn
    
    return menu_container
