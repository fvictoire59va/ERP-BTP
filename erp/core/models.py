from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum
from datetime import datetime

from erp.core.constants import (
    DEFAULT_TVA_RATE,
    DEFAULT_COEFFICIENT_MARGE,
    DEVIS_STATUS_COLORS,
    MIN_COEFFICIENT_MARGE,
    MAX_COEFFICIENT_MARGE,
    DATE_FORMAT,
)


class CategorieOuvrage(Enum):
    PLATRERIE = "platrerie"
    MENUISERIE_INT = "menuiserie_int"
    MENUISERIE_EXT = "menuiserie_ext"
    FAUX_PLAFOND = "faux_plafond"
    AGENCEMENT = "agencement"
    ISOLATION = "isolation"
    PEINTURE = "peinture"


class TypeArticle(Enum):
    MATERIAU = "materiau"
    FOURNITURE = "fourniture"
    MAIN_OEUVRE = "main_oeuvre"
    CONSOMMABLE = "consommable"


@dataclass
class Organisation:
    """Informations sur l'organisation/entreprise"""
    id: int = 1
    nom: str = ""
    siret: str = ""
    adresse: str = ""
    cp: str = ""
    ville: str = ""
    telephone: str = ""
    email: str = ""
    site_web: str = ""
    logo_path: str = ""
    date_debut_exercice: str = ""
    date_fin_exercice: str = ""


@dataclass
class Client:
    id: int
    nom: str
    prenom: str
    entreprise: str
    adresse: str
    cp: str
    ville: str
    telephone: str
    email: str
    
    def get_full_name(self) -> str:
        """Retourne le nom complet du client"""
        return f"{self.prenom} {self.nom}"
    
    def get_display_name(self) -> str:
        """Retourne le nom d'affichage avec entreprise"""
        return f"{self.nom} {self.prenom} - {self.entreprise}"
    
    def is_valid(self) -> bool:
        """Vérifie si le client a les informations minimales"""
        return bool(self.nom and self.prenom)


@dataclass
@dataclass
class Fournisseur:
    id: int
    nom: str
    specialite: str = ""
    telephone: str = ""
    email: str = ""
    remise: float = 0.0


@dataclass
class Article:
    id: int
    reference: str
    designation: str
    unite: str  # m², ml, u, h (heure), forfait
    prix_unitaire: float
    type_article: str  # materiau, fourniture, main_oeuvre, consommable
    fournisseur_id: int
    description: str = ""
    categorie: str = "general"  # platrerie, menuiserie_int, menuiserie_ext, faux_plafond, agencement, isolation, peinture, general
    
    def get_display_text(self) -> str:
        """Retourne le texte d'affichage de l'article"""
        return f"{self.reference} - {self.designation}"
    
    def calculate_total(self, quantite: float) -> float:
        """Calcule le prix total pour une quantité donnée"""
        return self.prix_unitaire * quantite
    
    def is_valid(self) -> bool:
        """Vérifie si l'article a les informations minimales"""
        return bool(self.reference and self.designation and self.prix_unitaire >= 0)


@dataclass
class ComposantOuvrage:
    """Composant d'un ouvrage : un article avec sa quantité"""
    article_id: int
    quantite: float  # Quantité par unité d'ouvrage
    designation: str = ""  # Sera rempli automatiquement
    unite: str = ""
    prix_unitaire: float = 0.0

    def prix_total(self) -> float:
        return self.quantite * self.prix_unitaire


@dataclass
class Ouvrage:
    """Un ouvrage est un ensemble d'articles qui forment un tout"""
    id: int
    reference: str
    designation: str
    description: str
    categorie: str  # platrerie, menuiserie_int, etc. (catégorie principale)
    sous_categorie: str = ""  # plaques_platre, ossature, etc. (sous-catégorie optionnelle)
    unite: str = ""  # m², ml, u, forfait
    composants: List[ComposantOuvrage] = field(default_factory=list)

    @property
    def prix_revient_unitaire(self) -> float:
        """Prix de revient pour une unité d'ouvrage"""
        return sum(comp.prix_total() for comp in self.composants)
    
    def calculate_prix_vente(self, coefficient: float = DEFAULT_COEFFICIENT_MARGE) -> float:
        """
        Calcule le prix de vente unitaire avec coefficient de marge.
        
        Args:
            coefficient: Coefficient multiplicateur (par défaut depuis constantes)
            
        Returns:
            Prix de vente unitaire
        """
        return self.prix_revient_unitaire * coefficient
    
    def get_display_text(self) -> str:
        """Retourne le texte d'affichage de l'ouvrage"""
        return f"{self.reference} - {self.designation}"
    
    def is_valid(self) -> bool:
        """Vérifie si l'ouvrage a les informations minimales"""
        return bool(self.reference and self.designation and self.composants)


@dataclass
class LigneDevis:
    """Ligne de devis : un ouvrage avec une quantité"""
    type: str = "ouvrage"  # Type de ligne: "ouvrage", "texte" ou "chapitre"
    id: int = 0  # ID unique pour cette ligne
    niveau: int = 1  # Niveau hiérarchique (1, 2, 3) pour chapitres et textes
    
    # Champs pour type "ouvrage"
    ouvrage_id: int = 0
    designation: str = ""
    description: str = ""
    quantite: float = 0.0
    unite: str = ""
    prix_unitaire: float = 0.0  # Prix de vente unitaire de l'ouvrage
    composants: List[ComposantOuvrage] = field(default_factory=list)  # Composantes modifiées pour cette ligne
    
    # Champs pour type "chapitre"
    titre: str = ""
    
    # Champs pour type "texte"
    texte: str = ""

    @property
    def prix_ht(self) -> float:
        if self.type == "ouvrage":
            return self.quantite * self.prix_unitaire
        return 0.0


@dataclass
class Devis:
    numero: str
    date: str
    client_id: int
    objet: str = ""  # Objet du devis
    lignes: List[LigneDevis] = field(default_factory=list)  # Contient chapitres, lignes devis, et lignes texte
    coefficient_marge: float = DEFAULT_COEFFICIENT_MARGE  # Coefficient de marge global pour tout le devis
    remise: float = 0.0  # Remise en pourcentage au niveau du devis
    tva: float = DEFAULT_TVA_RATE
    validite: int = 30  # jours
    notes: str = ""
    conditions: str = ""
    statut: str = "en cours"  # Statut du devis: "en cours", "envoyé", "refusé", "accepté"

    @property
    def total_ht(self) -> float:
        """Total HT = somme des lignes de type 'ouvrage' uniquement"""
        return sum(ligne.prix_ht for ligne in self.lignes if ligne.type == "ouvrage")

    @property
    def total_tva(self) -> float:
        return self.total_ht * (self.tva / 100)

    @property
    def total_ttc(self) -> float:
        return self.total_ht + self.total_tva
    
    def calculate_totals(self) -> dict:
        """
        Calcule tous les totaux du devis.
        
        Returns:
            dict: {'ht': float, 'tva': float, 'ttc': float}
        """
        total_ht = self.total_ht
        total_tva = self.total_tva
        total_ttc = self.total_ttc
        
        return {
            'ht': total_ht,
            'tva': total_tva,
            'ttc': total_ttc
        }
    
    def get_total_heures_main_oeuvre(self) -> float:
        """
        Calcule le total des heures de main d'œuvre dans le devis.
        Parcourt toutes les lignes de type ouvrage et additionne les heures des composants de type main_oeuvre.
        
        Returns:
            float: Total des heures de main d'œuvre
        """
        total_heures = 0.0
        for ligne in self.lignes:
            if ligne.type == "ouvrage" and hasattr(ligne, 'composants'):
                for comp in ligne.composants:
                    # Si le composant est de type main_oeuvre et unité en heures
                    if comp.unite == 'h':
                        total_heures += comp.quantite * ligne.quantite
        return total_heures


@dataclass
class DepenseReelle:
    """Représente une dépense réelle sur un chantier"""
    id: int
    type_depense: str  # 'materiau', 'main_oeuvre', 'fourniture', 'consommable'
    designation: str
    quantite: float
    unite: str
    prix_unitaire: float
    date: str
    article_id: int = 0  # Lien vers l'article si applicable
    notes: str = ""
    
    @property
    def prix_total(self) -> float:
        """Calcule le prix total de la dépense"""
        return self.quantite * self.prix_unitaire


@dataclass
class Projet:
    """Un projet/chantier avec suivi prévisionnel vs réel"""
    id: int
    numero: str  # Numéro unique du projet (ex: PROJ-2025-0001)
    devis_numeros: List[str]  # Liste des numéros de devis rattachés au chantier
    client_id: int
    date_creation: str
    date_debut: str = ""
    date_fin_prevue: str = ""
    date_fin_reelle: str = ""
    statut: str = "en attente"  # en attente, en cours, terminé, annulé
    adresse_chantier: str = ""
    notes: str = ""
    depenses_reelles: List[DepenseReelle] = None  # Dépenses réelles sur le chantier
    
    def __post_init__(self):
        """Initialise les listes si elles sont None"""
        if self.depenses_reelles is None:
            self.depenses_reelles = []
        if isinstance(self.devis_numeros, str):
            # Migration depuis l'ancien format avec un seul devis
            self.devis_numeros = [self.devis_numeros]
    
    def get_previsionnel(self, dm) -> dict:
        """
        Calcule le prévisionnel en agrégeant tous les devis rattachés
        
        Args:
            dm: DataManager pour récupérer les devis
            
        Returns:
            dict: {
                'total_ht': float,
                'total_heures_mo': float,
                'materiaux': List[{article_id, designation, quantite, unite, prix_unitaire, prix_total}],
                'main_oeuvre': List[...],
                'fournitures': List[...],
                'consommables': List[...]
            }
        """
        from collections import defaultdict
        
        # Agrégation des quantités par article_id et type
        agregation = defaultdict(lambda: {
            'article_id': 0,
            'designation': '',
            'quantite': 0.0,
            'unite': '',
            'prix_unitaire': 0.0,
            'type': ''
        })
        
        total_ht = 0.0
        total_heures_mo = 0.0
        
        for devis_numero in self.devis_numeros:
            devis = dm.get_devis_by_numero(devis_numero)
            if not devis:
                continue
                
            total_ht += devis.total_ht
            
            # Parcourir les lignes et composants
            for ligne in devis.lignes:
                if ligne.type == "ouvrage" and hasattr(ligne, 'composants'):
                    for comp in ligne.composants:
                        # Récupérer l'article pour connaître son type
                        article = dm.get_article_by_id(comp.article_id)
                        if not article:
                            continue
                        
                        key = (comp.article_id, article.type_article)
                        
                        if key not in agregation:
                            agregation[key] = {
                                'article_id': comp.article_id,
                                'designation': comp.designation,
                                'quantite': 0.0,
                                'unite': comp.unite,
                                'prix_unitaire': comp.prix_unitaire,
                                'type': article.type_article
                            }
                        
                        # Additionner les quantités (quantité du composant * quantité de la ligne)
                        agregation[key]['quantite'] += comp.quantite * ligne.quantite
                        
                        # Compter les heures de MO
                        if article.type_article == 'main_oeuvre' and comp.unite == 'h':
                            total_heures_mo += comp.quantite * ligne.quantite
        
        # Organiser par type
        result = {
            'total_ht': total_ht,
            'total_heures_mo': total_heures_mo,
            'materiaux': [],
            'main_oeuvre': []
        }
        
        for key, item in agregation.items():
            type_article = item['type']
            item_data = {
                'article_id': item['article_id'],
                'designation': item['designation'],
                'quantite': item['quantite'],
                'unite': item['unite'],
                'prix_unitaire': item['prix_unitaire'],
                'prix_total': item['quantite'] * item['prix_unitaire']
            }
            
            if type_article == 'materiau':
                result['materiaux'].append(item_data)
            elif type_article == 'main_oeuvre':
                result['main_oeuvre'].append(item_data)
        
        return result
    
    def get_reel(self) -> dict:
        """
        Calcule le réel à partir des dépenses enregistrées
        
        Returns:
            dict: Structure identique à get_previsionnel
        """
        from collections import defaultdict
        
        # Agrégation par article_id et type
        agregation = defaultdict(lambda: {
            'article_id': 0,
            'designation': '',
            'quantite': 0.0,
            'unite': '',
            'prix_unitaire': 0.0,
            'type': ''
        })
        
        total_ht = 0.0
        total_heures_mo = 0.0
        
        for depense in self.depenses_reelles:
            key = (depense.article_id, depense.type_depense)
            
            if key not in agregation:
                agregation[key] = {
                    'article_id': depense.article_id,
                    'designation': depense.designation,
                    'quantite': 0.0,
                    'unite': depense.unite,
                    'prix_unitaire': depense.prix_unitaire,
                    'type': depense.type_depense
                }
            
            agregation[key]['quantite'] += depense.quantite
            total_ht += depense.prix_total
            
            if depense.type_depense == 'main_oeuvre' and depense.unite == 'h':
                total_heures_mo += depense.quantite
        
        # Organiser par type
        result = {
            'total_ht': total_ht,
            'total_heures_mo': total_heures_mo,
            'materiaux': [],
            'main_oeuvre': []
        }
        
        for key, item in agregation.items():
            type_depense = item['type']
            item_data = {
                'article_id': item['article_id'],
                'designation': item['designation'],
                'quantite': item['quantite'],
                'unite': item['unite'],
                'prix_unitaire': item['prix_unitaire'],
                'prix_total': item['quantite'] * item['prix_unitaire']
            }
            
            if type_depense == 'materiau':
                result['materiaux'].append(item_data)
            elif type_depense == 'main_oeuvre':
                result['main_oeuvre'].append(item_data)
        
        return result
    
    def get_ecarts(self, dm) -> dict:
        """
        Calcule les écarts entre prévisionnel et réel
        
        Returns:
            dict: {
                'total_ht': {'prev': float, 'reel': float, 'ecart': float, 'ecart_pct': float},
                'total_heures_mo': {...},
                'par_type': {
                    'materiaux': {'prev': float, 'reel': float, 'ecart': float, 'ecart_pct': float},
                    ...
                }
            }
        """
        prev = self.get_previsionnel(dm)
        reel = self.get_reel()
        
        def calc_ecart(p, r):
            ecart = r - p
            ecart_pct = (ecart / p * 100) if p > 0 else 0
            return {
                'prev': p,
                'reel': r,
                'ecart': ecart,
                'ecart_pct': ecart_pct
            }
        
        # Calculer totaux par type
        prev_totaux = {
            'materiaux': sum(item['prix_total'] for item in prev['materiaux']),
            'main_oeuvre': sum(item['prix_total'] for item in prev['main_oeuvre'])
        }
        
        reel_totaux = {
            'materiaux': sum(item['prix_total'] for item in reel['materiaux']),
            'main_oeuvre': sum(item['prix_total'] for item in reel['main_oeuvre'])
        }
        
        return {
            'total_ht': calc_ecart(prev['total_ht'], reel['total_ht']),
            'total_heures_mo': calc_ecart(prev['total_heures_mo'], reel['total_heures_mo']),
            'par_type': {
                'materiaux': calc_ecart(prev_totaux['materiaux'], reel_totaux['materiaux']),
                'main_oeuvre': calc_ecart(prev_totaux['main_oeuvre'], reel_totaux['main_oeuvre'])
            }
        }
    
    def is_valid(self) -> bool:
        """Vérifie si le projet a les informations minimales"""
        return bool(self.numero and self.devis_numeros and self.client_id)
    
    def is_valid(self) -> bool:
        """
        Vérifie si le devis est valide.
        
        Returns:
            bool: True si le devis a des lignes, un client et un numéro
        """
        return bool(
            self.lignes 
            and self.client_id 
            and self.numero
            and MIN_COEFFICIENT_MARGE <= self.coefficient_marge <= MAX_COEFFICIENT_MARGE
        )
    
    def get_status_color(self) -> str:
        """
        Retourne la couleur associée au statut du devis.
        
        Returns:
            str: Code couleur hexadécimal
        """
        return DEVIS_STATUS_COLORS.get(self.statut, '#667eea')
    
    def get_lignes_by_type(self, ligne_type: str) -> List[LigneDevis]:
        """
        Retourne les lignes d'un type spécifique.
        
        Args:
            ligne_type: 'ouvrage', 'chapitre' ou 'texte'
            
        Returns:
            Liste des lignes du type demandé
        """
        return [ligne for ligne in self.lignes if ligne.type == ligne_type]
    
    def get_chapitres(self) -> List[LigneDevis]:
        """Retourne toutes les lignes de type 'chapitre'"""
        return self.get_lignes_by_type("chapitre")
    
    def get_lignes_devis(self) -> List[LigneDevis]:
        """Retourne toutes les lignes de type 'ouvrage'"""
        return self.get_lignes_by_type("ouvrage")
    
    def get_lignes_texte(self) -> List[LigneDevis]:
        """Retourne toutes les lignes de type 'texte'"""
        return self.get_lignes_by_type("texte")
    
    def is_expired(self) -> bool:
        """
        Vérifie si le devis est expiré.
        
        Returns:
            bool: True si la date de validité est dépassée
        """
        try:
            date_devis = datetime.strptime(self.date, DATE_FORMAT)
            date_limite = date_devis.replace(day=date_devis.day + self.validite)
            return datetime.now() > date_limite
        except (ValueError, AttributeError):
            return False
    
    def add_ligne(self, ligne: LigneDevis) -> None:
        """
        Ajoute une ligne au devis.
        
        Args:
            ligne: La ligne à ajouter
        """
        self.lignes.append(ligne)
    
    def remove_ligne(self, ligne_id: int) -> bool:
        """
        Supprime une ligne du devis par son ID.
        
        Args:
            ligne_id: ID de la ligne à supprimer
            
        Returns:
            bool: True si la ligne a été supprimée, False sinon
        """
        initial_length = len(self.lignes)
        self.lignes = [l for l in self.lignes if l.id != ligne_id]
        return len(self.lignes) < initial_length


# === User Authentication Model ===

import hashlib
import secrets


@dataclass
class User:
    """Utilisateur du système avec authentification"""
    id: str
    username: str
    email: str
    password_hash: str
    salt: str
    nom: str = ""
    prenom: str = ""
    role: str = "user"  # user, admin
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    dashboard_configs: List[str] = field(default_factory=list)  # Liste des noms de dashboards sauvegardés
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hashe un mot de passe avec un salt
        
        Returns:
            tuple: (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Utiliser SHA-256 avec le salt
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return pwd_hash, salt
    
    def verify_password(self, password: str) -> bool:
        """Vérifie si le mot de passe est correct"""
        pwd_hash, _ = self.hash_password(password, self.salt)
        return pwd_hash == self.password_hash
    
    def update_last_login(self):
        """Met à jour la date de dernière connexion"""
        self.last_login = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour la sérialisation"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'salt': self.salt,
            'nom': self.nom,
            'prenom': self.prenom,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'dashboard_configs': self.dashboard_configs
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'User':
        """Crée un User depuis un dictionnaire"""
        return User(
            id=data['id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            salt=data['salt'],
            nom=data.get('nom', ''),
            prenom=data.get('prenom', ''),
            role=data.get('role', 'user'),
            active=data.get('active', True),
            created_at=data.get('created_at', datetime.now().isoformat()),
            last_login=data.get('last_login'),
            dashboard_configs=data.get('dashboard_configs', [])
        )
