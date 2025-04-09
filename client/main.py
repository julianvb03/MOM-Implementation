from mom_client import MOMClient

def main():
    print("=== MOM CLIENT ===")
    action = input("Do you want to register or login? (register/login): ").strip().lower()
    if action not in ["register", "login"]:
        print("❌ Invalid action.")
        return

    username = input("Username: ").strip()
    password = input("Password: ").strip()

    base_url = input("Enter MOM base URL (e.g. http://localhost:8000/api): ").strip()

    if action == "register":
        client = MOMClient(base_url, username, password, "producer")  # type doesn't matter yet
        client.register_user()
        return

    client_type = input("Enter client type (producer / subscriber): ").strip().lower()
    if client_type not in ["producer", "subscriber"]:
        print("❌ Invalid client type.")
        return

    destination_type = input("Destination type (topics / queues): ").strip().lower()
    destination_name = input("Destination name (e.g. general): ").strip()

    client = MOMClient(base_url, username, password, client_type)

    if not client.authenticate():
        return

    if client_type == "producer":
        client.send_messages(destination_type, destination_name)
    elif client_type == "subscriber":
        client.receive_messages(destination_type, destination_name)

if __name__ == "__main__":
    main()
