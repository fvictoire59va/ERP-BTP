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
class Fournisseur:
    id: int
    nom: str
    specialite: str
    telephone: str
    email: str
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
    categorie: str  # platrerie, menuiserie_int, etc.
    unite: str  # m², ml, u, forfait
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
