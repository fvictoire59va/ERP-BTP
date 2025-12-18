"""
Module de validation des données
"""
import re


class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation"""
    pass


def validate_siret(siret: str) -> tuple[bool, str]:
    """Valide un numéro SIRET
    
    Args:
        siret: Le numéro SIRET à valider
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not siret:
        return True, ""  # SIRET optionnel
    
    # Enlever les espaces
    siret_clean = siret.replace(' ', '')
    
    # Vérifier la longueur
    if len(siret_clean) != 14:
        return False, "Le SIRET doit contenir 14 chiffres"
    
    # Vérifier que ce sont des chiffres
    if not siret_clean.isdigit():
        return False, "Le SIRET ne doit contenir que des chiffres"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Valide une adresse email
    
    Args:
        email: L'adresse email à valider
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not email:
        return True, ""  # Email optionnel
    
    # Pattern de base pour l'email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Format d'email invalide"
    
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    """Valide un numéro de téléphone français
    
    Args:
        phone: Le numéro de téléphone à valider
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not phone:
        return True, ""  # Téléphone optionnel
    
    # Enlever les espaces, points, tirets
    phone_clean = re.sub(r'[\s\.\-]', '', phone)
    
    # Vérifier le format français (10 chiffres commençant par 0)
    if not re.match(r'^0[1-9]\d{8}$', phone_clean):
        return False, "Le téléphone doit contenir 10 chiffres commençant par 0 (ex: 0612345678)"
    
    return True, ""


def validate_postal_code(cp: str) -> tuple[bool, str]:
    """Valide un code postal français
    
    Args:
        cp: Le code postal à valider
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not cp:
        return True, ""  # Code postal optionnel
    
    # Enlever les espaces
    cp_clean = cp.replace(' ', '')
    
    # Vérifier que c'est 5 chiffres
    if not re.match(r'^\d{5}$', cp_clean):
        return False, "Le code postal doit contenir 5 chiffres"
    
    return True, ""


def validate_required(value: str, field_name: str) -> tuple[bool, str]:
    """Valide qu'un champ obligatoire n'est pas vide
    
    Args:
        value: La valeur à valider
        field_name: Le nom du champ pour le message d'erreur
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not value or not value.strip():
        return False, f"Le champ '{field_name}' est obligatoire"
    
    return True, ""


def validate_url(url: str) -> tuple[bool, str]:
    """Valide une URL
    
    Args:
        url: L'URL à valider
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if not url:
        return True, ""  # URL optionnelle
    
    # Pattern de base pour URL
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    
    if not re.match(pattern, url, re.IGNORECASE):
        # Si pas de protocole, c'est acceptable
        if '.' in url and ' ' not in url:
            return True, ""
        return False, "Format d'URL invalide (ex: https://example.com)"
    
    return True, ""


def validate_positive_number(value, field_name: str) -> tuple[bool, str]:
    """Valide qu'un nombre est positif
    
    Args:
        value: La valeur à valider
        field_name: Le nom du champ pour le message d'erreur
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    if value is None or value == '':
        return True, ""  # Optionnel
    
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} ne peut pas être négatif"
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} doit être un nombre valide"


def validate_organisation(data: dict) -> tuple[bool, str]:
    """Valide les données d'une organisation
    
    Args:
        data: Dictionnaire contenant les données de l'organisation
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    # Nom obligatoire
    is_valid, error = validate_required(data.get('nom', ''), 'Nom')
    if not is_valid:
        return False, error
    
    # SIRET
    is_valid, error = validate_siret(data.get('siret', ''))
    if not is_valid:
        return False, error
    
    # Email
    is_valid, error = validate_email(data.get('email', ''))
    if not is_valid:
        return False, error
    
    # Téléphone
    is_valid, error = validate_phone(data.get('téléphone', ''))
    if not is_valid:
        return False, error
    
    # Code postal
    is_valid, error = validate_postal_code(data.get('code_postal', ''))
    if not is_valid:
        return False, error
    
    # Site web
    is_valid, error = validate_url(data.get('site_web', ''))
    if not is_valid:
        return False, error
    
    return True, ""


def validate_client(data: dict) -> tuple[bool, str]:
    """Valide les données d'un client
    
    Args:
        data: Dictionnaire contenant les données du client
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    # Nom obligatoire
    is_valid, error = validate_required(data.get('nom', ''), 'Nom')
    if not is_valid:
        return False, error
    
    # Prénom obligatoire
    is_valid, error = validate_required(data.get('prenom', ''), 'Prénom')
    if not is_valid:
        return False, error
    
    # Email
    is_valid, error = validate_email(data.get('email', ''))
    if not is_valid:
        return False, error
    
    # Téléphone
    is_valid, error = validate_phone(data.get('telephone', ''))
    if not is_valid:
        return False, error
    
    # Code postal
    is_valid, error = validate_postal_code(data.get('cp', ''))
    if not is_valid:
        return False, error
    
    return True, ""


def validate_article(data: dict) -> tuple[bool, str]:
    """Valide les données d'un article
    
    Args:
        data: Dictionnaire contenant les données de l'article
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    # Référence obligatoire
    is_valid, error = validate_required(data.get('reference', ''), 'Référence')
    if not is_valid:
        return False, error
    
    # Désignation obligatoire
    is_valid, error = validate_required(data.get('designation', ''), 'Désignation')
    if not is_valid:
        return False, error
    
    # Prix unitaire positif
    is_valid, error = validate_positive_number(data.get('prix_unitaire'), 'Prix unitaire')
    if not is_valid:
        return False, error
    
    return True, ""


def validate_projet(data: dict) -> tuple[bool, str]:
    """Valide les données d'un projet/chantier
    
    Args:
        data: Dictionnaire contenant les données du projet
        
    Returns:
        tuple (est_valide, message_erreur)
    """
    # Numéro obligatoire
    is_valid, error = validate_required(data.get('numero', ''), 'Numéro')
    if not is_valid:
        return False, error
    
    # Client obligatoire
    if not data.get('client_id'):
        return False, "Le client est obligatoire"
    
    return True, ""
