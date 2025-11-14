import logging

# Configure logging settings
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nlp_querier.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_info(message: str) -> None:
    """Log an informational message."""
    logger.info(message)

def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)

def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)

def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)