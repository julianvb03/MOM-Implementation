import requests
import os

class MOMClient:
    def __init__(self, base_url, username, password, client_type):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client_type = client_type.lower()
        self.token = None
        self.session = requests.Session()
        self.log_file = "log.txt"
        self.input_file = "message.txt"

    def register_user(self):
        url = f"{self.base_url}/register"
        data = {"username": self.username, "password": self.password}
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            print("[✔] User registered successfully.")
            return True
        except Exception as e:
            print(f"[✖] Registration failed: {e}")
            return False

    def authenticate(self):
        url = f"{self.base_url}/login"
        data = {"username": self.username, "password": self.password}
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            self.token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("[✔] Authenticated successfully.")
            return True
        except Exception as e:
            print(f"[✖] Authentication failed: {e}")
            return False

    def log(self, entry):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def read_messages(self):
        if not os.path.exists(self.input_file):
            print("[!] 'message.txt' does not exist.")
            return []
        with open(self.input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        messages = [line.strip().split(",", 1) for line in lines if "," in line]
        return messages

    def clear_input_file(self):
        open(self.input_file, "w", encoding="utf-8").close()

    def send_messages(self, destination_type="topics", destination_name="general"):
        messages = self.read_messages()
        if not messages:
            print("[i] No messages to send.")
            return
        for content, sender in messages:
            payload = {"message": content.strip(), "name": sender.strip()}
            try:
                url = f"{self.base_url}/{destination_type}/{destination_name}/messages"
                response = self.session.post(url, json=payload)
                response.raise_for_status()
                self.log(f"[SENT] ({sender}) → {content}")
                print(f"[✔] Sent: ({sender}) {content}")
            except Exception as e:
                print(f"[✖] Failed to send message: {e}")
        self.clear_input_file()

    def receive_messages(self, destination_type="topics", destination_name="general"):
        try:
            url = f"{self.base_url}/{destination_type}/{destination_name}/messages"
            response = self.session.get(url)
            response.raise_for_status()
            messages = response.json().get("messages", [])
            if not messages:
                print("[i] No new messages.")
                return
            for msg in messages:
                content = msg.get("message")
                sender = msg.get("name")
                self.log(f"[RECEIVED] ({sender}) → {content}")
                print(f"[📥] Received: ({sender}) {content}")
        except Exception as e:
            print(f"[✖] Failed to receive messages: {e}")
