"""
Redis Database Connection Pool
"""
from app.config.env import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from app.adapters.db import Database
from redis import Redis, ConnectionPool, ConnectionError as RedisConnectionError


class RedisDatabase(Database):
    """
    Manages Redis connection pool and provides client access
    with proper application lifecycle management
    """
    def __init__(self):
        """
        Initialize RedisDatabase with connection pool
        """
        self._client: Redis = None
        self._connected: bool = False
        self._pool: ConnectionPool = None

    def get_client(self) -> Redis:
        """
        Get the shared Redis client with connection pool
        
        Returns:
            Redis: Redis client instance
        """
        if not self._connected:
            self._pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
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
            self._reconnect()

        return self._client

    def _reconnect(self) -> None:
        """
        Reconnect to the Redis server
        """
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
