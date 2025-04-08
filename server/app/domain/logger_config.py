"""
This module configures the logging for the logic of the 
queues and topics module.
"""

import logging
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(current_dir, 'logs')

os.makedirs(logs_dir, exist_ok=True)

log_path = os.path.join(logs_dir, 'Domain.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_path,
    filemode='a'
)

logger = logging.getLogger('Domain')
