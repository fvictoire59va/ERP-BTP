"""
Configuration module - Application configuration and themes
"""
from erp.config.theme import (
    Theme,
    get_theme,
    set_theme,
    set_accent_color,
    set_theme_preset,
    THEME_PRESETS,
)

__all__ = [
    'Theme',
    'get_theme',
    'set_theme',
    'set_accent_color',
    'set_theme_preset',
    'THEME_PRESETS',
]
