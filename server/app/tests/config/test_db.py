"""Test the db initialization"""
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.db import RedisDatabase
import redis


def test_singleton():
    """Test that the database instance is a singleton."""
    db1 = ObjectFactory.get_instance(Database)
    db2 = ObjectFactory.get_instance(Database)

    assert db1 is db2, "Database instances are not the same"


def test_redis_client():
    """Test that the Redis Database is created correctly."""
    db = ObjectFactory.get_instance(Database)

    assert isinstance(
        db,
        RedisDatabase
    ), "Database should be of type RedisDatabase"


def test_redis_client_initialization():
    """Test that the Redis client is initialized correctly."""
    db = ObjectFactory.get_instance(Database)

    # Check if the client is initialized
    client = db.get_client()

    assert client is not None, "Redis client should not be None"

    # Check if the client is of type redis.Redis
    assert isinstance(
        client,
        redis.Redis
    ), "Client should be of type redis.Redis"

    # Make a ping to check if the connection is alive
    try:
        ping = client.ping()
        assert ping is True, "Ping should return True"
    except redis.ConnectionError:
        assert False, "Redis client connection failed"
