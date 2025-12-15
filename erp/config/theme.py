"""
Système de thème pour l'application avec couleur d'accent personnalisable
"""

from dataclasses import dataclass

@dataclass
class Theme:
    """Configuration de thème avec couleur d'accent personnalisable"""
    # Couleur d'accent principale (rouge/orange par défaut)
    accent_color: str = "#c84c3c"  # Rouge/Orange Todoist
    
    # Couleurs secondaires
    primary_bg: str = "#ffffff"      # Blanc
    secondary_bg: str = "#f8f9fa"    # Gris très clair
    border_color: str = "#e0e0e0"    # Gris clair
    text_primary: str = "#1f2937"    # Gris foncé
    text_secondary: str = "#6b7280"  # Gris moyen
    
    @classmethod
    def default(cls):
        """Retourne le thème par défaut"""
        return cls()
    
    @classmethod
    def from_accent_color(cls, accent_color: str):
        """Crée un thème à partir d'une couleur d'accent"""
        return cls(accent_color=accent_color)
    
    def get_accent(self) -> str:
        """Retourne la couleur d'accent"""
        return self.accent_color
    
    def get_button_style(self) -> str:
        """Retourne le style CSS pour les boutons"""
        return f"background-color: {self.accent_color}; color: white;"
    
    def get_sidebar_style(self) -> str:
        """Retourne le style CSS pour la sidebar"""
        return f"background-color: {self.primary_bg}; border-right: 1px solid {self.border_color};"
    
    def get_card_style(self) -> str:
        """Retourne le style CSS pour les cards"""
        return f"background-color: {self.primary_bg}; border: 1px solid {self.border_color};"


# Thèmes prédéfinis
THEME_PRESETS = {
    "default": Theme(accent_color="#c84c3c"),      # Rouge/Orange Todoist
    "blue": Theme(accent_color="#3b82f6"),         # Bleu
    "green": Theme(accent_color="#10b981"),        # Vert
    "purple": Theme(accent_color="#8b5cf6"),       # Violet
    "pink": Theme(accent_color="#ec4899"),         # Rose
    "cyan": Theme(accent_color="#06b6d4"),         # Cyan
    "yellow": Theme(accent_color="#f59e0b"),       # Jaune/Orange
}

# Thème actif global
_active_theme = Theme.default()

def get_theme() -> Theme:
    """Retourne le thème actif"""
    # Charger depuis le storage utilisateur si disponible
    try:
        from nicegui import app
        saved_color = app.storage.user.get('theme_accent_color')
        if saved_color and saved_color != _active_theme.accent_color:
            _active_theme.accent_color = saved_color
    except:
        pass
    return _active_theme

def set_theme(theme: Theme):
    """Définit le thème actif"""
    global _active_theme
    _active_theme = theme

def set_accent_color(color: str, save_to_storage=True):
    """Définit la couleur d'accent du thème actif"""
    global _active_theme
    _active_theme.accent_color = color
    
    # Sauvegarder dans le storage utilisateur si demandé
    if save_to_storage:
        try:
            from nicegui import app
            app.storage.user['theme_accent_color'] = color
        except:
            pass

def set_theme_preset(preset_name: str):
    """Définit le thème à partir d'un préset"""
    if preset_name in THEME_PRESETS:
        global _active_theme
        _active_theme = THEME_PRESETS[preset_name]
