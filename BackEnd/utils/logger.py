import logging
import sys

def setup_logger(name=__name__):
    """Configure un logger simple pour la console seulement"""
    
    logger = logging.getLogger(name)
    
    # Éviter les logs multiples
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Format du log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour la console seulement
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

# Logger global
logger = setup_logger('recipe-search')