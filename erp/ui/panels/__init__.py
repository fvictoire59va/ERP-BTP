"""
UI Panels - Individual application panels
"""
from erp.ui.panels.devis import create_devis_panel
from erp.ui.panels.ouvrages import create_ouvrages_panel
from erp.ui.panels.catalogue import create_catalogue_panel
from erp.ui.panels.clients import create_clients_panel
from erp.ui.panels.parametres import create_parametres_panel
from erp.ui.panels.liste_devis import create_liste_devis_panel
from erp.ui.panels.dashboard import create_dashboard_panel
from erp.ui.panels.organisation import create_company_panel

__all__ = [
    'create_devis_panel',
    'create_ouvrages_panel',
    'create_catalogue_panel',
    'create_clients_panel',
    'create_parametres_panel',
    'create_liste_devis_panel',
    'create_dashboard_panel',
    'create_company_panel',
]
