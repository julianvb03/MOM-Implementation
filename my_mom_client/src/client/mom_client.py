import logging
from .utils import read_config, do_request

logger = logging.getLogger(__name__)

class MOMClient:
    def __init__(self):
        """
        Inicializa el cliente leyendo la configuración, la URL base, y otros parámetros.
        También carga las credenciales y prepara variables para almacenar el token.
        """
        self.logger = logger
        self.config = read_config()
        self.base_url = self.config.get("api_base_url")
        self.timeout = self.config.get("timeout", 10)
        self.credentials = self.config.get("credentials", {})
        self.token = None
        self.token_type = None

    def get_home_message(self):
        """
        Realiza una petición GET al endpoint raíz para obtener el mensaje de bienvenida.
        Se usa la URL base.
        """
        url = self.base_url  # Se espera que el endpoint home sea la URL base
        return do_request("GET", url, timeout=self.timeout)

    def login(self, username=None, password=None):
        """
        Realiza la autenticación enviando una petición POST con credenciales.
        Usa las credenciales del config si no se pasan.
        Guarda internamente el token y token_type para llamadas futuras.
        Retorna la respuesta de autenticación o None en caso de error.
        """
        if not username:
            username = self.credentials.get("username")
        if not password:
            password = self.credentials.get("password")
        if not username or not password:
            self.logger.error("No credentials provided for login.")
            return None

        url = f"{self.base_url}/login/"
        payload = {"username": username, "password": password}
        response = do_request("POST", url, json=payload, timeout=self.timeout)
        if response and "access_token" in response and "token_type" in response:
            self.token = response["access_token"]
            self.token_type = response["token_type"]
            #self.logger.info("Login successful.")
            return response
        self.logger.error("Login failed: %s", response)
        return None

    def subscribe(self, name, qtype):
        """
        Se suscribe a un queue o topic.
        name: nombre del canal.
        qtype: "queue" o "topic".
        Retorna la respuesta de la API.
        """
        url = f"{self.base_url}/queue_topic/subscribe/"
        headers = {}
        if self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
        payload = {"name": name, "type": qtype}
        return do_request("POST", url, headers=headers, json=payload, timeout=self.timeout)

    def unsubscribe(self, name, qtype):
        """
        Se desuscribe de un queue o topic.
        Retorna la respuesta de la API.
        """
        url = f"{self.base_url}/queue_topic/unsubscribe/"
        headers = {}
        if self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
        payload = {"name": name, "type": qtype}
        return do_request("POST", url, headers=headers, json=payload, timeout=self.timeout)

    def send_message(self, name, message, qtype):
        """
        Envía un mensaje a un queue o topic.
        Retorna la respuesta de la API.
        """
        url = f"{self.base_url}/queue_topic/send/"
        headers = {}
        if self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
        payload = {"name": name, "message": message, "type": qtype}
        return do_request("POST", url, headers=headers, json=payload, timeout=self.timeout)

    def receive_message(self, name, qtype):
        """
        Recibe el siguiente mensaje de un queue o topic.
        Retorna la respuesta de la API.
        """
        url = f"{self.base_url}/queue_topic/receive/"
        headers = {}
        if self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
        payload = {"name": name, "type": qtype}
        return do_request("POST", url, headers=headers, json=payload, timeout=self.timeout)

    def get_protected_resource(self):
        """
        Realiza una petición GET al endpoint protegido.
        Retorna la respuesta o None en caso de error.
        """
        url = f"{self.base_url}/protected/"
        headers = {}
        if self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
        return do_request("GET", url, headers=headers, timeout=self.timeout)
