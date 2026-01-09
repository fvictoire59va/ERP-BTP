"""
Logging configuration for ERP BTP application

Provides centralized logging with both console and file handlers.
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from erp.core.constants import APP_NAME, LOGS_DIR_NAME


class NiceGUIWarningFilter(logging.Filter):
    """Filtre pour supprimer les warnings NiceGUI non pertinents"""
    
    def filter(self, record):
        # Filtrer les messages contenant .js.map ou .well-known
        if '.js.map not found' in record.getMessage():
            return False
        if '.well-known/' in record.getMessage():
            return False
        return True


# Global logger cache
_loggers = {}


def setup_logger(
    name: str = APP_NAME,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger for the application.
    
    Args:
        name: Logger name (usually module name or app name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Format for log messages
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(NiceGUIWarningFilter())
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent.parent / LOGS_DIR_NAME
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with date
        log_file = log_dir / f'erp_btp_{datetime.now().strftime("%Y%m%d")}.log'
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Cache the logger
    _loggers[name] = logger
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name. If None, returns the main app logger.
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
    """
    if name is None:
        name = APP_NAME
    
    if name not in _loggers:
        # Récupérer le niveau de log depuis l'environnement
        _log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        try:
            _log_level = getattr(logging, _log_level_str)
        except AttributeError:
            _log_level = logging.INFO
        return setup_logger(name, level=_log_level)
    
    return _loggers[name]


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with arguments.
    
    Example:
        >>> logger = get_logger(__name__)
        >>> @log_function_call(logger)
        >>> def my_function(arg1, arg2):
        >>>     return arg1 + arg2
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# Create main application logger on module import
# Lire le niveau de log depuis la variable d'environnement LOG_LEVEL
_log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
try:
    _log_level = getattr(logging, _log_level_str)
except AttributeError:
    _log_level = logging.INFO

app_logger = setup_logger(APP_NAME, level=_log_level)
