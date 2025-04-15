import yaml
import logging
import requests

logger = logging.getLogger(__name__)

def read_config(path="src/config.yaml"):
    """
    Lee el archivo de configuración YAML y retorna un diccionario.
    """
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error("Error reading config file %s: %s", path, e)
        return {}

def do_request(method, url, headers=None, json=None, timeout=10):
    """
    Realiza una petición HTTP usando requests y maneja errores básicos.
    Retorna la respuesta parseada (JSON o texto) o None en caso de error.
    """
    try:
        response = requests.request(method, url, headers=headers, json=json, timeout=timeout)
        response.raise_for_status()  # Lanza excepción si ocurre error HTTP
        try:
            return response.json()
        except ValueError:
            return response.text
    except requests.exceptions.RequestException as e:
        logger.error("Request error for %s %s: %s", method, url, e)
        return None
