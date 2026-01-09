"""
Configuration pour choisir le backend de stockage
PostgreSQL est maintenant le backend unique.
"""
import os

# Backend de stockage: PostgreSQL uniquement
STORAGE_BACKEND = 'postgres'

# Configuration PostgreSQL
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'client_erpbtp_victoire'),
    'user': os.getenv('POSTGRES_USER', 'fred'),
    'password': os.getenv('POSTGRES_PASSWORD', 'victoire')
}


def get_data_manager():
    """
    Retourne l'instance du gestionnaire de données PostgreSQL
    """
    from erp.core.data_manager_postgres import DataManagerPostgres
    return DataManagerPostgres()
