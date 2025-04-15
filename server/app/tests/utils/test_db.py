"""Test the db initialization"""
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.env import API_NAME, API_VERSION, DEFAULT_USER_NAME, DEFAULT_USER_PASSWORD
from app.dtos.admin.mom_management_dto import QueueTopic
from app.utils.db import initialize_database, generate_keys, backup_database, get_elements_from_db
from fastapi.testclient import TestClient
from app.app import app
import pytest
import time


client = TestClient(app)


# Erase Redis data before each test
@pytest.fixture(autouse=True)
def clear_redis():
    db = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)

    client = db.get_client()
    client.flushdb()
    db_mom_client = db_mom.get_client()
    db_mom_client.flushdb()
    initialize_database()
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
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": DEFAULT_USER_NAME,
        "password": DEFAULT_USER_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    
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
    for element in elements:
        response = client.put(
            f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
            headers=headers,
            json={
                "name": element.name,
                "type": element.type.value
            }
        )
        assert response.status_code == 200
        data = response.json()
        queue_topic = "Queue " if element.type.value == "queue" else "Topic "
        assert queue_topic + element.name + " created successfully" == data["message"]
        assert True == data["success"]
        
        response = client.post(
            f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
            headers=headers,
            json={
                "name": element.name,
                "type": element.type.value,
                "message": "Hello, World!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected_message = "" 
        if element.type.value == "queue":
            expected_message = "Message enqueued successfully"
        else:
            expected_message = "Message published to topic topic-example, but replication failed"
            
        assert expected_message == data["message"]
        assert True == data["success"]
        
    new_elements = get_elements_from_db()

    backup_database(new_elements)
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    redis_mom = db_mom.get_client()
    
    # Verify that the keys are generated correctly
    for element in elements:
        keys = generate_keys(element.name, element.type.value)
        for key in keys:
            assert redis_mom.exists(key), f"Key {key} should exist in backup database"


def test_get_elements_from_db():
    """Test database elements."""
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": DEFAULT_USER_NAME,
        "password": DEFAULT_USER_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    
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
    for element in elements:
        response = client.put(
            f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
            headers=headers,
            json={
                "name": element.name,
                "type": element.type.value
            }
        )
        assert response.status_code == 200
        data = response.json()
        queue_topic = "Queue " if element.type.value == "queue" else "Topic "
        assert queue_topic + element.name + " created successfully" == data["message"]
        assert True == data["success"]
        
                
        response = client.post(
            f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
            headers=headers,
            json={
                "name": element.name,
                "type": element.type.value,
                "message": "Hello, World!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        expected_message = "" 
        if element.type.value == "queue":
            expected_message = "Message enqueued successfully"
        else:
            expected_message = "Message published to topic topic-example, but replication failed"
            
        assert expected_message == data["message"]
        assert True == data["success"]
    
    db_elements = get_elements_from_db()
    assert len(db_elements) == len(elements), "Should retrieve all elements from the database"
    for element in db_elements:
        assert element in elements, f"Element {element} should be in the database"
