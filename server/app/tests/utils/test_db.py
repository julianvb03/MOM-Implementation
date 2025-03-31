"""Test the db initialization"""
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.env import DEFAULT_USER_NAME
from app.utils.db import initialize_database
import pytest


# Erase Redis data before each test
@pytest.fixture(autouse=True)
def clear_redis():
    db = ObjectFactory.get_instance(Database)

    client = db.get_client()
    client.flushdb()
    yield
    # Cleanup after tests
    client.flushdb()


def test_initialize_database():
    """Test database initialization with default admin and config."""
    # Initialize database
    initialize_database()

    db = ObjectFactory.get_instance(Database)
    redis = db.get_client()

    # Verify admin exists
    admin_user = redis.hget("users", DEFAULT_USER_NAME)
    assert admin_user is not None, "Default admin not created"

    # Verify Redis config
    maxmemory = redis.config_get("maxmemory")
    assert maxmemory.get("maxmemory") == "268435456", \
        "Should be 256MB in bytes"

    policy = redis.config_get("maxmemory-policy")
    assert policy.get("maxmemory-policy") == "allkeys-lru", \
        "Wrong eviction policy"
