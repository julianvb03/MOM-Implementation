import os
import sys
import time
import logging
import threading
import yaml
from src.client.mom_client import MOMClient

# ANSI color codes for terminal output
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

CONFIG_FILE = "src/config.yaml"
ACTIONS_FILE = "actions.txt"
DEFAULT_DELAY = 1  # 1 second delay between actions

def setup_logging_to_file():
    """
    Configures logging to record all messages only in the global file 'logs/app.log'.
    """
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    log_file = os.path.join(logs_dir, "app.log")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def setup_user_file_logger(username):
    """
    Adds a FileHandler so that logs are also saved in 'logs/<username>.log' in append mode.
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

def load_config():
    """
    Loads the YAML configuration from CONFIG_FILE.
    """
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{RED}Failed to load configuration file: {e}{RESET}")
        sys.exit(1)

def update_config(config):
    """
    Writes the updated configuration back to CONFIG_FILE.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        print(f"{RED}Failed to update configuration file: {e}{RESET}")

def get_next_credential():
    """
    Retrieves the next available credential from the configuration file.
    Once a credential is used, it is removed from the list and the configuration is updated.
    Exits if no credentials remain.
    Returns a tuple (username, password).
    """
    config = load_config()
    creds = config.get("credentials", [])
    if not creds:
        print(f"{RED}No more credentials available in {CONFIG_FILE}.{RESET}")
        sys.exit(1)
    cred = creds.pop(0)
    config["credentials"] = creds
    update_config(config)
    return cred["username"], cred["password"]

def listen_subscriptions(client):
    """
    Continuously listens for messages on all channels the client is subscribed to.
    Every second, for each channel in client.subscribed_channels, it calls client.receive_message(channel, type)
    and prints the message (in blue) if one is received and non-empty.
    """
    while True:
        for channel, ch_type in client.subscribed_channels.items():
            resp = client.receive_message(channel, ch_type)
            if isinstance(resp, dict) and resp.get("success") is True and "message" in resp:
                message = resp["message"]
                if message != None:
                    print(f"{BLUE}[{channel}] {message.strip()}{RESET}")
        time.sleep(1)

def process_action(action_line, client):
    """
    Processes a single action line from the user's actions file.
    Expected formats (without a username prefix, for per-user files):
      - subscribe;channel;type
      - unsubscribe;channel;type
      - send;channel;message;type
      - close
    Logs the full response and prints only the 'message' field in blue.
    Automatically re-logins if the token has expired.
    """
    parts = action_line.strip().split(";")
    if not parts:
        return None

    command = parts[0].lower()
    resp = None

    if command == "subscribe" and len(parts) == 3:
        resp = client.subscribe(parts[1], parts[2])
        if isinstance(resp, dict) and resp.get("success") or isinstance(resp, dict) is True:
            client.subscribed_channels[parts[1]] = parts[2]
    elif command == "unsubscribe" and len(parts) == 3:
        resp = client.unsubscribe(parts[1], parts[2])
        if isinstance(resp, dict) and resp.get("success") is True:
            client.subscribed_channels.pop(parts[1], None)
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

    # Auto re-login if token expired
    if isinstance(resp, dict) and "message" in resp and "token expired" in resp["message"].lower():
        logging.info("Token expired detected for user %s. Attempting auto re-login.", client.username)
        new_login = client.login(client.username, client.password)
        if new_login:
            logging.info("Auto re-login successful for user %s.", client.username)
            resp = process_action(action_line, client)
        else:
            logging.error("Auto re-login failed for user %s.", client.username)

    if isinstance(resp, dict) and "message" in resp:
        print(f"{BLUE}{resp['message']}{RESET}")
    elif resp is not None:
        print(f"{BLUE}{resp}{RESET}")
    else:
        print(f"{RED}No response received.{RESET}")

    return None

def process_actions_file(file_path, client):
    """
    Continuously reads the user's actions file (actions/<username>.txt), processes the first action,
    deletes it from the file, and repeats the process until a 'close' command is encountered.
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

        # Rewrite the file with the remaining lines
        with open(file_path, "w") as f:
            f.writelines(lines[1:])

        if result == "close":
            break

        time.sleep(DEFAULT_DELAY)

def main():
    setup_logging_to_file()

    client = MOMClient()
    client.subscribed_channels = {}

    print("Verifying connection with the API...")
    home_msg = client.get_home_message()
    if not home_msg:
        print(f"{RED}Connection error: Cannot access the API.{RESET}")
        logging.error("Connection failed: Home endpoint not accessible.")
        sys.exit(1)
    print(f"{GREEN}Successfully connected to the API. Welcome message:{RESET}")
    print(f"{GREEN}{home_msg}{RESET}")

    usuario, contraseña = get_next_credential()
    print(f"{BLUE}Using credentials for user: {usuario}{RESET}")

    # Store credentials in client for auto re-login
    client.username = usuario
    client.password = contraseña

    setup_user_file_logger(usuario)

    print("Attempting to log in, please wait...")
    login_resp = client.login(usuario, contraseña)
    if not login_resp:
        print(f"{RED}Login error: Please verify your credentials.{RESET}")
        logging.error("Login failed for user: %s", usuario)
        sys.exit(1)
    print(f"{GREEN}Login successful!{RESET}")
    logging.info("Login successful for user: %s", usuario)

    # Start subscription listening in the background (thread is daemon)
    listener_thread = threading.Thread(target=listen_subscriptions, args=(client,), daemon=True)
    listener_thread.start()

    # Determine the actions file path (per-user)
    actions_dir = "actions"
    if not os.path.exists(actions_dir):
        os.makedirs(actions_dir)
    actions_file = os.path.join(actions_dir, f"{usuario}.txt")
    if not os.path.exists(actions_file):
        logging.info("Actions file '%s' not found; creating an empty file.", actions_file)
        with open(actions_file, "w") as f:
            pass
        print(f"{YELLOW}Actions file created: {actions_file}{RESET}")

    print(f"\nStarting to process actions from '{actions_file}'...")
    logging.info("Processing actions from '%s'", actions_file)
    process_actions_file(actions_file, client)

    print(f"{GREEN}Client terminated.{RESET}")
    logging.info("Client terminated.")

if __name__ == "__main__":
    main()
