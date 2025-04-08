"""
Redis Database Connection Pool
"""
from app.adapters.db import Database
from app.config.logging import logger
from redis import Redis, ConnectionPool, ConnectionError as RedisConnectionError


class RedisDatabase(Database):
    """
    Manages Redis connection pool and provides client access
    with proper application lifecycle management
    """
    def __init__(self, host: str, port: int, password: str) -> None:
        """
        Initialize RedisDatabase with connection pool
        """
        self._client: Redis = None
        self._connected: bool = False
        self._pool: ConnectionPool = None
        self._host = host
        self._port = port
        self._password = password
        self._max_retries = 3

    def get_client(self) -> Redis:
        """
        Get the shared Redis client with connection pool
        
        Returns:
            Redis: Redis client instance
        """
        if not self._connected:
            self._pool = ConnectionPool(
                host=self._host,
                port=self._port,
                password=self._password,
                decode_responses=True,
                max_connections=10,
                health_check_interval=30,
                socket_keepalive=True
            )
            self._connected = True

        if not self._client:
            self._client = Redis(connection_pool=self._pool)

        try:
            self._client.ping()
        except RedisConnectionError:
            self._reconnect(attempt=1)

        return self._client

    def _reconnect(self, attempt: int) -> None:
        """
        Reconnect to the Redis server with a limited number of retries
        
        Args:
            attempt (int): Current attempt number
            
        Raises:
            RedisConnectionError: If the connection fails after max retries
        """
        if attempt > self._max_retries:
            logger.error(
                "Failed to reconnect to Redis at %s:%s after %s attempts.",
                self._host,
                self._port,
                self._max_retries
            )
            raise RedisConnectionError(
                f"Could not connect to Redis at {self._host}" \
                + f":{self._port} after {self._max_retries} attempts."
            )
        self.close()
        self.get_client()

    def close(self) -> None:
        """
        Close the connection pool
        """
        if self._client:
            self._client.close()
        if self._pool:
            self._pool.disconnect()

        self._connected = False
        self._client = None
        self._pool = None
