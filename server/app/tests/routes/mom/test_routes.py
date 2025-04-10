"""
Test the home routes
"""
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.adapters.user_service import UserService
from app.app import app
from app.config.env import API_NAME, API_VERSION, DEFAULT_USER_NAME, DEFAULT_USER_PASSWORD
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
    db_mom = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)

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

    db_mom_client = db_mom.get_client()
    db_mom_client.flushdb() 
    
    yield

    # Cleanup after tests
    db_client.flushdb()
    db_mom_client.flushdb()
    # Initialize the database before each test


def test_subscribe_queue_topic():
    """
    Test the subscribe queue topic endpoint
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
    
    # Suscribe test
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
    assert "User noadmin subscribed to queue-example" == data["message"]
    assert True == data["success"]
    
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin subscribed to topic topic-example" == data["message"]
    assert True == data["success"]


def test_subscribe_queue_topic_already_suscribed():
    """
    Test the subscribe queue topic endpoint
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

    # Suscribe test
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
    assert "User noadmin subscribed to queue-example" == data["message"]
    assert True == data["success"]

    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin subscribed to topic topic-example" == data["message"]
    assert True == data["success"]

    # Suscribe test again
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
    assert "User is subscribed" == data["message"]
    assert False == data["success"]
    
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin is already subscribed to topic topic-example" == data["message"]
    assert False == data["success"]


def test_suscribe_queue_topic_not_found():
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
    assert "Queue does not exist" == data["message"]
    assert False == data["success"]

    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example does not exist" == data["message"]
    assert False == data["success"]


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
    
    # Suscribe test
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
    assert "User noadmin subscribed to queue-example" == data["message"]
    assert True == data["success"]

    # Unsubscribe test
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
    assert "User noadmin unsubscribed from queue-example" == data["message"]
    assert True == data["success"]


def test_unsubscribe_queue_topic_already_unsubscribed():
    """
    Test the unsubscribe queue topic endpoint
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]
    
    # Suscribe test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin subscribed to topic topic-example" == data["message"]
    assert True == data["success"]

    # Unsubscribe test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin unsubscribed from topic topic-example" == data["message"]
    assert True == data["success"]


def test_unsubscribe_queue_topic_not_found():
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example does not exist" == data["message"]
    assert False == data["success"]


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
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]

    # Send test
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
    assert "Message published to topic topic-example, but replication failed" == data["message"]
    assert True == data["success"]


def test_send_queue_not_found():
    """
    Test the send endpoint with queue not found
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
    assert "Topic topic-example does not exist" == data["message"]
    assert False == data["success"]


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


def test_receive_topic():
    """
    Test the receive endpoint
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
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]

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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin subscribed to topic topic-example" == data["message"]
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
    assert "Message published to topic topic-example, but replication failed" == data["message"]
    assert True == data["success"]

    # Receive test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert True == data["success"]
    assert "Hello, World!" == data["message"]


def test_receive_queue():
    """
    Test the receive endpoint
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
    assert "User noadmin subscribed to queue-example" == data["message"]
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
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Message enqueued successfully" == data["message"]
    assert True == data["success"]

    # Receive test
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
    assert True == data["success"]
    assert "Hello, World!" == data["message"]


def test_receive_topic_same_publish():
    """
    Test the receive endpoint with the same publish user
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
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]

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
    assert "Message published to topic topic-example, but replication failed" == data["message"]
    assert True == data["success"]

    # Receive test
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/receive",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert True == data["success"]
    assert None == data["message"]


def test_receive_queue_same_publish():
    """
    Test the receive endpoint with the same publish user
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

    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Message enqueued successfully" == data["message"]
    assert True == data["success"]

    # Receive test
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
    assert True == data["success"]
    assert "Hello, World!" == data["message"]


def test_receive_topic_empty():
    """
    Test the receive endpoint with queue empty
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
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]

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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User noadmin subscribed to topic topic-example" == data["message"]
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
    assert "Message published to topic topic-example, but replication failed" == data["message"]
    assert True == data["success"]

    # Receive test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert True == data["success"]
    assert "Hello, World!" == data["message"]
    
    # Receive test again
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/receive",
        headers=headers,
        json={
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert True == data["success"]
    assert None == data["message"]


def test_receive_queue_empty():
    """
    Test the receive endpoint with queue empty
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
    assert "User noadmin subscribed to queue-example" == data["message"]
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
    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Message enqueued successfully" == data["message"]
    assert True == data["success"]

    # Receive test
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
    assert True == data["success"]
    assert "Hello, World!" == data["message"]
    
    # Receive test again
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
    assert True == data["success"]
    assert None == data["message"]


def test_receive_topic_not_suscribed():
    """
    Test the receive endpoint with queue topic not suscribed
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
            "name": "topic-example",
            "type": "topic"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "Topic topic-example created successfully" == data["message"]
    assert True == data["success"]

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
    assert "Message published to topic topic-example, but replication failed" == data["message"]
    assert True == data["success"]

    # Receive test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert False == data["success"]
    assert "User is not subscribed to this topic" == data["message"]


def test_receive_queue_not_suscribed():
    """
    Test the receive endpoint with queue topic not suscribed
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

    response = client.post(
        f"/api/{API_VERSION}/{API_NAME}/queue_topic/send",
        headers=headers,
        json={
            "name": "queue-example",
            "type": "queue",
            "message": "Hello, World!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "Message enqueued successfully" == data["message"]
    assert True == data["success"]

    # Receive test
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
    assert False == data["success"]
    assert "User is not subscribed" == data["message"]



def test_receive_queue_not_found():
    """
    Test the receive endpoint with queue topic not created
    """
    # Receive test
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
    assert False == data["success"]
    assert "Queue does not exist" == data["message"]


def test_receive_topic_not_found():
    """
    Test the receive endpoint with queue topic not created
    """
    # Receive test
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
            "name": "topic-example",
            "type": "topic"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert False == data["success"]
    assert "Topic does not exist" == data["message"]


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
