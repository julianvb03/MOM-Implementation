import redis
import os
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

def get_redis_connection():
    """
    Creates and returns a Redis connection using environment variables.
    """
    return redis.StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )

def redis_set_json(redis_conn, key, value):
    """
    Stores a JSON-serializable Python object in Redis.
    """
    redis_conn.set(key, json.dumps(value))

def redis_get_json(redis_conn, key):
    """
    Retrieves and deserializes a JSON object stored in Redis.
    """
    data = redis_conn.get(key)
    return json.loads(data) if data else None
