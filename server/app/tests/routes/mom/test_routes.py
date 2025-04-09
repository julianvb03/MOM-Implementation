"""
Test the home routes
"""
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.adapters.user_service import UserService
from app.app import app
from app.config.env import API_NAME, API_VERSION
from app.dtos.user_dto import UserDto
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

    db_client = db.get_client()
    db_client.flushdb()

    initialize_database()

    # Create a test user
    test_user = UserDto(
        username="noadmin",
        password="123",
    )

    # Create the user in the database
    user_service = ObjectFactory.get_instance(UserService)
    user_service.create_user(test_user)
    yield

    # Cleanup after tests
    db_client.flushdb()
    # Initialize the database before each test


def test_subscribe_queue_topic():
    """
    Test the subscribe queue topic endpoint
    """
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": "noadmin",
        "password": "123"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "noadmin subscribed to Queue queue-example successfully." == data


def test_subscribe_queue_topic_unauthorized():
    """
    Test the subscribe queue topic endpoint without token
    """
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_unsubscribe_queue_topic():
    """
    Test the unsubscribe queue topic endpoint
    """
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": "noadmin",
        "password": "123"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/unsubscribe",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "noadmin unsubscribed to Queue queue-example successfully." == data


def test_unsubscribe_queue_topic_unauthorized():
    """
    Test the unsubscribe queue topic endpoint without token
    """
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/unsubscribe",
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_send():
    """
    Test the send endpoint
    """
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": "noadmin",
        "password": "123"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "'Hello, World!' published by noadmin " \
        + "to Topic topic-example successfully." == data


def test_send_unauthorized():
    """
    Test the send endpoint without token
    """
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        json={
            "name": "topic-example",
            "type": "topic",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_receive():
    """
    Test the receive endpoint
    """
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": "noadmin",
        "password": "123"
    })
    assert response.status_code == 200
    data = response.json()
    token = data["access_token"]
    token_type = data["token_type"]
    headers = {
        "Authorization": f"{token_type} {token}"
    }
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/receive",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "'message' received by noadmin from Queue queue-example successfully." == data


def test_receive_unauthorized():
    """
    Test the receive endpoint without token
    """
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/receive",
        json={
            "name": "queue-example",
            "type": "queue"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"
