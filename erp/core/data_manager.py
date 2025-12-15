import json
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from erp.core.models import Client, Fournisseur, Article, Ouvrage, ComposantOuvrage, Devis, LigneDevis, Organisation, Projet, DepenseReelle, User
from erp.core.constants import DATA_DIR_NAME, DATA_FILES
from erp.utils.logger import get_logger
from erp.utils.exceptions import DataPersistenceError, ResourceNotFoundError

logger = get_logger(__name__)

# Singleton instance
_instance = None


class DataManager:
    """Simple data manager: loads/saves JSON and provides lookup helpers."""
    def __new__(cls, data_dir: Optional[Path] = None):
        global _instance
        if _instance is None:
            _instance = super(DataManager, cls).__new__(cls)
            _instance._initialized = False
        return _instance
    
    def __init__(self, data_dir: Optional[Path] = None):
        # Éviter la réinitialisation si déjà initialisé
        if self._initialized:
            return
        
        # Gestion spéciale pour PyInstaller
        import sys
        if getattr(sys, 'frozen', False):
            # Mode exécutable: utiliser le dossier de l'exécutable
            project_root = Path(sys.executable).parent
        else:
            # Mode développement: racine du projet (2 niveaux au-dessus de core/)
            project_root = Path(__file__).resolve().parent.parent.parent
        
        self.data_dir: Path = Path(data_dir) if data_dir else project_root / DATA_DIR_NAME
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.clients: List[Client] = []
        self.fournisseurs: List[Fournisseur] = []
        self.articles: List[Article] = []
        self.ouvrages: List[Ouvrage] = []
        self.devis_list: List[Devis] = []
        self.projets: List = []  # Will hold Projet instances
        self.organisation: Organisation = Organisation()
        self.users: List = []  # Will hold User instances

        logger.info(f"Initializing DataManager with data directory: {self.data_dir}")
        
        self.load_data()
        if not (self.clients or self.ouvrages or self.articles):
            logger.info("No existing data found, initializing demo data")
            self.init_demo_data()
            self.save_data()  # Persist demo data
        
        self._initialized = True

    def load_data(self):
        try:
            # Clear existing data first
            self.clients = []
            self.fournisseurs = []
            self.articles = []
            self.ouvrages = []
            self.devis_list = []
            self.projets = []
            self.organisation = Organisation()
            self.users = []
            
            # Load organisation from organisation.json
            org_path = self.data_dir / "organisation.json"
            if org_path.exists():
                with org_path.open("r", encoding="utf-8-sig") as f:
                    org_data = json.load(f)
                    # Check if new format (with separate fields) or old format (with "name", "address", "phone")
                    if "nom" in org_data:
                        # New format with separate fields
                        self.organisation.id = org_data.get("id", 1)
                        self.organisation.nom = org_data.get("nom", "")
                        self.organisation.siret = org_data.get("siret", "")
                        self.organisation.adresse = org_data.get("adresse", "")
                        self.organisation.cp = org_data.get("cp", "")
                        self.organisation.ville = org_data.get("ville", "")
                        self.organisation.telephone = org_data.get("telephone", "")
                        self.organisation.email = org_data.get("email", "")
                        self.organisation.site_web = org_data.get("site_web", "")
                        self.organisation.logo_path = org_data.get("logo_path", "")
                    else:
                        # Old format: parse "address" field with embedded cp/ville
                        self.organisation.nom = org_data.get("name", "")
                        address_parts = org_data.get("address", "").split("\n")
                        if len(address_parts) == 2:
                            self.organisation.adresse = address_parts[0]
                            cp_city = address_parts[1].split()
                            if cp_city:
                                self.organisation.cp = cp_city[0]
                                self.organisation.ville = " ".join(cp_city[1:])
                        else:
                            self.organisation.adresse = org_data.get("address", "")
                        self.organisation.telephone = org_data.get("phone", "")
            
            clients_path = self.data_dir / "clients.json"
            if clients_path.exists():
                with clients_path.open("r", encoding="utf-8-sig") as f:
                    self.clients = [Client(**c) for c in json.load(f)]

            articles_path = self.data_dir / "articles.json"
            if articles_path.exists():
                with articles_path.open("r", encoding="utf-8-sig") as f:
                    self.articles = [Article(**a) for a in json.load(f)]

            ouvrages_path = self.data_dir / "ouvrages.json"
            if ouvrages_path.exists():
                with ouvrages_path.open("r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for ouv in data:
                        comps = [ComposantOuvrage(**c) for c in ouv.get("composants", [])]
                        ouv["composants"] = comps
                        # Remove coefficient_marge if present (migrated to LigneDevis)
                        ouv.pop("coefficient_marge", None)
                        self.ouvrages.append(Ouvrage(**ouv))

            devis_path = self.data_dir / "devis.json"
            if devis_path.exists():
                with devis_path.open("r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for d in data:
                        try:
                            # Convertir les composants en objets ComposantOuvrage
                            lignes = []
                            for l in d.get("lignes", []):
                                # Convertir les composants du dictionnaire en objets ComposantOuvrage
                                if "composants" in l and l["composants"]:
                                    l["composants"] = [ComposantOuvrage(**c) for c in l["composants"]]
                                lignes.append(LigneDevis(**l))
                            d["lignes"] = lignes
                            # Ensure coefficient_marge exists (migration for old devis)
                            if "coefficient_marge" not in d:
                                d["coefficient_marge"] = 1.35
                            self.devis_list.append(Devis(**d))
                        except Exception as e:
                            logger.error(f"Error loading devis {d.get('numero', 'unknown')}: {e}", exc_info=True)
            
            # Load projets from projets.json
            projets_path = self.data_dir / "projets.json"
            if projets_path.exists():
                with projets_path.open("r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for p in data:
                        try:
                            # Convertir les dépenses réelles en objets DepenseReelle
                            if "depenses_reelles" in p and p["depenses_reelles"]:
                                p["depenses_reelles"] = [DepenseReelle(**d) for d in p["depenses_reelles"]]
                            # Migration: convertir devis_numero (string) en devis_numeros (list)
                            if "devis_numero" in p and "devis_numeros" not in p:
                                p["devis_numeros"] = [p.pop("devis_numero")]
                            self.projets.append(Projet(**p))
                        except Exception as e:
                            logger.error(f"Error loading projet {p.get('numero', 'unknown')}: {e}", exc_info=True)
            
            # Load users from users.json
            users_path = self.data_dir / "users.json"
            if users_path.exists():
                with users_path.open("r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    for u in data:
                        try:
                            self.users.append(User.from_dict(u))
                        except Exception as e:
                            logger.error(f"Error loading user {u.get('username', 'unknown')}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Failed to load data: {e}", exc_info=True)
            raise DataPersistenceError(f"Impossible de charger les données: {e}", {"data_dir": str(self.data_dir)})

    def save_data(self):
        try:
            # Save organisation to organisation.json
            org_data = {
                "name": self.organisation.nom,
                "address": f"{self.organisation.adresse}\n{self.organisation.cp} {self.organisation.ville}",
                "phone": self.organisation.telephone
            }
            with (self.data_dir / "organisation.json").open("w", encoding="utf-8") as f:
                json.dump(org_data, f, ensure_ascii=False, indent=2)

            with (self.data_dir / "clients.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(c) for c in self.clients], f, ensure_ascii=False, indent=2)

            with (self.data_dir / "fournisseurs.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(f) for f in self.fournisseurs], f, ensure_ascii=False, indent=2)

            with (self.data_dir / "articles.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(a) for a in self.articles], f, ensure_ascii=False, indent=2)

            with (self.data_dir / "ouvrages.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(o) for o in self.ouvrages], f, ensure_ascii=False, indent=2)

            with (self.data_dir / "devis.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(d) for d in self.devis_list], f, ensure_ascii=False, indent=2)
            
            with (self.data_dir / "projets.json").open("w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in self.projets], f, ensure_ascii=False, indent=2)
            
            with (self.data_dir / "users.json").open("w", encoding="utf-8") as f:
                json.dump([u.to_dict() for u in self.users], f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Failed to save data: {e}", exc_info=True)
            raise DataPersistenceError(f"Impossible de sauvegarder les données: {e}", {"data_dir": str(self.data_dir)})

    # Convenience API used by the UI
    def get_next_devis_number(self) -> str:
        year = __import__("datetime").datetime.now().year
        count = len([d for d in self.devis_list if getattr(d, 'date', '').startswith(str(year))]) + 1
        return f"DEV-{year}-{count:04d}"
    
    def get_next_projet_number(self) -> str:
        """Génère le prochain numéro de projet"""
        year = __import__("datetime").datetime.now().year
        count = len([p for p in self.projets if p.date_creation.startswith(str(year))]) + 1
        return f"PROJ-{year}-{count:04d}"

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID"""
        client = next((c for c in self.clients if c.id == client_id), None)
        if not client:
            logger.warning(f"Client not found: {client_id}")
        return client
    
    def get_devis_by_numero(self, numero: str) -> Optional[Devis]:
        """Récupère un devis par son numéro"""
        devis = next((d for d in self.devis_list if d.numero == numero), None)
        if not devis:
            logger.warning(f"Devis not found: {numero}")
        return devis

    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        return next((a for a in self.articles if a.id == article_id), None)

    def get_fournisseur_by_id(self, fournisseur_id: int) -> Optional[Fournisseur]:
        return next((f for f in self.fournisseurs if f.id == fournisseur_id), None)

    def get_ouvrage_by_id(self, ouvrage_id: int) -> Optional[Ouvrage]:
        return next((o for o in self.ouvrages if o.id == ouvrage_id), None)
    
    def get_projet_by_id(self, projet_id: int) -> Optional[Projet]:
        """Récupère un projet par son ID"""
        return next((p for p in self.projets if p.id == projet_id), None)
    
    def get_projet_by_numero(self, numero: str) -> Optional[Projet]:
        """Récupère un projet par son numéro"""
        return next((p for p in self.projets if p.numero == numero), None)

    def get_next_ouvrage_id(self) -> int:
        return max((o.id for o in self.ouvrages), default=0) + 1

    def init_demo_data(self):
        # Minimal demo data to make the UI functional
        self.fournisseurs = [
            Fournisseur(id=1, nom="Placo France", specialite="Plâtrerie", telephone="0140506070", email="contact@placo.fr", remise=0.0),
            Fournisseur(id=2, nom="Bois & Menuiserie", specialite="Menuiserie", telephone="0145678901", email="contact@boisetmenu.fr", remise=0.0),
        ]

        self.articles = [
            Article(id=1, reference="BA13-STD", designation="Plaque BA13 standard", unite="m²", prix_unitaire=8.50, type_article="materiau", fournisseur_id=1, description="Plaque de plâtre standard"),
            Article(id=2, reference="RAIL-M48", designation="Rail métallique 48mm", unite="ml", prix_unitaire=2.20, type_article="materiau", fournisseur_id=1),
            Article(id=10, reference="VIS-PLACO", designation="Vis pour placo (boîte de 1000)", unite="u", prix_unitaire=8.50, type_article="fourniture", fournisseur_id=1),
            Article(id=100, reference="MO-PLAT-QUAL", designation="Main d'œuvre plâtrier qualifié", unite="h", prix_unitaire=45.00, type_article="main_oeuvre", fournisseur_id=0),
        ]

        self.clients = [
            Client(id=1, nom="Dupont", prenom="Jean", entreprise="Maison Dupont", adresse="12 rue de la Paix", cp="75001", ville="Paris", telephone="0612345678", email="j.dupont@email.com"),
            Client(id=2, nom="Martin", prenom="Sophie", entreprise="SARL Martin Rénovation", adresse="45 avenue des Champs", cp="69000", ville="Lyon", telephone="0698765432", email="s.martin@email.com"),
        ]

        # Example ouvrage composed of articles
        self.ouvrages = [
            Ouvrage(
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
        ]

        # Ensure composants reflect current article data
        for ouvrage in self.ouvrages:
            for composant in ouvrage.composants:
                art = self.get_article_by_id(composant.article_id)
                if art:
                    composant.designation = art.designation
                    composant.unite = art.unite
                    composant.prix_unitaire = art.prix_unitaire

        # no saved devis initially

    def get_company_info(self) -> dict:
        """Return company information from `data/company.json` if present, otherwise default values."""
        company_file = Path(self.data_dir) / 'company.json'
        if company_file.exists():
            try:
                with company_file.open('r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        # sensible defaults
        return {
            'name': 'POCKO construction',
            'address': '1 Rue des Grands Champs\n00000 VILLE',
            'phone': '00.00.00.00.00'
        }

    def save_company_info(self, info: dict):
        company_file = Path(self.data_dir) / 'company.json'
        company_file.parent.mkdir(parents=True, exist_ok=True)
        with company_file.open('w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    
    # User management methods
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        user = next((u for u in self.users if u.id == user_id), None)
        if not user:
            logger.warning(f"User not found: {user_id}")
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        user = next((u for u in self.users if u.username == username), None)
        if not user:
            logger.debug(f"User not found by username: {username}")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        user = next((u for u in self.users if u.email == email), None)
        if not user:
            logger.debug(f"User not found by email: {email}")
        return user
    
    def add_user(self, user: User) -> None:
        """Ajoute un nouvel utilisateur et sauvegarde"""
        if self.get_user_by_username(user.username):
            raise ValueError(f"Un utilisateur avec le nom '{user.username}' existe déjà")
        if self.get_user_by_email(user.email):
            raise ValueError(f"Un utilisateur avec l'email '{user.email}' existe déjà")
        
        self.users.append(user)
        self.save_data()
        logger.info(f"User added: {user.username}")
    
    def update_user(self, user: User) -> None:
        """Met à jour un utilisateur existant et sauvegarde"""
        existing = self.get_user_by_id(user.id)
        if not existing:
            raise ResourceNotFoundError(f"Utilisateur non trouvé: {user.id}")
        
        # Replace the user in the list
        for i, u in enumerate(self.users):
            if u.id == user.id:
                self.users[i] = user
                break
        
        self.save_data()
        logger.info(f"User updated: {user.username}")
