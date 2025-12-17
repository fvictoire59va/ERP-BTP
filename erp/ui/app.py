from nicegui import ui
from datetime import datetime
from typing import List
from pathlib import Path

from erp.services.pdf_service import generate_pdf as generate_pdf_file
from erp.config.theme import get_theme, set_accent_color, THEME_PRESETS
from erp.ui.components import (
    create_input_field, create_number_field, create_textarea_field, 
    create_select_field, create_form_row, create_edit_dialog
)
from erp.ui.styles import CONSOLIDATED_STYLES, ROW_STANDARD, COLUMN_STANDARD
from erp.ui.utils import notify_success, notify_error, notify_info
from erp.ui.menu import create_main_menu, MENU_ICONS

from erp.core.models import (
    ComposantOuvrage,
    Ouvrage,
    LigneDevis,
    Devis,
)
from erp.core.data_manager import DataManager

# Imports des panels extraits
from erp.ui.panels.devis import create_devis_panel as panel_create_devis
from erp.ui.panels.ouvrages import create_ouvrages_panel as panel_create_ouvrages
from erp.ui.panels.catalogue import create_catalogue_panel as panel_create_catalogue
from erp.ui.panels.clients import create_clients_panel as panel_create_clients
from erp.ui.panels.parametres import create_parametres_panel as panel_create_parametres
from erp.ui.panels.projets import render_projets_panel as panel_create_projets
from erp.ui.panels.autres import (
    create_liste_devis_panel as panel_create_liste_devis,
    create_dashboard_panel as panel_create_dashboard,
    create_company_panel as panel_create_company
)
from erp.ui.panels.liste_articles import create_liste_articles_panel as panel_create_liste_articles
from erp.ui.panels.liste_ouvrages import create_liste_ouvrages_panel as panel_create_liste_ouvrages
from erp.ui.panels.editeur_devis import create_editeur_devis_panel as panel_create_editeur_devis
from erp.ui.panels.categories import create_categories_panel as panel_create_categories

# Helper pour créer un bouton avec la couleur du thème (utilisé comme méthode de classe uniquement)
def apply_theme_styles():
    """Applique les styles CSS basés sur le thème actif"""
    theme = get_theme()
    accent_color = theme.accent_color
    
    # Convertir la couleur hex en RGB pour les effets d'opacité
    def hex_to_rgb(hex_color):
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6:
                # Couleur par défaut si format invalide
                return (200, 76, 60)
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            # Couleur par défaut si conversion échoue
            return (200, 76, 60)
    
    # Valider et corriger la couleur si nécessaire
    # Forcer la couleur par défaut #c84c3c
    accent_color = '#c84c3c'
    
    rgb = hex_to_rgb(accent_color)
    rgb_str = f'{rgb[0]}, {rgb[1]}, {rgb[2]}'
    
    # Ajouter un log pour vérifier
    import logging
    logging.info(f"Applying theme with accent color: {accent_color}, RGB: {rgb_str}")
    
    theme_css = f'''
    /* Surcharger les variables CSS de Quasar à tous les niveaux */
    :root,
    body,
    #app {{
        --q-primary: {accent_color} !important;
        --q-positive: {accent_color} !important;
        --q-color-primary: {accent_color} !important;
        --theme-accent: {accent_color} !important;
    }}
    
    /* Boutons thématisés - utiliser la variable CSS */
    .themed-button,
    button.themed-button,
    .q-btn.themed-button {{
        background-color: var(--theme-accent) !important;
        color: white !important;
        border: none !important;
    }}
    
    .themed-button:hover,
    button.themed-button:hover,
    .q-btn.themed-button:hover {{
        filter: brightness(0.9) !important;
        opacity: 0.9 !important;
    }}
    
    /* Surcharger les couleurs Quasar par défaut */
    .q-btn.themed-button .q-btn__content {{
        color: white !important;
    }}
    
    /* Enlever les styles par défaut de Quasar */
    .q-btn.themed-button.q-btn--standard {{
        background: var(--theme-accent) !important;
    }}
    
    /* Forcer pour tous les boutons Quasar avec la classe */
    .q-btn.themed-button::before {{
        background: var(--theme-accent) !important;
    }}
    
    /* Texte d'accent */
    .themed-accent {{
        color: {accent_color};
    }}
    
    /* Bordures thématisées */
    .themed-border {{
        border-color: {accent_color};
    }}
    
    /* Éléments de menu actifs */
    .menu-item-active {{
        background-color: rgba({rgb_str}, 0.1);
        border-left: 4px solid {accent_color};
        color: {accent_color} !important;
    }}
    
    /* Sidebar */
    .themed-sidebar {{
        border-right: 1px solid {accent_color}33;
    }}
    
    /* Headers de cards */
    .themed-card-header {{
        border-bottom: 2px solid {accent_color};
        color: {accent_color};
    }}
    
    /* Listes actives */
    .themed-list-item-active {{
        background-color: rgba({rgb_str}, 0.1);
        color: {accent_color} !important;
    }}
    
    /* Tabs actifs */
    .themed-tab-active {{
        border-bottom: 3px solid {accent_color};
        color: {accent_color} !important;
    }}
    
    /* Links */
    .themed-link {{
        color: {accent_color} !important;
        text-decoration: none;
    }}
    
    .themed-link:hover {{
        text-decoration: underline;
    }}
    
    /* Icônes des boutons avec thème */
    .themed-link .q-icon {{
        color: {accent_color} !important;
    }}
    
    /* Boutons de suppression en rouge */
    .delete-button .q-icon {{
        color: #dc2626 !important;
    }}
    
    /* Badge/Statut */
    .themed-badge {{
        background-color: rgba({rgb_str}, 0.2);
        color: {accent_color};
        border: 1px solid {accent_color};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 500;
    }}
    
    /* Input focus */
    input:focus {{
        border-color: {accent_color} !important;
        box-shadow: 0 0 0 3px rgba({rgb_str}, 0.1) !important;
    }}
    
    /* Select focus */
    select:focus {{
        border-color: {accent_color} !important;
        box-shadow: 0 0 0 3px rgba({rgb_str}, 0.1) !important;
    }}
    '''
    
    ui.add_head_html(f'<style>{theme_css}</style>')


class DevisApp:
    def __init__(self):
        self.dm = DataManager()
        self.current_devis_lignes: List[LigneDevis] = []
        self.current_devis_coefficient: float = 1.35  # Coefficient du devis actuel
        self.selected_client_id = None
        self.next_ligne_id = 0
        
        # UI references
        self.total_ht_label = None
        self.total_tva_label = None
        self.total_ttc_label = None
        self.tva_rate_field = None
        self.client_select = None
        
        # Load CSS once
        ui.add_head_html(f'<style>{CONSOLIDATED_STYLES}</style>')
        apply_theme_styles()

    def update_totals(self):
        """Met à jour l'affichage des totaux du devis"""
        total_ht = sum(ligne.prix_ht for ligne in self.current_devis_lignes if ligne.type == 'ouvrage')
        
        tva_rate = self.tva_rate_field.value / 100 if self.tva_rate_field else 0.20
        total_tva = total_ht * tva_rate
        total_ttc = total_ht + total_tva
        
        if self.total_ht_label:
            self.total_ht_label.set_text(f"Total HT: {total_ht:.2f} EUR")
        if self.total_tva_label:
            self.total_tva_label.set_text(f"{total_tva:.2f} EUR")
        if self.total_ttc_label:
            self.total_ttc_label.set_text(f"Total TTC: {total_ttc:.2f} EUR")

    def update_ouvrage_prix(self, coefficient: float = None):
        """Met a jour les prix de l'ouvrage en creation"""
        if coefficient is None:
            coefficient = 1.35
        
        prix_revient = sum(c.prix_total() for c in self.current_ouvrage_composants)
        prix_vente = prix_revient * coefficient
        marge = prix_vente - prix_revient
        taux_marge = (marge / prix_revient * 100) if prix_revient > 0 else 0
        
        if self.ouvrage_prix_revient_label:
            self.ouvrage_prix_revient_label.set_text(f'Prix de revient: {prix_revient:.2f} EUR')
        if self.ouvrage_prix_vente_label:
            self.ouvrage_prix_vente_label.set_text(f'Prix de vente: {prix_vente:.2f} EUR')
        if self.ouvrage_marge_label:
            self.ouvrage_marge_label.set_text(f'Marge: {marge:.2f} EUR ({taux_marge:.1f}%)')
        
        if self.composants_table:
            self.composants_table.rows = [
                {
                    'designation': c.designation,
                    'quantite': f"{c.quantite:.2f}",
                    'unite': c.unite,
                    'prix_unitaire': f"{c.prix_unitaire:.2f} EUR",
                    'total': f"{c.prix_total():.2f} EUR",
                    'actions': i
                }
                for i, c in enumerate(self.current_ouvrage_composants)
            ]
            self.composants_table.update()

    def add_ligne_devis(self, ouvrage_id: int, quantite: float, remise: float = 0.0, chapitre_id: int = None):
        """Ajoute une ligne (ouvrage) au devis"""
        from copy import deepcopy
        ouvrage = self.dm.get_ouvrage_by_id(ouvrage_id)
        if ouvrage:
            # Calculer le prix unitaire: prix de revient * coefficient du devis
            prix_unitaire = ouvrage.prix_revient_unitaire * self.current_devis_coefficient
            
            ligne = LigneDevis(
                type='ouvrage',
                id=self.next_ligne_id,
                ouvrage_id=ouvrage.id,
                designation=ouvrage.designation,
                description=ouvrage.description,
                quantite=quantite,
                unite=ouvrage.unite,
                prix_unitaire=prix_unitaire,
                composants=deepcopy(ouvrage.composants)
            )
            self.next_ligne_id += 1
            self.current_devis_lignes.append(ligne)
            self.update_totals()

    def remove_ligne_devis(self, index: int):
        """Supprime une ligne du devis"""
        if 0 <= index < len(self.current_devis_lignes):
            self.current_devis_lignes.pop(index)
            self.update_totals()

    def apply_coefficient_to_all_lines(self, coefficient_value: float):
        """Applique le coefficient à toutes les lignes devis du devis actuel"""
        self.current_devis_coefficient = coefficient_value
        for ligne in self.current_devis_lignes:
            # Les lignes du devis ont type='ouvrage' avec composants
            if ligne.type == 'ouvrage' and hasattr(ligne, 'composants') and ligne.composants:
                composants_total = sum(c.prix_total() for c in ligne.composants)
                ligne.prix_unitaire = composants_total * coefficient_value
        self.update_totals()

    def create_themed_button(self, label: str, on_click=None, **kwargs):
        """Crée un bouton avec la couleur d'accent du thème"""
        btn = ui.button(label, on_click=on_click, **kwargs)
        btn.classes('themed-button')
        return btn

    def material_icon_button(self, icon_name: str, on_click=None, is_delete: bool = False):
        """Crée un bouton avec Material Symbols Icon (comme dans le menu)"""
        # Utiliser directement le nom de l'icône Material Symbols
        btn = ui.button(icon=icon_name, on_click=on_click).props('flat round')
        
        # Utiliser la couleur thématique par défaut (définie dans paramètres) ou rouge pour suppression
        if is_delete:
            btn.classes('delete-button hover:bg-red-50')
        else:
            btn.classes('themed-link hover:bg-gray-100')
        return btn

    def create_main_ui(self):
        """Cree l'interface principale"""
        from erp.core.auth import AuthManager
        from nicegui import app as nicegui_app
        
        with ui.header().classes('app-header items-center justify-between').style('background-color: #f5f1ec; border-bottom: 1px solid #e5e7eb;'):
            ui.label('ERP BTP').classes('title text-xl').style('color: #2c3e50;')
            
            # Ajouter le nom d'utilisateur et bouton de déconnexion
            with ui.row().classes('items-center gap-4'):
                username = nicegui_app.storage.user.get('username', 'Utilisateur')
                ui.label(f'👤 {username}').classes('text-sm').style('color: #2c3e50;')
                
                def handle_logout():
                    """Déconnecte l'utilisateur"""
                    session_id = nicegui_app.storage.user.get('session_id')
                    if session_id:
                        from erp.core.data_manager import DataManager
                        data_manager = DataManager()
                        auth_manager = AuthManager(data_manager)
                        auth_manager.logout(session_id)
                    
                    # Nettoyer le storage
                    nicegui_app.storage.user.clear()
                    
                    # Rediriger vers la page de login
                    ui.navigate.to('/login')
                
                ui.button('Déconnexion', on_click=handle_logout, icon='logout').classes('text-sm')

        with ui.row().classes('w-full').style('min-height: calc(100vh - 80px); background: var(--qonto-bg);'):
            # Menu vertical stylisé avec icônes (NOUVEAU MENU)
            menu_items = [
                ('Organisation', 'Organisation'),
                ('Devis', 'Devis'),
                ('Chantiers', 'Chantiers'),
                ('Catalogue', 'Catalogue'),
                ('Clients', 'Clients'),
                ('Éditeur', 'Éditeur'),
                ('Tableau de bord', 'Dashboard'),
                ('Paramètres', 'Paramètres'),
            ]
            
            current_section = {'value': 'devis'}
            
            def on_menu_selection(item_label: str):
                """Callback du menu - change la section affichée"""
                # Mapper le label du menu à la clé de section
                section_map = {
                    'Tableau de bord': 'dashboard',
                    'Organisation': 'organisation',
                    'Devis': 'devis',
                    'Chantiers': 'projets',
                    'Catalogue': 'catalogue',
                    'Clients': 'clients',
                    'Éditeur': 'editeur',
                    'Paramètres': 'parametres',
                }
                
                section_key = section_map.get(item_label, 'dashboard')
                current_section['value'] = section_key
                
                # R�initialiser le menu horizontal
                horizontal_menu_container.clear()
                
                # Afficher la section avec ses sous-menus
                subsections_map = {
                    'devis': ['liste', 'devis'],
                    'catalogue': ['liste_ouvrages', 'ouvrages', 'liste_articles', 'articles', 'categories'],
                    'editeur': ['editeur_devis'],
                }
                subsections = subsections_map.get(section_key)
                show_section_with_children(section_key, subsections)
            
            # Créer le menu stylisé
            menu = create_main_menu(on_item_selected=on_menu_selection, menu_items=menu_items)
            
            # Contenu principal à droite
            with ui.column().classes('flex-1').style('overflow: hidden; display: flex; flex-direction: column;'):
                # Conteneur pour le menu horizontal (MENU ENFANT)
                horizontal_menu_container = ui.row().classes('w-full bg-white shadow-sm items-center').style('border-bottom: 1px solid #e0e0e0; padding: 12px 24px; min-height: 50px;')
                
                # Conteneur pour le contenu principal
                with ui.column().classes('flex-1 overflow-y-auto').style('padding: 0; background: var(--qonto-bg); width: 100%;'):
                    content_container = ui.column().classes('w-full').style('padding: 0; margin: 0; width: 100%;')
                    
                    def show_content(content_key):
                        """Affiche le contenu de la section"""
                        content_container.clear()
                        with content_container:
                            if content_key == 'dashboard':
                                self.create_dashboard_panel()
                            elif content_key == 'organisation':
                                self.create_company_panel()
                            elif content_key == 'devis':
                                self.create_devis_panel()
                            elif content_key == 'projets':
                                self.create_projets_panel()
                            elif content_key == 'ouvrages':
                                self.create_ouvrages_panel()
                            elif content_key == 'articles':
                                self.create_catalogue_panel()
                            elif content_key == 'clients':
                                self.create_clients_panel()
                            elif content_key == 'parametres':
                                self.create_parametres_panel()
                            elif content_key == 'liste':
                                self.create_liste_devis_panel()
                            elif content_key == 'creer':
                                self.create_devis_panel()
                            elif content_key == 'liste_articles':
                                self.create_liste_articles_panel()
                            elif content_key == 'liste_ouvrages':
                                self.create_liste_ouvrages_panel()
                            elif content_key == 'editeur_devis':
                                self.create_editeur_devis_panel()
                            elif content_key == 'editeur':
                                self.create_editeur_devis_panel()
                            elif content_key == 'categories':
                                self.create_categories_panel()
                    
                    def show_section_with_children(section_key, subsections):
                        """Affiche la section avec ses sous-menus horizontaux"""
                        # Réinitialiser le menu horizontal
                        horizontal_menu_container.clear()
                        
                        with horizontal_menu_container:
                            if subsections:
                                # Créer les tabs pour les sous-sections
                                with ui.tabs().classes('w-full') as tab_selector:
                                    for sub_key in subsections:
                                        if sub_key == 'devis':
                                            ui.tab('devis_tab', label='Devis')
                                        elif sub_key == 'liste':
                                            ui.tab('liste_tab', label='Liste Devis')
                                        elif sub_key == 'articles':
                                            ui.tab('articles_tab', label='Articles')
                                        elif sub_key == 'liste_articles':
                                            ui.tab('liste_articles_tab', label='Liste Articles')
                                        elif sub_key == 'ouvrages':
                                            ui.tab('ouvrages_tab', label='Ouvrages')
                                        elif sub_key == 'liste_ouvrages':
                                            ui.tab('liste_ouvrages_tab', label='Liste Ouvrages')
                                        elif sub_key == 'editeur_devis':
                                            ui.tab('editeur_devis_tab', label='Éditeur de mise en forme')
                                        elif sub_key == 'categories':
                                            ui.tab('categories_tab', label='Catégories')
                                    
                                    self.tab_selector = tab_selector
                                    
                                    # Observer les changements de tab - utiliser une factory function
                                    def make_tab_change_handler(selector):
                                        def on_tab_change():
                                            current_tab = selector.value
                                            if current_tab == 'devis_tab':
                                                show_content('devis')
                                            elif current_tab == 'liste_tab':
                                                show_content('liste')
                                            elif current_tab == 'articles_tab':
                                                show_content('articles')
                                            elif current_tab == 'liste_articles_tab':
                                                show_content('liste_articles')
                                            elif current_tab == 'ouvrages_tab':
                                                show_content('ouvrages')
                                            elif current_tab == 'liste_ouvrages_tab':
                                                show_content('liste_ouvrages')
                                            elif current_tab == 'editeur_devis_tab':
                                                show_content('editeur_devis')
                                            elif current_tab == 'categories_tab':
                                                show_content('categories')
                                        return on_tab_change
                                    
                                    # Définir la valeur par défaut AVANT d'attacher le handler
                                    if subsections:
                                        tab_selector.value = f"{subsections[0]}_tab"
                                    
                                    # Attacher le handler APRÈS avoir défini la valeur initiale
                                    tab_selector.on_value_change(make_tab_change_handler(tab_selector))
                            else:
                                # Pas de sous-menu pour cette section
                                ui.label('').classes('text-gray-500 text-sm')
                        
                        # Afficher le contenu initial
                        if subsections:
                            show_content(subsections[0])
                        else:
                            show_content(section_key)
                    
                    # Stocker les références pour la navigation
                    self.show_section_with_children = show_section_with_children
                    self.show_content = show_content
                    self.current_section = current_section
                    
                    # Afficher la section par défaut (devis)
                    show_section_with_children('devis', ['devis', 'liste'])

    def create_devis_panel(self):
        """Cree le panneau de gestion des devis"""
        panel_create_devis(self)

    def create_ouvrages_panel(self):
        """Cree le panneau de gestion des ouvrages"""
        panel_create_ouvrages(self)

    def create_catalogue_panel(self):
        """Cree le panneau de gestion des articles"""
        panel_create_catalogue(self)

    def create_clients_panel(self):
        """Crée le panneau de gestion des clients"""
        panel_create_clients(self)
    
    def create_projets_panel(self):
        """Crée le panneau de gestion des projets"""
        panel_create_projets(self)

    def create_parametres_panel(self):
        """Crée le panneau de paramètres"""
        panel_create_parametres(self)

    def create_liste_devis_panel(self):
        """Cree le panneau de liste des devis"""
        panel_create_liste_devis(self)

    def create_liste_articles_panel(self):
        """Crée le panneau de liste des articles"""
        panel_create_liste_articles(self)

    def create_liste_ouvrages_panel(self):
        """Crée le panneau de liste des ouvrages"""
        panel_create_liste_ouvrages(self)

    def create_dashboard_panel(self):
        """Crée le panneau du dashboard"""
        panel_create_dashboard(self)

    def create_company_panel(self):
        """Cree le panneau de gestion de l'organisation"""
        panel_create_company(self)

    def create_editeur_devis_panel(self):
        """Crée le panneau éditeur de mise en forme des devis"""
        panel_create_editeur_devis(self)

    def create_categories_panel(self):
        """Crée le panneau de gestion des catégories"""
        panel_create_categories(self)
