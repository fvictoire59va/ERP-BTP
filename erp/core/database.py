"""
Module de gestion de la base de données PostgreSQL
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import os
from erp.utils.logger import get_logger

logger = get_logger(__name__)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# Configuration de la connexion PostgreSQL
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'client_erpbtp_victoire'),
    'user': os.getenv('POSTGRES_USER', 'fred'),
    'password': os.getenv('POSTGRES_PASSWORD', 'victoire')
}


class DatabaseManager:
    """Gestionnaire de connexion à la base de données PostgreSQL"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.Session = None
        
    def initialize(self):
        """Initialise la connexion à la base de données"""
        try:
            # Créer l'URL de connexion PostgreSQL
            db_url = (
                f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
                f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            )
            
            # Créer le moteur SQLAlchemy
            self.engine = create_engine(
                db_url,
                echo=False,  # Mettre à True pour voir les requêtes SQL
                pool_pre_ping=True,  # Vérifier la connexion avant utilisation
                pool_size=10,  # Taille du pool de connexions
                max_overflow=20  # Connexions supplémentaires possibles
            )
            
            # Créer la fabrique de sessions
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            # Tester la connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Connexion à la base de données PostgreSQL établie: {DB_CONFIG['database']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}", exc_info=True)
            raise
    
    def create_tables(self):
        """Crée toutes les tables dans la base de données"""
        try:
            # Importer les modèles pour que SQLAlchemy les connaisse
            from erp.core import db_models
            
            Base.metadata.create_all(self.engine)
            logger.info("Tables créées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création des tables: {e}", exc_info=True)
            raise
    
    def drop_tables(self):
        """Supprime toutes les tables (ATTENTION: perte de données)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("Toutes les tables ont été supprimées")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des tables: {e}", exc_info=True)
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager pour obtenir une session de base de données.
        
        Usage:
            with db_manager.get_session() as session:
                session.query(...)
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur dans la session de base de données: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def close(self):
        """Ferme toutes les connexions"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Connexions à la base de données fermées")


# Instance singleton du gestionnaire de base de données
db_manager = DatabaseManager()


def init_db():
    """Fonction d'initialisation de la base de données"""
    db_manager.initialize()
    db_manager.create_tables()
