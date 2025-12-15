# -*- coding: utf-8 -*-
"""
DEPRECATED: Ce fichier a ete reorganise en fichiers separes.

Les fonctions ont ete deplacees vers:
- create_liste_devis_panel -> liste_devis.py
- create_dashboard_panel -> dashboard.py
- create_company_panel -> organisation.py

Ce fichier est conserve temporairement pour compatibilite.
"""

# Imports de compatibilite
from erp.ui.panels.liste_devis import create_liste_devis_panel
from erp.ui.panels.dashboard import create_dashboard_panel
from erp.ui.panels.organisation import create_company_panel

__all__ = [
    'create_liste_devis_panel',
    'create_dashboard_panel',
    'create_company_panel',
]
