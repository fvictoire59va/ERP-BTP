"""
Utilitaires et helpers pour l'UI
"""
from typing import Callable, Dict, Any, Optional
from nicegui import ui


# ============================================================================
# HANDLERS GÉNÉRIQUES
# ============================================================================

def create_closure_handler(callback: Callable, *args, **kwargs) -> Callable:
    """
    Crée un handler avec closure pour éviter les problèmes de scope
    Utile pour les boucles
    """
    def handler():
        return callback(*args, **kwargs)
    return handler


def create_value_change_handler(callback: Callable, field_data: Dict, key: str) -> Callable:
    """Crée un handler pour mettre à jour des données sur changement de valeur"""
    def handler():
        # Récupérer la valeur du field
        field_data[key] = getattr(handler._field, 'value', None)
        if callback:
            callback(field_data)
    return handler


# ============================================================================
# HELPERS DE VALIDATION
# ============================================================================

def validate_required(value: str, field_name: str = 'Champ') -> tuple[bool, str]:
    """Valide qu'un champ n'est pas vide"""
    if not value or not str(value).strip():
        return False, f"{field_name} est requis"
    return True, ""


def validate_positive_number(value: float, field_name: str = 'Valeur') -> tuple[bool, str]:
    """Valide qu'un nombre est positif"""
    try:
        num = float(value)
        if num <= 0:
            return False, f"{field_name} doit être positif"
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} doit être un nombre"


def validate_email(email: str) -> tuple[bool, str]:
    """Valide un format email simple"""
    if '@' not in email or '.' not in email:
        return False, "Email invalide"
    return True, ""


# ============================================================================
# HELPERS DE NOTIFICATION
# ============================================================================

def notify_success(message: str) -> None:
    """Affiche une notification de succès"""
    ui.notify(message, type='positive')


def notify_error(message: str) -> None:
    """Affiche une notification d'erreur"""
    ui.notify(message, type='negative')


def notify_info(message: str) -> None:
    """Affiche une notification d'info"""
    ui.notify(message, type='info')


def notify_warning(message: str) -> None:
    """Affiche une notification d'avertissement"""
    ui.notify(message, type='warning')


# ============================================================================
# HELPERS DE FORMATAGE
# ============================================================================

def format_currency(value: float, currency: str = 'EUR') -> str:
    """Formate un montant en devise"""
    return f"{value:.2f} {currency}"


def format_date(date_str: str) -> str:
    """Formate une date"""
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return date_str


def format_number(value: float, decimals: int = 2) -> str:
    """Formate un nombre"""
    return f"{value:.{decimals}f}"


# ============================================================================
# HELPERS DE TIMING
# ============================================================================

class DebounceTimer:
    """Utilitaire pour debouncer des actions (évite les appels multiples rapides)"""
    def __init__(self, wait_ms: int = 500):
        self.wait_ms = wait_ms
        self._timer = None
    
    def debounce(self, func: Callable):
        """Debounce une fonction"""
        def wrapper(*args, **kwargs):
            if self._timer:
                self._timer.stop()
            self._timer = ui.timer(
                self.wait_ms / 1000,
                lambda: func(*args, **kwargs),
                once=True
            )
        return wrapper
