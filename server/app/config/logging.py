"""
Logging configuration for the API.
"""
from app.config.env import API_NAME
import logging

# Log file name
log_filename = f"api_{API_NAME}.log"

# Configurate the logging level to catch all messages from DEBUG onwards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)