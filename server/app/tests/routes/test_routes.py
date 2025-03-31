"""
Test the home routes
"""
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
    # Initialize the database before each test
    initialize_database()


def test_home():
    """
    Test the home get endpoint or the root get endpoint /
    """
    response = client.get(f"/api/{API_VERSION}/{API_NAME}/")
    assert response.status_code == 200
    data = response.json()
    assert data == "Welcome to MOM TET API!"


def test_login():
    """
    Test the post login endpoint /login/
    """
    response = client.post(f"/api/{API_VERSION}/{API_NAME}/login/", json={
        "username": DEFAULT_USER_NAME,
        "password": DEFAULT_USER_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "Bearer"


def test_protected():
    """
    Test the get protected endpoint /protected/
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
    response = client.get(
        f"/api/{API_VERSION}/{API_NAME}/protected/",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "This is a protected endpoint" + \
        f". Welcome, {DEFAULT_USER_NAME}!" == data

def test_protected_unauthorized():
    """
    Test the get protected endpoint /protected/ without token
    """
    response = client.get(f"/api/{API_VERSION}/{API_NAME}/protected/")
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Not authenticated"
