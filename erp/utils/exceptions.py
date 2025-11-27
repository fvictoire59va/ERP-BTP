"""
Custom exceptions for ERP BTP application

Provides a hierarchy of exceptions for better error handling and debugging.
"""


class ERPBTPException(Exception):
    """
    Base exception for all ERP BTP application errors.
    
    All custom exceptions should inherit from this class to allow
    catching all application-specific errors in one except block.
    
    Example:
        >>> try:
        >>>     # Some operation
        >>>     pass
        >>> except ERPBTPException as e:
        >>>     logger.error(f"Application error: {e}")
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class DataValidationError(ERPBTPException):
    """
    Raised when data validation fails.
    
    Used when user input or data from files doesn't meet business rules.
    
    Example:
        >>> if not client.email:
        >>>     raise DataValidationError(
        >>>         "Email requis",
        >>>         {"field": "email", "value": None}
        >>>     )
    """
    pass


class PDFGenerationError(ERPBTPException):
    """
    Raised when PDF generation fails.
    
    Used when creating PDF documents encounters errors.
    
    Example:
        >>> try:
        >>>     generate_pdf(devis, path)
        >>> except Exception as e:
        >>>     raise PDFGenerationError(
        >>>         f"Impossible de générer le PDF: {e}",
        >>>         {"devis_numero": devis.numero, "path": str(path)}
        >>>     )
    """
    pass


class DataPersistenceError(ERPBTPException):
    """
    Raised when saving or loading data fails.
    
    Used for errors related to reading/writing JSON files.
    
    Example:
        >>> try:
        >>>     with open(file_path) as f:
        >>>         data = json.load(f)
        >>> except Exception as e:
        >>>     raise DataPersistenceError(
        >>>         f"Impossible de charger {file_path}",
        >>>         {"file": str(file_path), "error": str(e)}
        >>>     )
    """
    pass


class BusinessRuleViolation(ERPBTPException):
    """
    Raised when a business rule is violated.
    
    Used for domain-specific constraints.
    
    Example:
        >>> if coefficient < MIN_COEFFICIENT_MARGE:
        >>>     raise BusinessRuleViolation(
        >>>         "Coefficient de marge trop faible",
        >>>         {"min": MIN_COEFFICIENT_MARGE, "actual": coefficient}
        >>>     )
    """
    pass


class ResourceNotFoundError(ERPBTPException):
    """
    Raised when a requested resource doesn't exist.
    
    Used when trying to access clients, devis, articles, etc. that don't exist.
    
    Example:
        >>> client = get_client_by_id(client_id)
        >>> if not client:
        >>>     raise ResourceNotFoundError(
        >>>         f"Client {client_id} introuvable",
        >>>         {"resource_type": "client", "id": client_id}
        >>>     )
    """
    pass


class DuplicateResourceError(ERPBTPException):
    """
    Raised when attempting to create a duplicate resource.
    
    Used when unique constraints are violated (e.g., duplicate devis numero).
    
    Example:
        >>> if any(d.numero == numero for d in devis_list):
        >>>     raise DuplicateResourceError(
        >>>         f"Le numéro de devis {numero} existe déjà",
        >>>         {"numero": numero}
        >>>     )
    """
    pass
