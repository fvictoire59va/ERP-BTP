"""
UI module - User interface components and application
"""
from erp.ui.app import DevisApp
from erp.ui.components import (
    create_input_field,
    create_number_field,
    create_textarea_field,
    create_select_field,
    create_edit_dialog,
    create_form_row,
)
from erp.ui.menu import create_main_menu, MENU_ICONS
from erp.ui.styles import get_consolidated_styles
from erp.ui.utils import (
    notify_success,
    notify_error,
    notify_warning,
    notify_info,
)

__all__ = [
    'DevisApp',
    'create_input_field',
    'create_number_field',
    'create_textarea_field',
    'create_select_field',
    'create_edit_dialog',
    'create_form_row',
    'create_main_menu',
    'MENU_ICONS',
    'get_consolidated_styles',
    'notify_success',
    'notify_error',
    'notify_warning',
    'notify_info',
]
