"""
Test the home routes
"""
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.app import app
from app.config.env import API_NAME, API_VERSION, DEFAULT_USER_NAME, DEFAULT_USER_PASSWORD
from app.utils.db import initialize_database
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def initialize_test_db():
    """
    Fixture to initialize the test database before each test.
    This ensures that each test runs with a fresh database state.
    """
    db = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)

    db_client = db.get_client()
    db_client.flushdb()

    initialize_database()
    db_mom_client = db_mom.get_client()
    db_mom_client.flushdb()

    yield

    # Cleanup after tests
    db_client.flushdb()
    db_mom_client.flushdb()


def test_create_queue_topic_success():
    """
    Test the create queue topic endpoint
    """
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
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue queue-example created successfully" == data["message"]
    assert True == data["success"]

    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]
    
    
def test_create_queue_topic_failure_duplicated():
    """
    Test the create queue topic endpoint with duplicated name
    """
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
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue queue-example created successfully" == data["message"]
    assert True == data["success"]

    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]
    
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue exists" == data["message"]
    assert True == data["success"]
    
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Topic exists" == data["message"]
    assert False == data["success"]


def test_delete_queue_topic():
    """
    Test the delete queue topic endpoint
    """
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
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue queue-example created successfully" == data["message"]
    assert True == data["success"]

    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]
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
    
    response = client.delete(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/delete/queue-example?mom_type=queue",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue 'queue-example' deleted successfully" == data["message"]
    assert True == data["success"]
    
    response = client.delete(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/delete/topic-example?mom_type=topic",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example deleted successfully" == data["message"]
    assert True == data["success"]


def test_delete_queue_topic_failure():
    """
    Test the delete queue topic endpoint
    """
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
    
    response = client.delete(
        f"/api/{API_VERSION}/{API_NAME}/admin/queue_topic/delete/queue-example?mom_type=queue",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "Queue does not exist" == data["message"]
    assert False == data["success"]
