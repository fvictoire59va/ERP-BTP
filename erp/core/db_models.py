"""
Modèles SQLAlchemy pour PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, JSON, Date, Boolean
from sqlalchemy.orm import relationship
from erp.core.database import Base


class OrganisationModel(Base):
    """Table Organisation"""
    __tablename__ = 'organisations'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    siret = Column(String(50))
    adresse = Column(String(255))
    cp = Column(String(20))
    ville = Column(String(100))
    telephone = Column(String(30))
    email = Column(String(100))
    site_web = Column(String(255))
    logo_path = Column(String(255))
    date_debut_exercice = Column(String(10))
    date_fin_exercice = Column(String(10))


class ClientModel(Base):
    """Table Clients"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    entreprise = Column(String(255))
    adresse = Column(String(255))
    cp = Column(String(10))
    ville = Column(String(100))
    telephone = Column(String(20))
    email = Column(String(100))
    
    # Relations
    devis = relationship("DevisModel", back_populates="client")
    projets = relationship("ProjetModel", back_populates="client")


class FournisseurModel(Base):
    """Table Fournisseurs"""
    __tablename__ = 'fournisseurs'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    specialite = Column(String(255))
    telephone = Column(String(20))
    email = Column(String(100))
    remise = Column(Float, default=0.0)
    
    # Relations
    articles = relationship("ArticleModel", back_populates="fournisseur")


class ArticleModel(Base):
    """Table Articles"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    reference = Column(String(50), nullable=False, unique=True)
    designation = Column(String(255), nullable=False)
    unite = Column(String(20), nullable=False)  # m², ml, u, h, forfait
    prix_unitaire = Column(Float, nullable=False)
    type_article = Column(String(50), nullable=False)  # materiau, fourniture, main_oeuvre, consommable
    fournisseur_id = Column(Integer, ForeignKey('fournisseurs.id'), nullable=True)
    description = Column(Text)
    categorie = Column(String(50), default='general')
    
    # Relations
    fournisseur = relationship("FournisseurModel", back_populates="articles")


class OuvrageModel(Base):
    """Table Ouvrages"""
    __tablename__ = 'ouvrages'
    
    id = Column(Integer, primary_key=True)
    reference = Column(String(50), nullable=False, unique=True)
    designation = Column(String(255), nullable=False)
    description = Column(Text)
    categorie = Column(String(50))
    sous_categorie = Column(String(50))
    unite = Column(String(20), nullable=False)
    composants = Column(JSON)  # Stocké en JSON: [{article_id, quantite, designation, unite, prix_unitaire}, ...]


class DevisModel(Base):
    """Table Devis"""
    __tablename__ = 'devis'
    
    numero = Column(String(50), primary_key=True)
    date = Column(String(10), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    objet = Column(String(255))
    lignes = Column(JSON)  # Stocké en JSON
    coefficient_marge = Column(Float, default=1.35)
    remise = Column(Float, default=0.0)
    tva = Column(Float, default=20.0)
    validite = Column(Integer, default=30)
    notes = Column(Text)
    conditions = Column(Text)
    statut = Column(String(20), default='en cours')  # en cours, envoyé, refusé, accepté
    
    # Relations
    client = relationship("ClientModel", back_populates="devis")


class ProjetModel(Base):
    """Table Projets"""
    __tablename__ = 'projets'
    
    id = Column(Integer, primary_key=True)
    numero = Column(String(50), nullable=False, unique=True)
    devis_numeros = Column(JSON)  # Liste des numéros de devis
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date_creation = Column(String(10), nullable=False)
    date_debut = Column(String(10))
    date_fin_prevue = Column(String(10))
    date_fin_reelle = Column(String(10))
    statut = Column(String(20), default='en attente')  # en attente, en cours, terminé, annulé
    adresse_chantier = Column(String(255))
    notes = Column(Text)
    depenses_reelles = Column(JSON)  # Stocké en JSON
    
    # Relations
    client = relationship("ClientModel", back_populates="projets")


class UserModel(Base):
    """Table Utilisateurs"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)  # UUID
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    role = Column(String(20), default='user')  # admin, user
    nom = Column(String(100))
    prenom = Column(String(100))
    email = Column(String(100))
    client_id = Column(Integer, nullable=True)  # Référence au client dans la table abonnements
    actif = Column(Boolean, default=True)
    date_creation = Column(String(10))
    derniere_connexion = Column(String(19))  # Format: YYYY-MM-DD HH:MM:SS


class CategorieModel(Base):
    """Table Catégories"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    ordre = Column(Integer, default=0)
