import logging
from client.mom_client import MOMClient

def main():
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    client = MOMClient()

    # 1. Obtener el mensaje del endpoint home
    home_message = client.get_home_message()
    if home_message:
        print("Home message:", home_message)
    else:
        print("Error: Could not retrieve home message.")

    # 2. Autenticación (login)
    auth_response = client.login()  # Usa las credenciales por defecto del config
    if auth_response:
        print("Login successful!")
    else:
        print("Login failed!")
        return  # Detener si falla el login

    # 3. Suscribirse a un canal ("queue-example" de tipo "queue")
    subscribe_response = client.subscribe("queue-example", "queue")
    if subscribe_response and subscribe_response.get("success"):
        print("Subscribe successful:", subscribe_response.get("message"))
    else:
        print("Subscribe failed:", subscribe_response)

    # 4. Desuscribirse del canal
    unsubscribe_response = client.unsubscribe("queue-example", "queue")
    if unsubscribe_response and unsubscribe_response.get("success"):
        print("Unsubscribe successful:", unsubscribe_response.get("message"))
    else:
        print("Unsubscribe failed:", unsubscribe_response)

    # 5. Enviar un mensaje al canal
    send_response = client.send_message("queue-example", "Hello, world!", "queue")
    if send_response and send_response.get("success"):
        print("Message sent:", send_response.get("message"))
    else:
        print("Send message failed:", send_response)

    # 6. Recibir un mensaje del canal
    receive_response = client.receive_message("queue-example", "queue")
    if receive_response and receive_response.get("success"):
        msg = receive_response.get("message")
        if msg is not None:
            print("Received message:", msg)
        else:
            print("Queue is empty.")
    else:
        print("Receive message failed:", receive_response)

    # 7. Acceder al endpoint protegido
    protected_response = client.get_protected_resource()
    if protected_response:
        print("Protected resource:", protected_response)
    else:
        print("Failed to get protected resource.")

if __name__ == "__main__":
    main()
