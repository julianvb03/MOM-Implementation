# MOM Client - Message Oriented Middleware

This is the client implementation for the MOM (Message Oriented Middleware) system, developed as part of the Telematics Project at Universidad EAFIT.

It supports two types of clients: **producers** and **subscribers**, and allows registration, authentication, and message exchange via HTTP with a REST API.

---

## 🔧 Requirements

- Python 3.10+
- pip
- A running MOM server with REST API supporting:
  - `POST /register`
  - `POST /login`
  - `POST /topics/{name}/messages`
  - `GET /topics/{name}/messages`
  - (or `/queues/{name}/messages` if using queues)

---

## 📁 Project Structure

```
client/
├── venv/                # Virtual environment (not committed)
├── mom_client.py        # Core client logic (register, login, send/receive)
├── main.py              # Entry point for running the client
├── message.txt          # Input file (used by producers)
├── log.txt              # Log of sent/received messages
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## ⚙️ Setup

1. **Create and activate the virtual environment**

```bash
python -m venv venv
.\venv\Scripts\activate     # On Windows
```

2. **Install dependencies**

```bash
pip install requests
```

3. (Optional) Save dependencies:

```bash
pip freeze > requirements.txt
```

---

## ▶️ How to Run

1. Make sure your MOM REST server is running (e.g. on `http://localhost:8000/api`)

2. Run the client:

```bash
python main.py
```

3. Choose one of the options:
   - `register` → Create a new user account
   - `login` → Authenticate and continue as producer or subscriber

---

## 📤 Producer Mode

- Reads messages from `message.txt`
- Each line must follow the format: `Message,Name`
- Messages are sent to a topic or queue
- Messages are logged to `log.txt`
- `message.txt` is cleared after sending

Example:
```
Hello from Chepe,Chepe
Testing my MOM client,Dayana
```

---

## 📥 Subscriber Mode

- Polls a topic or queue for messages
- Received messages are printed and saved in `log.txt`

---

## 📌 Notes

- All messages and logs are stored in plain `.txt` files.
- Only users with valid credentials can send/receive messages.
- You can switch between producer and subscriber roles at runtime.

---

## 🧑‍💻 Author

José Agudelo (Chepe)  
Universidad EAFIT - Tópicos de Telemática (2025-1)
