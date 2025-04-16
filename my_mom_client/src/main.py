import os
import sys
import time
import logging
import threading
from src.client.mom_client import MOMClient

# Códigos ANSI para colores (terminales compatibles)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Diccionario global para almacenar las subscriptions activas.
# La clave es el canal y el valor es el tipo (por ejemplo, "queue" o "topic").
subscribed_channels = {}

def setup_logging_to_file():
    """
    Configura el logging general para que se registren todos los mensajes
    en un archivo 'logs/app.log' (sin imprimir en consola a través de logging).
    """
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file = os.path.join(logs_dir, "app.log")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Eliminar todos los handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def setup_user_file_logger(username):
    """
    Agrega un FileHandler para registrar mensajes en 'logs/<username>.log' en modo append.
    """
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file = os.path.join(logs_dir, f"{username}.log")
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)

def listen_subscriptions(client):
    """
    Hilo que escucha continuamente los mensajes de todos los canales a los que el cliente
    está suscrito. Por cada canal en 'subscribed_channels', llama a client.receive_message(channel, type)
    de forma periódica y muestra en la terminal únicamente el mensaje recibido (en color azul).
    """
    while True:
        # Copia de los canales suscritos (para evitar problemas de concurrencia)
        channels = list(subscribed_channels.items())
        for channel, ch_type in channels:
            resp = client.receive_message(channel, ch_type)
            # Si se recibe una respuesta y contiene 'message', se muestra.
            if isinstance(resp, dict) and resp.get("success") is True:
                message = resp.get("message")
                if message:
                    print(f"{BLUE}[{channel}] {message}{RESET}")
            # En caso de error o no recibir nada, simplemente continúa.
        time.sleep(2)  # Esperar 2 segundos antes de la siguiente comprobación

def process_action(action_line, client):
    """
    Procesa una línea de acción del archivo de acciones de usuario.
    
    Formato esperado:
      - subscribe;channel;type
      - unsubscribe;channel;type
      - send;channel;message;type
      - close
    Nota: No se procesa 'receive' desde el archivo, ya que se gestiona continuamente en un hilo.
    """
    parts = action_line.strip().split(";")
    if not parts:
        return None

    command = parts[0].lower()
    resp = None

    if command == "subscribe" and len(parts) == 3:
        resp = client.subscribe(parts[1], parts[2])
        if isinstance(resp, dict) and resp.get("success") is True:
            # Agregar canal a las suscripciones activas
            subscribed_channels[parts[1]] = parts[2]
    elif command == "unsubscribe" and len(parts) == 3:
        resp = client.unsubscribe(parts[1], parts[2])
        if isinstance(resp, dict) and resp.get("success") is True:
            # Eliminar canal de las suscripciones activas, si existe
            if parts[1] in subscribed_channels:
                del subscribed_channels[parts[1]]
    elif command == "send" and len(parts) == 4:
        resp = client.send_message(parts[1], parts[2], parts[3])
    elif command == "close":
        print(f"{YELLOW}close{RESET}")
        logging.info("Action 'close' received. Shutting down client.")
        return "close"
    else:
        msg = f"Unknown or malformed command: {action_line.strip()}"
        print(f"{RED}{msg}{RESET}")
        logging.warning(msg)
        return None

    logging.info("Action '%s' executed. Full response: %s", command, resp)
    
    # En la terminal se muestra solo el "message" de la respuesta, si existe.
    if isinstance(resp, dict) and "message" in resp:
        print(f"{BLUE}{resp['message']}{RESET}")
    elif resp is not None:
        print(f"{BLUE}{resp}{RESET}")
    else:
        print(f"{RED}No response received.{RESET}")

    return None

def process_actions_file(file_path, client):
    """
    Lee continuamente el archivo de acciones del usuario, procesa la primera línea,
    la elimina y repite el proceso hasta encontrar la acción 'close'.
    """
    while True:
        if not os.path.exists(file_path):
            time.sleep(1)
            continue

        with open(file_path, "r") as f:
            lines = f.readlines()
        
        if not lines:
            time.sleep(1)
            continue

        action_line = lines[0]
        result = process_action(action_line, client)
        
        with open(file_path, "w") as f:
            f.writelines(lines[1:])
        
        if result == "close":
            break

        time.sleep(1)

def main():
    setup_logging_to_file()
    
    client = MOMClient()
    
    # Verificar conexión con la API
    print("Verificando conexión con la API...")
    home_msg = client.get_home_message()
    if not home_msg:
        print(f"{RED}Error de conexión: No se pudo acceder a la API.{RESET}")
        logging.error("Conexión fallida: Endpoint home no accesible.")
        sys.exit(1)
    print(f"{GREEN}Conexión exitosa con la API. Mensaje de bienvenida:{RESET}")
    print(f"{GREEN}{home_msg}{RESET}")
    
    # Solicitar credenciales
    usuario = input("Ingrese su usuario: ")
    contraseña = input("Ingrese su contraseña: ")
    
    setup_user_file_logger(usuario)
    
    print("Intentando autenticar, por favor espere...")
    login_resp = client.login(usuario, contraseña)
    if not login_resp:
        print(f"{RED}Error en el login, verifique sus credenciales.{RESET}")
        logging.error("Login fallido para el usuario: %s", usuario)
        sys.exit(1)
    print(f"{GREEN}Login exitoso!{RESET}")
    logging.info("Login exitoso para el usuario: %s", usuario)
    
    # Inicia hilo para escuchar continuamente todas las suscripciones activas.
    listener_thread = threading.Thread(target=listen_subscriptions, args=(client,), daemon=True)
    listener_thread.start()
    
    # Determinar el archivo de acciones para el usuario (dentro de la carpeta 'actions')
    actions_dir = "actions"
    if not os.path.exists(actions_dir):
        os.makedirs(actions_dir)
    
    actions_file = os.path.join(actions_dir, f"{usuario}.txt")
    if not os.path.exists(actions_file):
        logging.info("No se encontró el archivo de acciones '%s'; creándolo vacío.", actions_file)
        with open(actions_file, "w") as f:
            pass
        print(f"{YELLOW}Archivo de acciones creado: {actions_file}{RESET}")
    
    print(f"\nIniciando procesamiento de acciones desde '{actions_file}'...")
    logging.info("Procesando acciones desde '%s'", actions_file)
    process_actions_file(actions_file, client)
    
    print(f"{GREEN}Cliente finalizado.{RESET}")
    logging.info("Cliente finalizado.")

if __name__ == "__main__":
    main()
