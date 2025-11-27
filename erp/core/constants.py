"""
Business constants for ERP BTP application

This module centralizes all magic numbers, formats, and business rules
to ensure consistency across the application.
"""

# =============================================================================
# Devis (Quotation) Constants
# =============================================================================

# Default values
DEFAULT_TVA_RATE = 20.0
DEFAULT_COEFFICIENT_MARGE = 1.35

# Formats
DATE_FORMAT = '%Y-%m-%d'
DEVIS_NUMBER_FORMAT = 'DEV-{year}-{number:04d}'
CURRENCY = 'EUR'
CURRENCY_SYMBOL = '€'

# Limits
MAX_LIGNE_DEVIS = 100
MIN_COEFFICIENT_MARGE = 1.0
MAX_COEFFICIENT_MARGE = 5.0
MIN_TVA_RATE = 0.0
MAX_TVA_RATE = 100.0

# Statuses
DEVIS_STATUSES = ['en cours', 'envoyé', 'refusé', 'accepté']

# Status colors (for UI display)
DEVIS_STATUS_COLORS = {
    'en cours': '#667eea',
    'envoyé': '#f093fb',
    'refusé': '#f5576c',
    'accepté': '#43e97b'
}


# =============================================================================
# UI Constants
# =============================================================================

# Notification durations (seconds)
NOTIFICATION_DURATION = 3
NOTIFICATION_DURATION_ERROR = 5

# Debounce timers (seconds)
DEBOUNCE_SEARCH = 0.3
DEBOUNCE_INPUT = 0.5


# =============================================================================
# PDF Generation Constants
# =============================================================================

# Page settings
PDF_PAGE_SIZE = 'A4'
PDF_MARGIN = 50
PDF_TITLE_SIZE = 18
PDF_HEADER_SIZE = 14
PDF_BODY_SIZE = 10
PDF_SMALL_SIZE = 8

# Colors (RGB)
PDF_COLOR_HEADER = (200, 76, 60)  # Accent color
PDF_COLOR_TEXT = (44, 62, 80)
PDF_COLOR_LIGHT_GRAY = (220, 220, 220)


# =============================================================================
# Data Validation Constants
# =============================================================================

# Email regex pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Phone number patterns
PHONE_PATTERN = r'^(\+33|0)[1-9](\d{2}){4}$'

# SIRET pattern (French business ID)
SIRET_PATTERN = r'^\d{14}$'

# Minimum lengths
MIN_CLIENT_NAME_LENGTH = 2
MIN_ARTICLE_REFERENCE_LENGTH = 1
MIN_OUVRAGE_REFERENCE_LENGTH = 1


# =============================================================================
# File System Constants
# =============================================================================

# Data files
DATA_FILES = {
    'articles': 'articles.json',
    'clients': 'clients.json',
    'devis': 'devis.json',
    'fournisseurs': 'fournisseurs.json',
    'organisation': 'organisation.json',
    'ouvrages': 'ouvrages.json',
}

# Default data directory name
DATA_DIR_NAME = 'data'
LOGS_DIR_NAME = 'logs'


# =============================================================================
# Application Info
# =============================================================================

APP_NAME = "ERP BTP"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"
