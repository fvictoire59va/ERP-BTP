"""
Composants UI réutilisables et homogénéisés
"""
from nicegui import ui
from typing import List, Dict, Callable, Optional
from pathlib import Path


# ============================================================================
# COMPOSANTS FORMULAIRE STANDARD
# ============================================================================

def create_form_row(gap: str = 'gap-4', classes_extra: str = '') -> ui.element:
    """Crée une row standard pour formulaires"""
    return ui.row().classes(f'w-full {gap} {classes_extra}')


def create_input_field(
    label: str,
    value: str = '',
    placeholder: str = '',
    input_class: str = '',
    width_class: str = 'flex-1',
    **kwargs
) -> ui.element:
    """Crée un input homogénéisé avec style natif"""
    return ui.input(
        label,
        value=value,
        placeholder=placeholder
    ).classes(f'{width_class} {input_class}')


def create_number_field(
    label: str,
    value: float = 0,
    min_val: float = 0,
    step: float = 0.01,
    input_class: str = '',
    width_class: str = 'w-24',
    **kwargs
) -> ui.element:
    """Crée un number input homogénéisé"""
    return ui.number(
        label,
        value=value,
        min=min_val,
        step=step
    ).classes(f'{width_class} {input_class}')


def create_textarea_field(
    label: str,
    value: str = '',
    placeholder: str = '',
    rows: int = 2,
    input_class: str = '',
    width_class: str = 'flex-1',
    **kwargs
) -> ui.element:
    """Crée un textarea homogénéisé"""
    return ui.textarea(
        label,
        value=value,
        placeholder=placeholder
    ).classes(f'{width_class} {input_class}').props(f'rows={rows}')


def create_select_field(
    label: str,
    options: Dict,
    value: Optional[str] = None,
    select_class: str = '',
    width_class: str = 'flex-1',
    **kwargs
) -> ui.element:
    """Crée un select homogénéisé"""
    return ui.select(
        label=label,
        options=options,
        value=value
    ).classes(f'{width_class} {select_class}')


def create_date_field(
    label: str,
    value: str = '',
    input_class: str = '',
    width_class: str = 'flex-1',
    **kwargs
) -> ui.element:
    """Crée un champ date homogénéisé avec date picker"""
    date_input = ui.input(label, value=value).classes(f'{width_class} {input_class}')
    with date_input.add_slot('append'):
        ui.icon('event').classes('cursor-pointer')
    
    # Créer le menu avec le date picker
    with ui.menu().props('no-parent-event') as menu:
        with ui.date(value=value).bind_value(date_input).props('mask="YYYY-MM-DD"') as date_picker:
            # Fermer le menu après sélection
            date_picker.on('update:model-value', lambda: menu.close())
    
    # Ouvrir le menu au clic sur l'icône ou l'input
    date_input.on('click', menu.open)
    
    return date_input


# ============================================================================
# DIALOGS RÉUTILISABLES
# ============================================================================

def create_edit_dialog(
    title: str,
    fields: List[Dict],
    on_save: Callable,
    on_close: Optional[Callable] = None
) -> ui.element:
    """
    Crée une dialog d'édition standard
    
    Args:
        title: Titre de la dialog
        fields: Liste des champs [
            {'type': 'input', 'label': '...', 'value': '...', 'class': '...'},
            {'type': 'select', 'label': '...', 'options': {...}, 'value': '...'},
            {'type': 'number', 'label': '...', 'value': 0, 'min': 0, 'step': 0.01},
            ...
        ]
        on_save: Callback appelé à la sauvegarde avec dict des valeurs
        on_close: Callback optionnel à la fermeture
    
    Returns:
        Dialog element (call .open() pour l'afficher)
    """
    dialog = ui.dialog()
    
    with dialog:
        with ui.card().classes('w-full max-w-2xl'):
            ui.label(title).classes('text-xl font-bold mb-4')
            
            # Créer les champs dynamiquement
            field_inputs = {}
            with ui.column().classes('w-full gap-3'):
                for field in fields:
                    field_type = field.get('type', 'input')
                    field_label = field.get('label', '')
                    field_class = field.get('class', '')
                    field_key = field.get('key', field_label.lower().replace(' ', '_'))
                    
                    if field_type == 'input':
                        field_inputs[field_key] = create_input_field(
                            field_label,
                            value=field.get('value', ''),
                            placeholder=field.get('placeholder', ''),
                            input_class=field_class,
                            width_class='w-full'
                        )
                    elif field_type == 'textarea':
                        field_inputs[field_key] = create_textarea_field(
                            field_label,
                            value=field.get('value', ''),
                            rows=field.get('rows', 2),
                            input_class=field_class,
                            width_class='w-full'
                        )
                    elif field_type == 'select':
                        field_inputs[field_key] = create_select_field(
                            field_label,
                            options=field.get('options', {}),
                            value=field.get('value'),
                            select_class=field_class,
                            width_class='w-full'
                        )
                    elif field_type == 'number':
                        field_inputs[field_key] = create_number_field(
                            field_label,
                            value=field.get('value', 0),
                            min_val=field.get('min', 0),
                            step=field.get('step', 0.01),
                            input_class=field_class,
                            width_class='w-full'
                        )
                    elif field_type == 'date':
                        field_inputs[field_key] = create_date_field(
                            field_label,
                            value=field.get('value', ''),
                            input_class=field_class,
                            width_class='w-full'
                        )
            
            # Boutons
            with ui.row().classes('gap-2 justify-end mt-4'):
                def on_cancel():
                    dialog.close()
                    if on_close:
                        on_close()
                
                ui.button('Annuler', on_click=on_cancel).props('flat')
                
                def on_save_click():
                    # Récupérer les valeurs et appeler le callback
                    values = {key: field.value for key, field in field_inputs.items()}
                    on_save(values)
                    dialog.close()
                    if on_close:
                        on_close()
                
                ui.button('Enregistrer', on_click=on_save_click).classes('themed-button')
    
    return dialog


# ============================================================================
# HELPERS STANDARD
# ============================================================================

def create_card_header(title: str, subtitle: str = '') -> None:
    """Crée un header standard pour card"""
    ui.label(title).classes('font-semibold text-lg text-gray-800 mb-4')
    if subtitle:
        ui.label(subtitle).classes('text-sm text-gray-600')


def create_section_header(title: str, size: str = 'lg') -> None:
    """Crée un header de section standard"""
    size_classes = {
        'sm': 'text-lg font-semibold',
        'md': 'text-xl font-bold',
        'lg': 'text-2xl font-bold'
    }
    ui.label(title).classes(f'{size_classes.get(size, size_classes["lg"])} text-gray-900 mb-4')


def create_label_value_row(label: str, value: str, label_width: str = 'w-32') -> None:
    """Crée une row label-valeur standard"""
    with ui.row().classes('w-full items-center gap-4'):
        ui.label(label).classes(f'{label_width} font-medium text-gray-700')
        ui.label(value).classes('text-lg')
