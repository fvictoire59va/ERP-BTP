"""
Core module - Business logic and data models
"""
from erp.core.constants import *
from erp.core.models import (
    CategorieOuvrage,
    TypeArticle,
    Organisation,
    Client,
    Fournisseur,
    Article,
    ComposantOuvrage,
    Ouvrage,
    LigneDevis,
    Devis,
)
from erp.core.storage_config import get_data_manager

__all__ = [
    # Constants
    'DEFAULT_TVA_RATE',
    'DEFAULT_COEFFICIENT_MARGE',
    'DATE_FORMAT',
    'DEVIS_NUMBER_FORMAT',
    'MAX_LIGNE_DEVIS',
    'MIN_COEFFICIENT_MARGE',
    'MAX_COEFFICIENT_MARGE',
    'DEVIS_STATUSES',
    'DEVIS_STATUS_COLORS',
    # Models
    'CategorieOuvrage',
    'TypeArticle',
    'Organisation',
    'Client',
    'Fournisseur',
    'Article',
    'ComposantOuvrage',
    'Ouvrage',
    'LigneDevis',
    'Devis',
    # Data Manager
    'DataManager',
]
