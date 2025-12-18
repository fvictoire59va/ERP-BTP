"""
Configuration pour choisir le backend de stockage
"""
import os

# Backend de stockage: 'json' ou 'postgres'
STORAGE_BACKEND = os.getenv('ERP_STORAGE_BACKEND', 'json')

# Configuration PostgreSQL (utilisée uniquement si STORAGE_BACKEND == 'postgres')
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'client_erpbtp_victoire'),
    'user': os.getenv('POSTGRES_USER', 'fred'),
    'password': os.getenv('POSTGRES_PASSWORD', 'victoire')
}


def get_data_manager():
    """
    Retourne l'instance du gestionnaire de données approprié
    selon la configuration
    """
    if STORAGE_BACKEND == 'postgres':
        from erp.core.data_manager_postgres import DataManagerPostgres
        return DataManagerPostgres()
    else:
        from erp.core.data_manager import DataManager
        return DataManager()
