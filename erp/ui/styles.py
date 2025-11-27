"""
Styles UI centralisés et homogénéisés
"""

# ============================================================================
# CSS CONSOLIDÉ
# ============================================================================

CONSOLIDATED_STYLES = '''
/* Base inputs - all input fields */
.numero-input input, .date-input input, .w-24 input, .chapitre-input input,
.texte-input textarea, .tva-input input, .comp-qte input, .comp-pu input,
.recap-card input, .notes-textarea textarea, .conditions-textarea textarea,
.ouvrage-input input, .ouvrage-input textarea, .comp-designation input,
.comp-unite input, .ouvrage-reference input, .ouvrage-designation input,
.ouvrage-description textarea, .ouvrage-categorie, .ouvrage-unite,
.article-reference input, .article-designation input, .article-description textarea,
.article-unite, .article-price input, .dialog-input input, .dialog-textarea textarea {
    border: 1px solid #e5e7eb !important; 
    outline: none !important; 
    box-shadow: none !important;
    padding: 8px 12px !important;
    box-sizing: border-box !important;
    border-radius: 4px !important;
}

/* Numero input - completely borderless */
.numero-input input {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

.numero-input input:focus {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Focus states */
.tva-input input:focus, .date-input input:focus {
    border: 1px solid var(--todoist-accent, #c84c3c) !important;
    outline: none !important;
    box-shadow: none !important;
    padding: 8px 12px !important;
}

/* Right-aligned numeric inputs - descend to bottom */
.date-input input, 
.comp-qte input, .comp-pu input, .article-price input, 
.tva-input input {
    text-align: right !important;
    padding-top: 16px !important;
    padding-bottom: 0px !important;
}

/* Numero input - no special padding, just display value */
.numero-input input {
    padding-top: 16px !important;
    padding-bottom: 0px !important;
}

/* Centered inputs */
.comp-unite input {
    text-align: center !important;
    padding-top: 16px !important;
    padding-bottom: 0px !important;
}

/* Ouvrage section inputs */
.ouvrage-reference input, .ouvrage-designation input {
    padding-top: 16px !important;
    padding-bottom: 0px !important;
}

/* Remove Quasar field wrapper styling */
.tva-input .q-field__inner {
    padding: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

.tva-input {
    width: 100% !important;
    min-width: 80px !important;
}

/* Material Design Icons */
@font-face {
    font-family: 'Material Icons';
    font-style: normal;
    font-weight: 400;
    src: url(https://fonts.gstatic.com/s/materialicons/v142/flUhRq6tzZsQSLGM8HNQXv-d-_FrxI5I.woff2) format('woff2');
}

.material-icons {
    font-family: 'Material Icons';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    display: inline-block;
    line-height: 1;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;
}

/* Hide tab arrows */
.q-tabs__arrow, .q-tabs > button, .q-tabs [role="button"] {
    display: none !important;
}

/* Reduce row spacing */
.q-row {
    min-height: auto !important;
    margin: 0 !important;
}

/* Compact table spacing */
.w-full.gap-2.p-1 {
    margin-bottom: -1px !important;
}
'''


def get_consolidated_styles() -> str:
    """Retourne tout le CSS consolidé"""
    return CONSOLIDATED_STYLES


# ============================================================================
# CLASSES TAILWIND RÉUTILISABLES
# ============================================================================

# Standard rows
ROW_STANDARD = 'w-full gap-4'
ROW_COMPACT = 'w-full gap-2 p-1 border-b border-gray-100'
ROW_DENSE = 'w-full gap-2 px-2 py-0.5 items-center hover:bg-gray-50 text-sm border-b border-gray-200'

# Standard cards
CARD_STANDARD = 'w-full mt-6 shadow-sm'
CARD_FORM = 'flex-1 shadow-none border'
CARD_COMPACT = 'w-full shadow-none border'

# Standard columns
COLUMN_STANDARD = 'w-full gap-4'
COLUMN_DENSE = 'w-full gap-2'

# Standard widths
WIDTH_FULL = 'w-full'
WIDTH_FLEX = 'flex-1'
WIDTH_SMALL = 'w-32'
WIDTH_MEDIUM = 'w-48'
WIDTH_LARGE = 'w-96'

# Standard text classes
TEXT_HEADER_SM = 'font-semibold text-lg text-gray-800'
TEXT_HEADER_MD = 'text-xl font-bold text-gray-900'
TEXT_HEADER_LG = 'text-3xl font-bold text-gray-900'
TEXT_LABEL = 'text-base font-medium text-gray-700'
TEXT_SECONDARY = 'text-sm text-gray-600'

# Standard button states
BUTTON_PRIMARY = 'color=positive'
BUTTON_SECONDARY = 'flat'
BUTTON_DANGER = 'color=negative flat'
