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

CONFIG_FILE   = "src/config.yaml"
ACTIONS_DIR   = "actions"
DEFAULT_DELAY = 1  # seconds between processing actions

def setup_logging_to_file():
    """Log all INFO+ messages into logs/app.log only."""
    os.makedirs("logs", exist_ok=True)
    handler = logging.FileHandler("logs/app.log", mode="a")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)

def setup_user_file_logger(username):
    """Also log INFO+ messages to logs/<username>.log."""
    os.makedirs("logs", exist_ok=True)
    handler = logging.FileHandler(f"logs/{username}.log", mode="a")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(handler)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{RED}Failed to load config: {e}{RESET}")
        sys.exit(1)

def update_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)
    except Exception as e:
        print(f"{RED}Failed to update config: {e}{RESET}")

def get_next_credential():
    cfg = load_config()
    creds = cfg.get("credentials", [])
    if not creds:
        print(f"{RED}No more credentials available.{RESET}")
        sys.exit(1)
    cred = creds.pop(0)
    cfg["credentials"] = creds
    update_config(cfg)
    return cred["username"], cred["password"]

def listen_subscriptions(client):
    """
    Background thread: every second, poll each subscribed channel.
    On Unauthorized (resp None), auto re-login and retry once.
    Print only non-empty messages.
    """
    while True:
        for channel, qtype in client.subscribed_channels.items():
            resp = client.receive_message(channel, qtype)
            if resp is None:
                # Assume Unauthorized: retry login
                logging.error("Unauthorized on receive for %s; auto re-login.", client.username)
                if client.login(client.username, client.password):
                    logging.info("Re-login successful in listener for %s", client.username)
                    # retry once
                    resp = client.receive_message(channel, qtype)
                else:
                    logging.error("Re-login failed in listener for %s", client.username)
                    continue
            # if we have a dict with success/message, print non-empty
            if isinstance(resp, dict) and resp.get("success") and resp.get("message"):
                msg = resp["message"].strip()
                if msg:
                    print(f"{BLUE}[{channel}] {msg}{RESET}")
        time.sleep(1)

def process_action(line, client):
    parts = line.strip().split(";")
    if not parts:
        return None

    cmd = parts[0].lower()
    resp = None

    def retry_login_and_retry():
        logging.info("Attempting auto re-login for %s", client.username)
        if client.login(client.username, client.password):
            logging.info("Re-login successful for %s; retrying '%s'", client.username, cmd)
            return process_action(line, client)
        else:
            print(f"{RED}Re-login failed for {client.username}.{RESET}")
            logging.error("Re-login failed for %s", client.username)
            return None

    if cmd == "subscribe" and len(parts) == 3:
        name, qtype = parts[1], parts[2]
        resp = client.subscribe(name, qtype)
        if resp is None:
            return retry_login_and_retry()
        if isinstance(resp, dict) and "message" in resp:
            print(f"{BLUE}{resp['message']}{RESET}")
        text = (resp.get("message") or "").lower() if isinstance(resp, dict) else ""
        if (isinstance(resp, dict) and resp.get("success")) or "subscribed" in text:
            client.subscribed_channels[name] = qtype
            logging.info("Listening on %s '%s'", qtype, name)

    elif cmd == "unsubscribe" and len(parts) == 3:
        name, qtype = parts[1], parts[2]
        resp = client.unsubscribe(name, qtype)
        if resp is None:
            return retry_login_and_retry()
        if isinstance(resp, dict) and "message" in resp:
            print(f"{BLUE}{resp['message']}{RESET}")
        if isinstance(resp, dict) and resp.get("success"):
            client.subscribed_channels.pop(name, None)

    elif cmd == "send" and len(parts) == 4:
        resp = client.send_message(parts[1], parts[2], parts[3])
        if resp is None:
            return retry_login_and_retry()
        if isinstance(resp, dict) and "message" in resp:
            print(f"{BLUE}{resp['message']}{RESET}")

    elif cmd == "close":
        print(f"{YELLOW}close{RESET}")
        logging.info("Received 'close'; shutting down.")
        return "close"

    else:
        msg = f"Malformed command: {line.strip()}"
        print(f"{RED}{msg}{RESET}")
        logging.warning(msg)
        return None

    logging.info("Action '%s' executed. Full response: %s", cmd, resp)
    return None

def process_actions_file(path, client):
    """Continuously read/execute first line from path, remove it, until 'close'."""
    while True:
        if not os.path.exists(path):
            time.sleep(1)
            continue
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines:
            time.sleep(1)
            continue

        first = lines[0]
        result = process_action(first, client)
        with open(path, "w") as f:
            f.writelines(lines[1:])
        if result == "close":
            break
        time.sleep(DEFAULT_DELAY)

def main():
    setup_logging_to_file()
    client = MOMClient()
    client.subscribed_channels = {}

    # 1) Home check
    print("Verifying connection with the API...")
    home = client.get_home_message()
    if not home:
        print(f"{RED}Cannot reach API.{RESET}")
        logging.error("Home endpoint unreachable.")
        sys.exit(1)
    print(f"{GREEN}Connected. Welcome:{RESET}\n{GREEN}{home}{RESET}")

    # 2) Credentials & login
    user, pwd = get_next_credential()
    client.username, client.password = user, pwd
    print(f"{BLUE}Using credentials for user: {user}{RESET}")
    setup_user_file_logger(user)
    print("Logging in...")
    if not client.login(user, pwd):
        print(f"{RED}Login failed.{RESET}")
        logging.error("Login failed for %s", user)
        sys.exit(1)
    print(f"{GREEN}Login successful!{RESET}")
    logging.info("User %s logged in", user)

    # 3) Start listener thread
    threading.Thread(target=listen_subscriptions, args=(client,), daemon=True).start()

    # 4) Ensure actions file exists
    os.makedirs(ACTIONS_DIR, exist_ok=True)
    path = os.path.join(ACTIONS_DIR, f"{user}.txt")
    if not os.path.exists(path):
        open(path, "w").close()
        print(f"{YELLOW}Created actions file: {path}{RESET}")
        logging.info("Created actions file %s", path)

    # 5) Process actions until 'close'
    print(f"\nProcessing actions in '{path}'...")
    process_actions_file(path, client)

    print(f"{GREEN}Client terminated.{RESET}")
    logging.info("Client terminated for %s", user)

if __name__ == "__main__":
    main()
