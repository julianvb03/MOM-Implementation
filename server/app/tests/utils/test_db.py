"""Test the db initialization"""
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.env import DEFAULT_USER_NAME
from app.dtos.admin.mom_management_dto import QueueTopic
from app.utils.db import initialize_database, generate_keys, backup_database
import pytest


# Erase Redis data before each test
@pytest.fixture(autouse=True)
def clear_redis():
    db = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)

    client = db.get_client()
    client.flushdb()
    db_mom_client = db_mom.get_client()
    db_mom_client.flushdb()
    yield
    # Cleanup after tests
    client.flushdb()
    db_mom_client.flushdb()


def test_initialize_database():
    """Test database initialization with default admin and config."""
    # Initialize database
    initialize_database()

    db = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
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


def test_generate_keys():
    """Test key generation for queues and topics."""
    # Test queue keys
    queue_name = "test_queue"
    queue_keys = generate_keys(queue_name, "queue")

    assert len(queue_keys) == 3, "Should generate 3 keys for queues"
    assert all(key.startswith(f"mom:queues:{queue_name}") for key in queue_keys), \
        "Keys should start with 'mom:queues:test_queue'"

    # Test topic keys
    topic_name = "test_topic"
    topic_keys = generate_keys(topic_name, "topic")

    assert len(topic_keys) == 4, "Should generate 4 keys for topics"
    assert all(key.startswith(f"mom:topics:{topic_name}") for key in topic_keys), \
        "Keys should start with 'mom:topics:test_topic'"


def test_backup_database():
    """Test database backup."""
    # Create a sample QueueTopic object
    elements = [
        QueueTopic(
            name="queue-example",
            type="queue",
        ),
        QueueTopic(
            name="topic-example",
            type="topic",
        )
    ]
    
    backup_database(elements)
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    redis_mom = db_mom.get_client()
    
    # Verify that the keys are generated correctly
    for element in elements:
        keys = generate_keys(element.name, element.type.value)
        for key in keys:
            assert redis_mom.exists(key), f"Key {key} should exist in backup database"
