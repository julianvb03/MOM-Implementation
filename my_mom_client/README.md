# MOM Client

MOM Client is a Python application that communicates with a Message Oriented Middleware (MOM) API. The client supports various operations for both topics and queues, including:

- **Home:** Check API connectivity.  
- **Login:** Authenticate the user.  
- **Subscribe:** Subscribe to a channel (queue or topic).  
- **Unsubscribe:** Unsubscribe from a channel.  
- **Send Message:** Send a message to a channel.  
- **Close:** Stop the client.  
- **Action Processing:** Read commands from a per‑user file in `actions/<username>.txt`.  
- **Background Listener:** Continuously listen (every second) for messages on all subscribed channels.  
- **Automatic Re‑login:** On any 401 Unauthorized, the client will auto re‑authenticate and retry the failed request.  

All detailed log messages are saved to `logs/app.log` (global) and `logs/<username>.log` (per user). The terminal shows only the response messages in color.

> **Note:**  
> The listener prints only non‑empty messages. If a queue/topic is empty, no output appears.

---

## Project Structure

```
my_mom_client/
├── .gitignore
├── README.md
├── requirements.txt
├── actions/                  # Per-user action files
│   ├── admin.txt
│   └── julian.txt
├── env/                      # Virtual environment (ignored)
├── logs/                     # Log files (ignored)
├── src/
│   ├── __init__.py
│   ├── config.yaml           # API URL, credential list, timeout
│   ├── main.py               # Entry point with error handling & listener
│   └── client/
│       ├── __init__.py
│       ├── mom_client.py     # MOMClient class (login, subscribe, etc.)
│       └── utils.py          # Helpers (read_config, do_request, etc.)
└── tests/                    # Optional tests
    ├── __init__.py
    ├── queue_utils.py
    └── test_mom_client.py
```

---

## Prerequisites

- **Python 3.8+**  
- **pip** (or `python -m pip`)  
- Recommended: use a virtual environment (e.g. `venv`)

---

## Installation

1. **Clone & enter project:**
   ```bash
   git clone <repository_url>
   cd my_mom_client
   ```

2. **Create & activate a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate      # Linux/macOS
   .\env\Scripts\Activate.ps1   # Windows PowerShell
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Edit `src/config.yaml`:

```yaml
api_base_url: "http://localhost:8080/api/v1.0.0/MomServer"
credentials:
  - username: "admin"
    password: "123"
  - username: "julian"
    password: "abc"
timeout: 10  # seconds
```

---

## Per‑User Actions

Each user has a file `actions/<username>.txt`. One command per line:

```
subscribe;my_queue;queue
send;my_queue;Hello from <user>;queue
unsubscribe;my_queue;queue

subscribe;my_topic;topic
send;my_topic;Message for <user>;topic
unsubscribe;my_topic;topic

close
```

---

## Running the Client

```bash
python src/main.py
```

1. Checks API home endpoint.  
2. Auto‑loads next credential and logs in.  
3. Starts background listener thread.  
4. Processes `actions/<username>.txt` until `close`.  
5. Handles 401 by auto re‑login & retry.  

---

## Troubleshooting

- Verify the `api_base_url` in `src/config.yaml`.  
- Populate `actions/<username>.txt` with valid commands.  
- Inspect detailed logs in `logs/` for errors.  

Enjoy using MOM Client!  