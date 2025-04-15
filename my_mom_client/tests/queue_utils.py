import logging
from src.client.utils import read_config, do_request

logger = logging.getLogger(__name__)

def create_test_queue(token_type, access_token, queue_name="test-queue"):
    """
    Crea una queue de prueba usando el endpoint de administración.
    
    Método: PUT
    URL: /admin/queue_topic/create/
    
    Request Body (JSON):
        {
            "name": "<queue_name>",
            "type": "queue"
        }
    
    Headers:
        {
            "Authorization": "Bearer <token>"
        }
    
    Retorna:
        La respuesta del servidor (por ejemplo: {"success": true, "message": "Queue created successfully."})
        o None en caso de error.
    """
    config = read_config()
    base_url = config.get("api_base_url", "http://localhost:8080/api/v1.0.0/MomServer")
    url = f"{base_url}/admin/queue_topic/create/"
    
    headers = {
        "Authorization": f"{token_type} {access_token}"
    }
    payload = {
        "name": queue_name,
        "type": "queue"
    }

    logger.debug("Creating test queue '%s' at URL: %s", queue_name, url)
    response = do_request("PUT", url, headers=headers, json=payload, timeout=config.get("timeout", 10))
    if response:
        logger.debug("Test queue '%s' created successfully: %s", queue_name, response)
    else:
        logger.error("Failed to create test queue '%s'.", queue_name)
    return response

def delete_test_queue(token_type, access_token, queue_name="test-queue"):
    """
    Elimina la queue de prueba usando el endpoint de administración.
    
    Método: DELETE
    URL: /admin/queue_topic/delete/{queue_name}?type=queue
    
    Headers:
        {
            "Authorization": "Bearer <token>"
        }
    
    Retorna:
        La respuesta del servidor (por ejemplo: {"success": true, "message": "Queue deleted successfully."})
        o None en caso de error.
    """
    config = read_config()
    base_url = config.get("api_base_url", "http://localhost:8080/api/v1.0.0/MomServer")
    url = f"{base_url}/admin/queue_topic/delete/{queue_name}?type=queue"
    
    headers = {
        "Authorization": f"{token_type} {access_token}"
    }

    logger.debug("Deleting test queue '%s' at URL: %s", queue_name, url)
    response = do_request("DELETE", url, headers=headers, timeout=config.get("timeout", 10))
    if response:
        logger.debug("Test queue '%s' deleted successfully: %s", queue_name, response)
    else:
        logger.error("Failed to delete test queue '%s'.", queue_name)
    return response
