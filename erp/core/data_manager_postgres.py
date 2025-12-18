"""
Gestionnaire de données avec PostgreSQL
Version compatible avec PostgreSQL utilisant SQLAlchemy
"""
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict
from datetime import datetime

from erp.core.models import (
    Client, Fournisseur, Article, Ouvrage, ComposantOuvrage, 
    Devis, LigneDevis, Organisation, Projet, DepenseReelle, User
)
from erp.core.database import db_manager
from erp.core.db_models import (
    OrganisationModel, ClientModel, FournisseurModel, ArticleModel,
    OuvrageModel, DevisModel, ProjetModel, UserModel, CategorieModel
)
from erp.utils.logger import get_logger
from erp.utils.exceptions import DataPersistenceError, ResourceNotFoundError

logger = get_logger(__name__)

# Singleton instance
_instance = None


class DataManagerPostgres:
    """
    Gestionnaire de données utilisant PostgreSQL.
    Remplace l'ancien système basé sur JSON.
    """
    
    def __new__(cls):
        global _instance
        if _instance is None:
            _instance = super(DataManagerPostgres, cls).__new__(cls)
            _instance._initialized = False
        return _instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialiser la connexion à la base de données
        db_manager.initialize()
        db_manager.create_tables()
        
        logger.info("DataManagerPostgres initialized with PostgreSQL")
        self._initialized = True
    
    # ==================== ORGANISATION ====================
    
    @property
    def organisation(self) -> Organisation:
        """Récupère les informations de l'organisation"""
        with db_manager.get_session() as session:
            org_model = session.query(OrganisationModel).first()
            if org_model:
                return Organisation(
                    id=org_model.id,
                    nom=org_model.nom or "",
                    siret=org_model.siret or "",
                    adresse=org_model.adresse or "",
                    cp=org_model.cp or "",
                    ville=org_model.ville or "",
                    telephone=org_model.telephone or "",
                    email=org_model.email or "",
                    site_web=org_model.site_web or "",
                    logo_path=org_model.logo_path or "",
                    date_debut_exercice=org_model.date_debut_exercice or "",
                    date_fin_exercice=org_model.date_fin_exercice or ""
                )
            # Créer une organisation par défaut
            return Organisation()
    
    @organisation.setter
    def organisation(self, org: Organisation):
        """Met à jour les informations de l'organisation"""
        with db_manager.get_session() as session:
            org_model = session.query(OrganisationModel).first()
            if org_model:
                org_model.nom = org.nom
                org_model.siret = org.siret
                org_model.adresse = org.adresse
                org_model.cp = org.cp
                org_model.ville = org.ville
                org_model.telephone = org.telephone
                org_model.email = org.email
                org_model.site_web = org.site_web
                org_model.logo_path = org.logo_path
                org_model.date_debut_exercice = org.date_debut_exercice
                org_model.date_fin_exercice = org.date_fin_exercice
            else:
                org_model = OrganisationModel(
                    id=org.id,
                    nom=org.nom,
                    siret=org.siret,
                    adresse=org.adresse,
                    cp=org.cp,
                    ville=org.ville,
                    telephone=org.telephone,
                    email=org.email,
                    site_web=org.site_web,
                    logo_path=org.logo_path,
                    date_debut_exercice=org.date_debut_exercice,
                    date_fin_exercice=org.date_fin_exercice
                )
                session.add(org_model)
    
    # ==================== CLIENTS ====================
    
    @property
    def clients(self) -> List[Client]:
        """Récupère tous les clients"""
        with db_manager.get_session() as session:
            clients_models = session.query(ClientModel).all()
            return [
                Client(
                    id=c.id,
                    nom=c.nom,
                    prenom=c.prenom,
                    entreprise=c.entreprise or "",
                    adresse=c.adresse or "",
                    cp=c.cp or "",
                    ville=c.ville or "",
                    telephone=c.telephone or "",
                    email=c.email or ""
                )
                for c in clients_models
            ]
    
    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID"""
        with db_manager.get_session() as session:
            c = session.query(ClientModel).filter_by(id=client_id).first()
            if c:
                return Client(
                    id=c.id,
                    nom=c.nom,
                    prenom=c.prenom,
                    entreprise=c.entreprise or "",
                    adresse=c.adresse or "",
                    cp=c.cp or "",
                    ville=c.ville or "",
                    telephone=c.telephone or "",
                    email=c.email or ""
                )
            logger.warning(f"Client not found: {client_id}")
            return None
    
    def add_client(self, client: Client):
        """Ajoute un nouveau client"""
        with db_manager.get_session() as session:
            client_model = ClientModel(
                id=client.id,
                nom=client.nom,
                prenom=client.prenom,
                entreprise=client.entreprise,
                adresse=client.adresse,
                cp=client.cp,
                ville=client.ville,
                telephone=client.telephone,
                email=client.email
            )
            session.add(client_model)
        logger.info(f"Client added: {client.nom} {client.prenom}")
    
    def update_client(self, client: Client):
        """Met à jour un client existant"""
        with db_manager.get_session() as session:
            c = session.query(ClientModel).filter_by(id=client.id).first()
            if c:
                c.nom = client.nom
                c.prenom = client.prenom
                c.entreprise = client.entreprise
                c.adresse = client.adresse
                c.cp = client.cp
                c.ville = client.ville
                c.telephone = client.telephone
                c.email = client.email
                logger.info(f"Client updated: {client.id}")
            else:
                raise ResourceNotFoundError(f"Client not found: {client.id}")
    
    def delete_client(self, client_id: int):
        """Supprime un client"""
        with db_manager.get_session() as session:
            c = session.query(ClientModel).filter_by(id=client_id).first()
            if c:
                session.delete(c)
                logger.info(f"Client deleted: {client_id}")
            else:
                raise ResourceNotFoundError(f"Client not found: {client_id}")
    
    # ==================== FOURNISSEURS ====================
    
    @property
    def fournisseurs(self) -> List[Fournisseur]:
        """Récupère tous les fournisseurs"""
        with db_manager.get_session() as session:
            fournisseurs_models = session.query(FournisseurModel).all()
            return [
                Fournisseur(
                    id=f.id,
                    nom=f.nom,
                    specialite=f.specialite or "",
                    telephone=f.telephone or "",
                    email=f.email or "",
                    remise=f.remise or 0.0
                )
                for f in fournisseurs_models
            ]
    
    def get_fournisseur_by_id(self, fournisseur_id: int) -> Optional[Fournisseur]:
        """Récupère un fournisseur par son ID"""
        with db_manager.get_session() as session:
            f = session.query(FournisseurModel).filter_by(id=fournisseur_id).first()
            if f:
                return Fournisseur(
                    id=f.id,
                    nom=f.nom,
                    specialite=f.specialite or "",
                    telephone=f.telephone or "",
                    email=f.email or "",
                    remise=f.remise or 0.0
                )
            return None
    
    def add_fournisseur(self, fournisseur: Fournisseur):
        """Ajoute un nouveau fournisseur"""
        with db_manager.get_session() as session:
            f_model = FournisseurModel(
                id=fournisseur.id,
                nom=fournisseur.nom,
                specialite=fournisseur.specialite,
                telephone=fournisseur.telephone,
                email=fournisseur.email,
                remise=fournisseur.remise
            )
            session.add(f_model)
        logger.info(f"Fournisseur added: {fournisseur.nom}")
    
    def update_fournisseur(self, fournisseur: Fournisseur):
        """Met à jour un fournisseur existant"""
        with db_manager.get_session() as session:
            f = session.query(FournisseurModel).filter_by(id=fournisseur.id).first()
            if f:
                f.nom = fournisseur.nom
                f.specialite = fournisseur.specialite
                f.telephone = fournisseur.telephone
                f.email = fournisseur.email
                f.remise = fournisseur.remise
                logger.info(f"Fournisseur updated: {fournisseur.id}")
            else:
                raise ResourceNotFoundError(f"Fournisseur not found: {fournisseur.id}")
    
    def delete_fournisseur(self, fournisseur_id: int):
        """Supprime un fournisseur"""
        with db_manager.get_session() as session:
            f = session.query(FournisseurModel).filter_by(id=fournisseur_id).first()
            if f:
                session.delete(f)
                logger.info(f"Fournisseur deleted: {fournisseur_id}")
            else:
                raise ResourceNotFoundError(f"Fournisseur not found: {fournisseur_id}")
    
    # ==================== ARTICLES ====================
    
    @property
    def articles(self) -> List[Article]:
        """Récupère tous les articles"""
        with db_manager.get_session() as session:
            articles_models = session.query(ArticleModel).all()
            return [
                Article(
                    id=a.id,
                    reference=a.reference,
                    designation=a.designation,
                    unite=a.unite,
                    prix_unitaire=a.prix_unitaire,
                    type_article=a.type_article,
                    fournisseur_id=a.fournisseur_id if a.fournisseur_id is not None else 0,
                    description=a.description or "",
                    categorie=a.categorie or "general"
                )
                for a in articles_models
            ]
    
    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        """Récupère un article par son ID"""
        with db_manager.get_session() as session:
            a = session.query(ArticleModel).filter_by(id=article_id).first()
            if a:
                return Article(
                    id=a.id,
                    reference=a.reference,
                    designation=a.designation,
                    unite=a.unite,
                    prix_unitaire=a.prix_unitaire,
                    type_article=a.type_article,
                    fournisseur_id=a.fournisseur_id if a.fournisseur_id is not None else 0,
                    description=a.description or "",
                    categorie=a.categorie or "general"
                )
            return None
    
    def add_article(self, article: Article):
        """Ajoute un nouvel article"""
        with db_manager.get_session() as session:
            # Convertir fournisseur_id=0 en None pour les articles sans fournisseur
            fournisseur_id = article.fournisseur_id if article.fournisseur_id > 0 else None
            
            a_model = ArticleModel(
                id=article.id,
                reference=article.reference,
                designation=article.designation,
                unite=article.unite,
                prix_unitaire=article.prix_unitaire,
                type_article=article.type_article,
                fournisseur_id=fournisseur_id,
                description=article.description,
                categorie=article.categorie
            )
            session.add(a_model)
        logger.info(f"Article added: {article.reference}")
    
    def update_article(self, article: Article):
        """Met à jour un article existant"""
        with db_manager.get_session() as session:
            a = session.query(ArticleModel).filter_by(id=article.id).first()
            if a:
                # Convertir fournisseur_id=0 en None pour les articles sans fournisseur
                fournisseur_id = article.fournisseur_id if article.fournisseur_id > 0 else None
                
                a.reference = article.reference
                a.designation = article.designation
                a.unite = article.unite
                a.prix_unitaire = article.prix_unitaire
                a.type_article = article.type_article
                a.fournisseur_id = fournisseur_id
                a.description = article.description
                a.categorie = article.categorie
                logger.info(f"Article updated: {article.id}")
            else:
                raise ResourceNotFoundError(f"Article not found: {article.id}")
    
    def delete_article(self, article_id: int):
        """Supprime un article"""
        with db_manager.get_session() as session:
            a = session.query(ArticleModel).filter_by(id=article_id).first()
            if a:
                session.delete(a)
                logger.info(f"Article deleted: {article_id}")
            else:
                raise ResourceNotFoundError(f"Article not found: {article_id}")
    
    # ==================== OUVRAGES ====================
    
    @property
    def ouvrages(self) -> List[Ouvrage]:
        """Récupère tous les ouvrages"""
        with db_manager.get_session() as session:
            ouvrages_models = session.query(OuvrageModel).all()
            ouvrages = []
            for o in ouvrages_models:
                composants = []
                if o.composants:
                    for comp_data in o.composants:
                        composants.append(ComposantOuvrage(
                            article_id=comp_data['article_id'],
                            quantite=comp_data['quantite'],
                            designation=comp_data.get('designation', ''),
                            unite=comp_data.get('unite', ''),
                            prix_unitaire=comp_data.get('prix_unitaire', 0.0)
                        ))
                
                ouvrages.append(Ouvrage(
                    id=o.id,
                    reference=o.reference,
                    designation=o.designation,
                    description=o.description or "",
                    categorie=o.categorie or "",
                    sous_categorie=o.sous_categorie or "",
                    unite=o.unite,
                    composants=composants
                ))
            return ouvrages
    
    def get_ouvrage_by_id(self, ouvrage_id: int) -> Optional[Ouvrage]:
        """Récupère un ouvrage par son ID"""
        with db_manager.get_session() as session:
            o = session.query(OuvrageModel).filter_by(id=ouvrage_id).first()
            if o:
                composants = []
                if o.composants:
                    for comp_data in o.composants:
                        composants.append(ComposantOuvrage(
                            article_id=comp_data['article_id'],
                            quantite=comp_data['quantite'],
                            designation=comp_data.get('designation', ''),
                            unite=comp_data.get('unite', ''),
                            prix_unitaire=comp_data.get('prix_unitaire', 0.0)
                        ))
                
                return Ouvrage(
                    id=o.id,
                    reference=o.reference,
                    designation=o.designation,
                    description=o.description or "",
                    categorie=o.categorie or "",
                    sous_categorie=o.sous_categorie or "",
                    unite=o.unite,
                    composants=composants
                )
            return None
    
    def add_ouvrage(self, ouvrage: Ouvrage):
        """Ajoute un nouvel ouvrage"""
        with db_manager.get_session() as session:
            composants_json = [asdict(c) for c in ouvrage.composants]
            o_model = OuvrageModel(
                reference=ouvrage.reference,
                designation=ouvrage.designation,
                description=ouvrage.description,
                categorie=ouvrage.categorie,
                sous_categorie=ouvrage.sous_categorie or None,
                unite=ouvrage.unite,
                composants=composants_json
            )
            # Ne pas spécifier l'ID, laisser PostgreSQL le générer automatiquement
            session.add(o_model)
            session.flush()  # Générer l'ID avant de sortir du contexte
            ouvrage.id = o_model.id  # Mettre à jour l'ID de l'objet
        logger.info(f"Ouvrage added: {ouvrage.reference}")
    
    def update_ouvrage(self, ouvrage: Ouvrage):
        """Met à jour un ouvrage existant"""
        with db_manager.get_session() as session:
            o = session.query(OuvrageModel).filter_by(id=ouvrage.id).first()
            if o:
                composants_json = [asdict(c) for c in ouvrage.composants]
                o.reference = ouvrage.reference
                o.designation = ouvrage.designation
                o.description = ouvrage.description
                o.categorie = ouvrage.categorie
                o.sous_categorie = ouvrage.sous_categorie or None
                o.unite = ouvrage.unite
                o.composants = composants_json
                logger.info(f"Ouvrage updated: {ouvrage.id}")
            else:
                raise ResourceNotFoundError(f"Ouvrage not found: {ouvrage.id}")
    
    def delete_ouvrage(self, ouvrage_id: int):
        """Supprime un ouvrage"""
        with db_manager.get_session() as session:
            o = session.query(OuvrageModel).filter_by(id=ouvrage_id).first()
            if o:
                session.delete(o)
                logger.info(f"Ouvrage deleted: {ouvrage_id}")
            else:
                raise ResourceNotFoundError(f"Ouvrage not found: {ouvrage_id}")
    
    def get_next_ouvrage_id(self) -> int:
        """Génère le prochain ID d'ouvrage"""
        with db_manager.get_session() as session:
            max_id = session.query(OuvrageModel.id).order_by(OuvrageModel.id.desc()).first()
            return (max_id[0] if max_id else 0) + 1
    
    # ==================== DEVIS ====================
    
    @property
    def devis_list(self) -> List[Devis]:
        """Récupère tous les devis"""
        with db_manager.get_session() as session:
            devis_models = session.query(DevisModel).all()
            devis_list = []
            for d in devis_models:
                lignes = []
                if d.lignes:
                    for ligne_data in d.lignes:
                        composants = []
                        if 'composants' in ligne_data and ligne_data['composants']:
                            for comp_data in ligne_data['composants']:
                                composants.append(ComposantOuvrage(
                                    article_id=comp_data['article_id'],
                                    quantite=comp_data['quantite'],
                                    designation=comp_data.get('designation', ''),
                                    unite=comp_data.get('unite', ''),
                                    prix_unitaire=comp_data.get('prix_unitaire', 0.0)
                                ))
                        ligne_data['composants'] = composants
                        lignes.append(LigneDevis(**ligne_data))
                
                devis_list.append(Devis(
                    numero=d.numero,
                    date=d.date,
                    client_id=d.client_id,
                    objet=d.objet or "",
                    lignes=lignes,
                    coefficient_marge=d.coefficient_marge,
                    remise=d.remise,
                    tva=d.tva,
                    validite=d.validite,
                    notes=d.notes or "",
                    conditions=d.conditions or "",
                    statut=d.statut
                ))
            return devis_list
    
    def get_devis_by_numero(self, numero: str) -> Optional[Devis]:
        """Récupère un devis par son numéro"""
        with db_manager.get_session() as session:
            d = session.query(DevisModel).filter_by(numero=numero).first()
            if d:
                lignes = []
                if d.lignes:
                    for ligne_data in d.lignes:
                        composants = []
                        if 'composants' in ligne_data and ligne_data['composants']:
                            for comp_data in ligne_data['composants']:
                                composants.append(ComposantOuvrage(
                                    article_id=comp_data['article_id'],
                                    quantite=comp_data['quantite'],
                                    designation=comp_data.get('designation', ''),
                                    unite=comp_data.get('unite', ''),
                                    prix_unitaire=comp_data.get('prix_unitaire', 0.0)
                                ))
                        ligne_data['composants'] = composants
                        lignes.append(LigneDevis(**ligne_data))
                
                return Devis(
                    numero=d.numero,
                    date=d.date,
                    client_id=d.client_id,
                    objet=d.objet or "",
                    lignes=lignes,
                    coefficient_marge=d.coefficient_marge,
                    remise=d.remise,
                    tva=d.tva,
                    validite=d.validite,
                    notes=d.notes or "",
                    conditions=d.conditions or "",
                    statut=d.statut
                )
            logger.warning(f"Devis not found: {numero}")
            return None
    
    def add_devis(self, devis: Devis):
        """Ajoute un nouveau devis"""
        with db_manager.get_session() as session:
            lignes_json = []
            for ligne in devis.lignes:
                ligne_dict = asdict(ligne)
                # Convertir les composants en dict si ce sont des dataclasses
                if ligne_dict['composants']:
                    ligne_dict['composants'] = [
                        asdict(c) if hasattr(c, '__dataclass_fields__') else c 
                        for c in ligne_dict['composants']
                    ]
                lignes_json.append(ligne_dict)
            
            d_model = DevisModel(
                numero=devis.numero,
                date=devis.date,
                client_id=devis.client_id,
                objet=devis.objet,
                lignes=lignes_json,
                coefficient_marge=devis.coefficient_marge,
                remise=devis.remise,
                tva=devis.tva,
                validite=devis.validite,
                notes=devis.notes,
                conditions=devis.conditions,
                statut=devis.statut
            )
            session.add(d_model)
        logger.info(f"Devis added: {devis.numero}")
    
    def update_devis(self, devis: Devis):
        """Met à jour un devis existant"""
        with db_manager.get_session() as session:
            d = session.query(DevisModel).filter_by(numero=devis.numero).first()
            if d:
                lignes_json = []
                for ligne in devis.lignes:
                    ligne_dict = asdict(ligne)
                    # Les composants sont déjà convertis en dict par asdict()
                    lignes_json.append(ligne_dict)
                
                d.date = devis.date
                d.client_id = devis.client_id
                d.objet = devis.objet
                d.lignes = lignes_json
                d.coefficient_marge = devis.coefficient_marge
                d.remise = devis.remise
                d.tva = devis.tva
                d.validite = devis.validite
                d.notes = devis.notes
                d.conditions = devis.conditions
                d.statut = devis.statut
                logger.info(f"Devis updated: {devis.numero}")
            else:
                raise ResourceNotFoundError(f"Devis not found: {devis.numero}")
    
    def delete_devis(self, numero: str):
        """Supprime un devis"""
        with db_manager.get_session() as session:
            d = session.query(DevisModel).filter_by(numero=numero).first()
            if d:
                session.delete(d)
                logger.info(f"Devis deleted: {numero}")
            else:
                raise ResourceNotFoundError(f"Devis not found: {numero}")
    
    def get_next_devis_number(self) -> str:
        """Génère le prochain numéro de devis"""
        year = datetime.now().year
        with db_manager.get_session() as session:
            count = session.query(DevisModel).filter(
                DevisModel.date.like(f"{year}%")
            ).count()
        return f"DEV-{year}-{count + 1:04d}"
    
    # ==================== PROJETS ====================
    
    @property
    def projets(self) -> List[Projet]:
        """Récupère tous les projets"""
        with db_manager.get_session() as session:
            projets_models = session.query(ProjetModel).all()
            projets = []
            for p in projets_models:
                depenses = []
                if p.depenses_reelles:
                    for dep_data in p.depenses_reelles:
                        depenses.append(DepenseReelle(**dep_data))
                
                projets.append(Projet(
                    id=p.id,
                    numero=p.numero,
                    devis_numeros=p.devis_numeros or [],
                    client_id=p.client_id,
                    date_creation=p.date_creation,
                    date_debut=p.date_debut or "",
                    date_fin_prevue=p.date_fin_prevue or "",
                    date_fin_reelle=p.date_fin_reelle or "",
                    statut=p.statut,
                    adresse_chantier=p.adresse_chantier or "",
                    notes=p.notes or "",
                    depenses_reelles=depenses
                ))
            return projets
    
    def get_projet_by_id(self, projet_id: int) -> Optional[Projet]:
        """Récupère un projet par son ID"""
        with db_manager.get_session() as session:
            p = session.query(ProjetModel).filter_by(id=projet_id).first()
            if p:
                depenses = []
                if p.depenses_reelles:
                    for dep_data in p.depenses_reelles:
                        depenses.append(DepenseReelle(**dep_data))
                
                return Projet(
                    id=p.id,
                    numero=p.numero,
                    devis_numeros=p.devis_numeros or [],
                    client_id=p.client_id,
                    date_creation=p.date_creation,
                    date_debut=p.date_debut or "",
                    date_fin_prevue=p.date_fin_prevue or "",
                    date_fin_reelle=p.date_fin_reelle or "",
                    statut=p.statut,
                    adresse_chantier=p.adresse_chantier or "",
                    notes=p.notes or "",
                    depenses_reelles=depenses
                )
            return None
    
    def get_projet_by_numero(self, numero: str) -> Optional[Projet]:
        """Récupère un projet par son numéro"""
        with db_manager.get_session() as session:
            p = session.query(ProjetModel).filter_by(numero=numero).first()
            if p:
                depenses = []
                if p.depenses_reelles:
                    for dep_data in p.depenses_reelles:
                        depenses.append(DepenseReelle(**dep_data))
                
                return Projet(
                    id=p.id,
                    numero=p.numero,
                    devis_numeros=p.devis_numeros or [],
                    client_id=p.client_id,
                    date_creation=p.date_creation,
                    date_debut=p.date_debut or "",
                    date_fin_prevue=p.date_fin_prevue or "",
                    date_fin_reelle=p.date_fin_reelle or "",
                    statut=p.statut,
                    adresse_chantier=p.adresse_chantier or "",
                    notes=p.notes or "",
                    depenses_reelles=depenses
                )
            return None
    
    def add_projet(self, projet: Projet):
        """Ajoute un nouveau projet"""
        with db_manager.get_session() as session:
            depenses_json = [asdict(d) for d in projet.depenses_reelles] if projet.depenses_reelles else []
            p_model = ProjetModel(
                id=projet.id,
                numero=projet.numero,
                devis_numeros=projet.devis_numeros,
                client_id=projet.client_id,
                date_creation=projet.date_creation,
                date_debut=projet.date_debut,
                date_fin_prevue=projet.date_fin_prevue,
                date_fin_reelle=projet.date_fin_reelle,
                statut=projet.statut,
                adresse_chantier=projet.adresse_chantier,
                notes=projet.notes,
                depenses_reelles=depenses_json
            )
            session.add(p_model)
        logger.info(f"Projet added: {projet.numero}")
    
    def update_projet(self, projet: Projet):
        """Met à jour un projet existant"""
        with db_manager.get_session() as session:
            p = session.query(ProjetModel).filter_by(id=projet.id).first()
            if p:
                depenses_json = [asdict(d) for d in projet.depenses_reelles] if projet.depenses_reelles else []
                p.numero = projet.numero
                p.devis_numeros = projet.devis_numeros
                p.client_id = projet.client_id
                p.date_creation = projet.date_creation
                p.date_debut = projet.date_debut
                p.date_fin_prevue = projet.date_fin_prevue
                p.date_fin_reelle = projet.date_fin_reelle
                p.statut = projet.statut
                p.adresse_chantier = projet.adresse_chantier
                p.notes = projet.notes
                p.depenses_reelles = depenses_json
                logger.info(f"Projet updated: {projet.id}")
            else:
                raise ResourceNotFoundError(f"Projet not found: {projet.id}")
    
    def delete_projet(self, projet_id: int):
        """Supprime un projet"""
        with db_manager.get_session() as session:
            p = session.query(ProjetModel).filter_by(id=projet_id).first()
            if p:
                session.delete(p)
                logger.info(f"Projet deleted: {projet_id}")
            else:
                raise ResourceNotFoundError(f"Projet not found: {projet_id}")
    
    def get_next_projet_number(self) -> str:
        """Génère le prochain numéro de projet"""
        year = datetime.now().year
        with db_manager.get_session() as session:
            count = session.query(ProjetModel).filter(
                ProjetModel.date_creation.like(f"{year}%")
            ).count()
        return f"PROJ-{year}-{count + 1:04d}"
    
    # ==================== USERS ====================
    
    @property
    def users(self) -> List[User]:
        """Récupère tous les utilisateurs"""
        with db_manager.get_session() as session:
            users_models = session.query(UserModel).all()
            return [
                User.from_dict({
                    'id': u.id,
                    'username': u.username,
                    'password_hash': u.password_hash,
                    'salt': u.salt,
                    'role': u.role,
                    'nom': u.nom or "",
                    'prenom': u.prenom or "",
                    'email': u.email or "",
                    'actif': u.actif,
                    'date_creation': u.date_creation or "",
                    'derniere_connexion': u.derniere_connexion or ""
                })
                for u in users_models
            ]
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        with db_manager.get_session() as session:
            u = session.query(UserModel).filter_by(id=user_id).first()
            if u:
                return User.from_dict({
                    'id': u.id,
                    'username': u.username,
                    'password_hash': u.password_hash,
                    'salt': u.salt,
                    'role': u.role,
                    'nom': u.nom or "",
                    'prenom': u.prenom or "",
                    'email': u.email or "",
                    'actif': u.actif,
                    'date_creation': u.date_creation or "",
                    'derniere_connexion': u.derniere_connexion or ""
                })
            logger.warning(f"User not found: {user_id}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        with db_manager.get_session() as session:
            u = session.query(UserModel).filter_by(username=username).first()
            if u:
                return User.from_dict({
                    'id': u.id,
                    'username': u.username,
                    'password_hash': u.password_hash,
                    'salt': u.salt,
                    'role': u.role,
                    'nom': u.nom or "",
                    'prenom': u.prenom or "",
                    'email': u.email or "",
                    'actif': u.actif,
                    'date_creation': u.date_creation or "",
                    'derniere_connexion': u.derniere_connexion or ""
                })
            logger.debug(f"User not found by username: {username}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        with db_manager.get_session() as session:
            u = session.query(UserModel).filter_by(email=email).first()
            if u:
                return User.from_dict({
                    'id': u.id,
                    'username': u.username,
                    'password_hash': u.password_hash,
                    'salt': u.salt,
                    'role': u.role,
                    'nom': u.nom or "",
                    'prenom': u.prenom or "",
                    'email': u.email or "",
                    'actif': u.actif,
                    'date_creation': u.date_creation or "",
                    'derniere_connexion': u.derniere_connexion or ""
                })
            logger.debug(f"User not found by email: {email}")
            return None
    
    def add_user(self, user: User):
        """Ajoute un nouvel utilisateur"""
        if self.get_user_by_username(user.username):
            raise ValueError(f"Un utilisateur avec le nom '{user.username}' existe déjà")
        if self.get_user_by_email(user.email):
            raise ValueError(f"Un utilisateur avec l'email '{user.email}' existe déjà")
        
        with db_manager.get_session() as session:
            user_data = user.to_dict()
            u_model = UserModel(
                id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                salt=user_data['salt'],
                role=user_data['role'],
                nom=user_data.get('nom', ''),
                prenom=user_data.get('prenom', ''),
                email=user_data.get('email', ''),
                actif=user_data.get('actif', True),
                date_creation=user_data.get('date_creation', ''),
                derniere_connexion=user_data.get('derniere_connexion', '')
            )
            session.add(u_model)
        logger.info(f"User added: {user.username}")
    
    def update_user(self, user: User):
        """Met à jour un utilisateur existant"""
        with db_manager.get_session() as session:
            u = session.query(UserModel).filter_by(id=user.id).first()
            if u:
                user_data = user.to_dict()
                u.username = user_data['username']
                u.password_hash = user_data['password_hash']
                u.salt = user_data['salt']
                u.role = user_data['role']
                u.nom = user_data.get('nom', '')
                u.prenom = user_data.get('prenom', '')
                u.email = user_data.get('email', '')
                u.actif = user_data.get('actif', True)
                u.date_creation = user_data.get('date_creation', '')
                u.derniere_connexion = user_data.get('derniere_connexion', '')
                logger.info(f"User updated: {user.username}")
            else:
                raise ResourceNotFoundError(f"User not found: {user.id}")
    
    # ==================== MÉTHODES DE COMPATIBILITÉ ====================
    
    def save_data(self):
        """
        Méthode de compatibilité (ne fait rien car les données sont automatiquement sauvegardées)
        """
        pass
    
    def load_data(self):
        """
        Méthode de compatibilité (ne fait rien car les données sont chargées à la demande)
        """
        pass
    
    def init_demo_data(self):
        """Initialise des données de démonstration si la base est vide"""
        if not self.clients and not self.articles:
            logger.info("Initializing demo data in PostgreSQL")
            
            # Ajouter des fournisseurs
            fournisseurs = [
                Fournisseur(id=1, nom="Placo France", specialite="Plâtrerie", telephone="0140506070", email="contact@placo.fr", remise=0.0),
                Fournisseur(id=2, nom="Bois & Menuiserie", specialite="Menuiserie", telephone="0145678901", email="contact@boisetmenu.fr", remise=0.0),
            ]
            for f in fournisseurs:
                self.add_fournisseur(f)
            
            # Ajouter des articles
            articles = [
                Article(id=1, reference="BA13-STD", designation="Plaque BA13 standard", unite="m²", prix_unitaire=8.50, type_article="materiau", fournisseur_id=1, description="Plaque de plâtre standard", categorie="platrerie"),
                Article(id=2, reference="RAIL-M48", designation="Rail métallique 48mm", unite="ml", prix_unitaire=2.20, type_article="materiau", fournisseur_id=1, categorie="platrerie"),
                Article(id=10, reference="VIS-PLACO", designation="Vis pour placo (boîte de 1000)", unite="u", prix_unitaire=8.50, type_article="fourniture", fournisseur_id=1, categorie="platrerie"),
                Article(id=100, reference="MO-PLAT-QUAL", designation="Main d'œuvre plâtrier qualifié", unite="h", prix_unitaire=45.00, type_article="main_oeuvre", fournisseur_id=0, categorie="platrerie"),
            ]
            for a in articles:
                self.add_article(a)
            
            # Ajouter des clients
            clients = [
                Client(id=1, nom="Dupont", prenom="Jean", entreprise="Maison Dupont", adresse="12 rue de la Paix", cp="75001", ville="Paris", telephone="0612345678", email="j.dupont@email.com"),
                Client(id=2, nom="Martin", prenom="Sophie", entreprise="SARL Martin Rénovation", adresse="45 avenue des Champs", cp="69000", ville="Lyon", telephone="0698765432", email="s.martin@email.com"),
            ]
            for c in clients:
                self.add_client(c)
            
            # Ajouter un ouvrage
            ouvrage = Ouvrage(
                id=1,
                reference="CLO-BA13-SIMPLE",
                designation="Cloison BA13 simple face sur rail 48",
                description="Cloison séparative légère, plaque BA13 simple face avec isolation acoustique",
                categorie="platrerie",
                unite="m²",
                composants=[
                    ComposantOuvrage(article_id=1, quantite=1.05, designation="Plaque BA13", unite="m²", prix_unitaire=8.50),
                    ComposantOuvrage(article_id=2, quantite=0.6, designation="Rail métallique", unite="ml", prix_unitaire=2.20),
                    ComposantOuvrage(article_id=100, quantite=0.45, designation="MO plâtrier", unite="h", prix_unitaire=45.00),
                ]
            )
            self.add_ouvrage(ouvrage)
            
            # Créer une organisation par défaut
            org = Organisation(
                id=1,
                nom="POCKO construction",
                siret="",
                adresse="1 Rue des Grands Champs",
                cp="00000",
                ville="VILLE",
                telephone="00.00.00.00.00",
                email="",
                site_web="",
                logo_path="",
                date_debut_exercice="",
                date_fin_exercice=""
            )
            self.organisation = org
            
            logger.info("Demo data initialized successfully")
    
    def get_company_info(self) -> dict:
        """Retourne les informations de l'entreprise (pour compatibilité)"""
        org = self.organisation
        return {
            'name': org.nom,
            'address': f"{org.adresse}\n{org.cp} {org.ville}",
            'phone': org.telephone
        }
    
    def save_company_info(self, info: dict):
        """Sauvegarde les informations de l'entreprise (pour compatibilité)"""
        org = self.organisation
        org.nom = info.get('name', org.nom)
        
        # Parse address
        address = info.get('address', '')
        if '\n' in address:
            parts = address.split('\n')
            org.adresse = parts[0]
            if len(parts) > 1:
                cp_ville = parts[1].split(' ', 1)
                if len(cp_ville) == 2:
                    org.cp = cp_ville[0]
                    org.ville = cp_ville[1]
        else:
            org.adresse = address
        
        org.telephone = info.get('phone', org.telephone)
        self.organisation = org
