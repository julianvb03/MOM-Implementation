# MOM Client

MOM Client is a Python application that communicates with a Message Oriented Middleware (MOM) API. The client supports various operations for both topics and queues, including:

- **Home:** Check API connectivity.
- **Login:** Authenticate the user.
- **Subscribe:** Subscribe to a channel (queue or topic).
- **Unsubscribe:** Unsubscribe from a channel.
- **Send Message:** Send a message to a channel.
- **Close:** Stop the client.
- **Action Processing:** The client reads commands continuously from a user-specific actions file.

All detailed log messages are saved to files in the `logs/` folder. A global log is saved in `logs/app.log`, and each user has a dedicated log file named `<username>.log`.

> **Note:**  
> The "receive" command is not used as an action in the file because the client listens continuously on subscribed channels in the background.

## Project Structure

```plaintext
my_mom_client/
├── actions/                  # Folder for per-user actions files (e.g., julian.txt)
├── env/                      # Virtual environment folder (do not version control)
├── logs/                     # Folder for log files (e.g., app.log, <username>.log)
├── src/
│   ├── client/
│   │   ├── __init__.py       # (Empty)
│   │   ├── mom_client.py     # Contains the MOMClient class with API methods (login, subscribe, etc.)
│   │   └── utils.py          # Utility functions (read_config, do_request, etc.)
│   ├── __init__.py           # (Empty)
│   ├── config.yaml           # Configuration file (API URL, credentials, timeout, etc.)
│   └── main.py               # Main entry point for the client application
├── tests/                    # (Optional) Folder for tests
│   ├── __init__.py           # (Empty)
│   └── test_mom_client.py    # Test suite for the client (excluding action file processing)
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Prerequisites

- **Python 3.8+** – [Download Python](https://www.python.org/downloads/)
- **pip** – Python package installer  
- Recommended: use a virtual environment (e.g., `venv`)

## Installation

1. **Clone the repository:**

```bash
git clone <repository_url>
cd my_mom_client
```

2. **Create and activate a virtual environment:**

- **Linux/macOS:**
  ```bash
  python -m venv env
  source env/bin/activate
  ```
- **Windows (CMD):**
  ```cmd
  python -m venv env
  env\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```powershell
  python -m venv env
  .\env\Scripts\Activate.ps1
  ```

3. **Install required packages:**

```bash
pip install -r requirements.txt
```

## Configuration

Edit the `src/config.yaml`:

```yaml
api_base_url: "http://localhost:8080/api/v1.0.0/MomServer"
credentials:
  username: "admin"
  password: "123"
timeout: 10  # seconds
```

## Actions File Format

Each user has their own actions file in `actions/<username>.txt`. Commands:

- **Subscribe:**
  ```
  subscribe;channel;type
  ```

- **Unsubscribe:**
  ```
  unsubscribe;channel;type
  ```

- **Send Message:**
  ```
  send;channel;message;type
  ```

- **Close:**
  ```
  close
  ```

## Running the Client

1. **Prepare Actions File:**

```plaintext
subscribe;queue-example;queue
send;queue-example;Hello, world!;queue
unsubscribe;queue-example;queue
close
```

2. **Run Client:**

```bash
python src/main.py
```

- Client verifies API connectivity.
- Prompts user credentials.
- Logs are in `logs/app.log` and `logs/<username>.log`.
- Actions from `actions/<username>.txt` processed sequentially.

## Example Client Session

```plaintext
Verifying connection with the API...
Conexión exitosa con la API. Mensaje de bienvenida:
Welcome to MOM API!

Ingrese su usuario: julian
Ingrese su contraseña: ********

Intentando autenticar, por favor espere...
Login exitoso!

Archivo de acciones creado: actions/julian.txt

Starting processing of actions from 'actions/julian.txt'...
Hello, world!           ← (Printed in blue from the "send" action)
close                   ← (Printed in yellow indicating closure)
Cliente finalizado.
```

Detailed logs are in `logs/app.log` and `logs/julian.log`.

## Troubleshooting

- Check API server URL in `src/config.yaml`.
- Actions file auto-created if missing; populate commands.
- Logs in `logs/` contain detailed error messages.

## Additional Information

- Continuous action file monitoring and command execution.
- Minimal terminal output; detailed logging in files.

Enjoy using the MOM Client!