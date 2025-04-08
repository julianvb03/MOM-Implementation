"""
Test the home routes
"""
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.adapters.user_service import UserService
from app.dtos.user_dto import UserDto
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
    db = ObjectFactory.get_instance(Database)

    db_client = db.get_client()
    db_client.flushdb()

    initialize_database()

    # Create a test user
    test_user = UserDto(
        username="removal",
        password="123",
    )

    # Create the user in the database
    user_service = ObjectFactory.get_instance(UserService)
    user_service.create_user(test_user)

    yield

    # Cleanup after tests
    db_client.flushdb()
    # Initialize the database before each test


def test_remove_users():
    """
    Test the get protected admin endpoint /protected/admin/
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
        f"/api/{API_VERSION}/{API_NAME}/admin/users/remove/removal",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "User removal " + \
        "removed successfully." == data


def test_remove_users_unauthorized():
    """
    Test the get protected admin endpoint /protected/admin/ without token
    """
    response = client.delete(
        f"/api/{API_VERSION}/{API_NAME}/admin/users/remove/removal"
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_remove_non_existent_user():
    """
    Test the get protected admin endpoint 
    /protected/admin/ with non existent user
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
        f"/api/{API_VERSION}/{API_NAME}/admin/users/remove/non_existent_user",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "User non_existent_user " + \
        "not found." == data


def test_create_users():
    """
    Test the get protected admin endpoint /protected/admin/
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
        f"/api/{API_VERSION}/{API_NAME}/admin/users/create/",
        headers=headers,
        json={
            "username": "new_user",
            "password": "123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User new_user created successfully." == data


def test_create_users_unauthorized():
    """
    Test the get protected admin endpoint /protected/admin/ without token
    """
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/users/create/",
        json={
            "username": "new_user",
            "password": "123"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"


def test_create_users_already_exists():
    """
    Test the get protected admin endpoint 
    /protected/admin/ with already existing user
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
        f"/api/{API_VERSION}/{API_NAME}/admin/users/create/",
        headers=headers,
        json={
            "username": "new_user",
            "password": "123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "User new_user created successfully." == data
    response = client.put(
        f"/api/{API_VERSION}/{API_NAME}/admin/users/create/",
        headers=headers,
        json={
            "username": "new_user",
            "password": "123"
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert "Username already exists" == data["detail"]
