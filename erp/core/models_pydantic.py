"""
Modèles de données avec Pydantic pour validation automatique
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional
from enum import Enum
from datetime import datetime
import re

from erp.core.constants import (
    DEFAULT_TVA_RATE,
    DEFAULT_COEFFICIENT_MARGE,
    MIN_COEFFICIENT_MARGE,
    MAX_COEFFICIENT_MARGE,
)


class CategorieOuvrage(str, Enum):
    PLATRERIE = "platrerie"
    MENUISERIE_INT = "menuiserie_int"
    MENUISERIE_EXT = "menuiserie_ext"
    FAUX_PLAFOND = "faux_plafond"
    AGENCEMENT = "agencement"
    ISOLATION = "isolation"
    PEINTURE = "peinture"


class TypeArticle(str, Enum):
    MATERIAU = "materiau"
    FOURNITURE = "fourniture"
    MAIN_OEUVRE = "main_oeuvre"
    CONSOMMABLE = "consommable"


class Organisation(BaseModel):
    """Informations sur l'organisation/entreprise avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int = 1
    nom: str = Field(min_length=1, description="Nom de l'organisation (obligatoire)")
    siret: str = Field(default="", max_length=50, description="Numéro SIRET")
    adresse: str = Field(default="", max_length=255)
    cp: str = Field(default="", max_length=20, description="Code postal")
    ville: str = Field(default="", max_length=100)
    telephone: str = Field(default="", max_length=30)
    email: Optional[EmailStr] = Field(default=None, description="Email valide")
    site_web: str = Field(default="", max_length=255)
    logo_path: str = Field(default="", max_length=255)
    date_debut_exercice: str = Field(default="")
    date_fin_exercice: str = Field(default="")
    
    @field_validator('siret')
    @classmethod
    def validate_siret(cls, v: str) -> str:
        """Valide le format SIRET (14 chiffres)"""
        if v and v.strip():
            v_clean = v.replace(' ', '')
            if not v_clean.isdigit():
                raise ValueError("Le SIRET ne doit contenir que des chiffres")
            if len(v_clean) != 14:
                raise ValueError("Le SIRET doit contenir exactement 14 chiffres")
        return v
    
    @field_validator('cp')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Valide le format code postal français (5 chiffres)"""
        if v and v.strip():
            v_clean = v.replace(' ', '')
            if not re.match(r'^\d{5}$', v_clean):
                raise ValueError("Le code postal doit contenir 5 chiffres")
        return v
    
    @field_validator('telephone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valide le format téléphone français"""
        if v and v.strip():
            v_clean = re.sub(r'[\s\.\-]', '', v)
            if not re.match(r'^0[1-9]\d{8}$', v_clean):
                raise ValueError("Le téléphone doit contenir 10 chiffres commençant par 0")
        return v


class Client(BaseModel):
    """Client avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int
    nom: str = Field(min_length=1, description="Nom (obligatoire)")
    prenom: str = Field(min_length=1, description="Prénom (obligatoire)")
    entreprise: str = Field(default="")
    adresse: str = Field(default="", max_length=255)
    cp: str = Field(default="", max_length=20)
    ville: str = Field(default="", max_length=100)
    telephone: str = Field(default="", max_length=30)
    email: str = Field(default="")
    
    @field_validator('cp')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Valide le format code postal français"""
        if v and v.strip():
            v_clean = v.replace(' ', '')
            if not re.match(r'^\d{5}$', v_clean):
                raise ValueError("Le code postal doit contenir 5 chiffres")
        return v
    
    @field_validator('telephone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valide le format téléphone français"""
        if v and v.strip():
            v_clean = re.sub(r'[\s\.\-]', '', v)
            if not re.match(r'^0[1-9]\d{8}$', v_clean):
                raise ValueError("Le téléphone doit contenir 10 chiffres commençant par 0")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Valide le format email"""
        if v and v.strip():
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError("Format d'email invalide")
        return v
    
    def get_full_name(self) -> str:
        """Retourne le nom complet du client"""
        return f"{self.prenom} {self.nom}"
    
    def get_display_name(self) -> str:
        """Retourne le nom d'affichage avec entreprise"""
        return f"{self.nom} {self.prenom} - {self.entreprise}"


class Fournisseur(BaseModel):
    """Fournisseur avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int
    nom: str = Field(min_length=1)
    specialite: str = Field(default="")
    telephone: str = Field(default="", max_length=30)
    email: str = Field(default="")
    remise: float = Field(default=0.0, ge=0, le=100, description="Remise en %")
    
    @field_validator('telephone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valide le format téléphone français"""
        if v and v.strip():
            v_clean = re.sub(r'[\s\.\-]', '', v)
            if not re.match(r'^0[1-9]\d{8}$', v_clean):
                raise ValueError("Le téléphone doit contenir 10 chiffres commençant par 0")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Valide le format email"""
        if v and v.strip():
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError("Format d'email invalide")
        return v


class Article(BaseModel):
    """Article avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int
    reference: str = Field(min_length=1, description="Référence unique (obligatoire)")
    designation: str = Field(min_length=1, description="Désignation (obligatoire)")
    unite: str = Field(description="m², ml, u, h, kg, l, forfait")
    prix_unitaire: float = Field(ge=0, description="Prix unitaire >= 0")
    type_article: str = Field(description="materiau, fourniture, main_oeuvre, consommable")
    fournisseur_id: int
    description: str = Field(default="")
    categorie: str = Field(default="general")
    
    def get_display_text(self) -> str:
        """Retourne le texte d'affichage de l'article"""
        return f"{self.reference} - {self.designation}"
    
    def calculate_total(self, quantite: float) -> float:
        """Calcule le prix total pour une quantité donnée"""
        return self.prix_unitaire * quantite


class ComposantOuvrage(BaseModel):
    """Composant d'un ouvrage avec validations"""
    article_id: int
    quantite: float = Field(gt=0, description="Quantité > 0")
    designation: str = Field(default="")
    unite: str = Field(default="")
    prix_unitaire: float = Field(ge=0)

    def prix_total(self) -> float:
        return self.quantite * self.prix_unitaire


class Ouvrage(BaseModel):
    """Ouvrage avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int
    reference: str = Field(min_length=1)
    designation: str = Field(min_length=1)
    description: str = Field(default="")
    categorie: str
    unite: str
    composants: List[ComposantOuvrage] = Field(default_factory=list)

    @property
    def prix_revient_unitaire(self) -> float:
        """Prix de revient pour une unité d'ouvrage"""
        return sum(comp.prix_total() for comp in self.composants)
    
    def calculate_prix_vente(self, coefficient: float = DEFAULT_COEFFICIENT_MARGE) -> float:
        """Calcule le prix de vente unitaire avec coefficient de marge"""
        return self.prix_revient_unitaire * coefficient
    
    def get_display_text(self) -> str:
        """Retourne le texte d'affichage de l'ouvrage"""
        return f"{self.reference} - {self.designation}"


class LigneDevis(BaseModel):
    """Ligne de devis avec validations"""
    type: str = Field(default="ouvrage", pattern="^(ouvrage|texte|chapitre)$")
    id: int = 0
    
    # Champs pour type "ouvrage"
    ouvrage_id: int = 0
    designation: str = Field(default="")
    description: str = Field(default="")
    quantite: float = Field(default=0.0, ge=0)
    unite: str = Field(default="")
    prix_unitaire: float = Field(default=0.0, ge=0)
    composants: List[ComposantOuvrage] = Field(default_factory=list)
    
    # Champs pour type "chapitre"
    titre: str = Field(default="")
    
    # Champs pour type "texte"
    texte: str = Field(default="")

    @property
    def prix_ht(self) -> float:
        if self.type == "ouvrage":
            return self.quantite * self.prix_unitaire
        return 0.0


class Devis(BaseModel):
    """Devis avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    numero: str = Field(min_length=1, description="Numéro de devis unique")
    date: str
    client_id: int = Field(gt=0, description="ID client obligatoire")
    objet: str = Field(default="")
    lignes: List[LigneDevis] = Field(default_factory=list)
    coefficient_marge: float = Field(
        default=DEFAULT_COEFFICIENT_MARGE,
        ge=MIN_COEFFICIENT_MARGE,
        le=MAX_COEFFICIENT_MARGE,
        description="Coefficient de marge"
    )
    remise: float = Field(default=0.0, ge=0, le=100, description="Remise en %")
    tva: float = Field(default=DEFAULT_TVA_RATE, ge=0, le=100, description="TVA en %")
    validite: int = Field(default=30, gt=0, description="Validité en jours")
    notes: str = Field(default="")
    conditions: str = Field(default="")
    statut: str = Field(
        default="en cours",
        pattern="^(en cours|envoyé|refusé|accepté)$"
    )

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


class DepenseReelle(BaseModel):
    """Dépense réelle avec validations"""
    id: int
    type_depense: str = Field(
        pattern="^(materiau|main_oeuvre|fourniture|consommable)$"
    )
    designation: str = Field(min_length=1)
    quantite: float = Field(gt=0)
    unite: str
    prix_unitaire: float = Field(ge=0)
    date: str
    article_id: int = Field(default=0)
    notes: str = Field(default="")
    
    @property
    def prix_total(self) -> float:
        """Calcule le prix total de la dépense"""
        return self.quantite * self.prix_unitaire


class Projet(BaseModel):
    """Projet/chantier avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: int
    numero: str = Field(min_length=1, description="Numéro unique du projet")
    devis_numeros: List[str] = Field(default_factory=list, min_length=1)
    client_id: int = Field(gt=0)
    date_creation: str
    date_debut: str = Field(default="")
    date_fin_prevue: str = Field(default="")
    date_fin_reelle: str = Field(default="")
    statut: str = Field(
        default="en attente",
        pattern="^(en attente|en cours|terminé|annulé)$"
    )
    adresse_chantier: str = Field(default="")
    notes: str = Field(default="")
    depenses_reelles: List[DepenseReelle] = Field(default_factory=list)


class User(BaseModel):
    """Utilisateur avec validations"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str = Field(description="UUID de l'utilisateur")
    username: str = Field(min_length=3, max_length=50, description="Nom d'utilisateur unique")
    email: Optional[EmailStr] = Field(default=None)
    password_hash: str = Field(min_length=1, description="Hash du mot de passe")
    salt: str = Field(min_length=1, description="Salt pour le hash")
    role: str = Field(default="user", pattern="^(admin|user)$")
    created_at: str
    last_login: str = Field(default="")
    is_active: bool = Field(default=True)
    nom: str = Field(default="")
    prenom: str = Field(default="")
    
    def update_last_login(self) -> None:
        """Met à jour la date de dernière connexion"""
        self.last_login = datetime.now().isoformat()


class Categorie(BaseModel):
    """Catégorie avec sous-catégories"""
    id: str
    label: str = Field(min_length=1)
    icon: str = Field(default="")
    children: List['Categorie'] = Field(default_factory=list)
