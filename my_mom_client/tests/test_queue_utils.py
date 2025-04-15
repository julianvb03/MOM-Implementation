import logging
from tests.queue_utils import create_test_queue, delete_test_queue

def main():
    # Configurar logging en DEBUG para ver todo el detalle
    logging.basicConfig(level=logging.DEBUG)

    # Setea aquí tu token (y token_type) manualmente
    token_type = "Bearer"
    access_token = "YOUR_ADMIN_TOKEN_HERE"  # Reemplaza con un token válido
    
    queue_name = "test-queue"

    print(">>> Creating test queue...")
    create_resp = create_test_queue(token_type, access_token, queue_name=queue_name)
    if create_resp is None or (isinstance(create_resp, dict) and create_resp.get("success") is not True):
        print("FAILED to create test queue. Check logs above for details.")
    else:
        print("Test queue created successfully:", create_resp)

    print(">>> Deleting test queue...")
    delete_resp = delete_test_queue(token_type, access_token, queue_name=queue_name)
    if delete_resp is None or (isinstance(delete_resp, dict) and delete_resp.get("success") is not True):
        print("FAILED to delete test queue. Check logs above for details.")
    else:
        print("Test queue deleted successfully:", delete_resp)

if __name__ == "__main__":
    main()
