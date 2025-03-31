"""
Test cases for the UserService class
"""

from app.adapters.user_service import UserService
from app.adapters.user_repository import UserRepository
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.auth.auth import auth_handler
from app.dtos.user_dto import UserDto
from app.models.user import UserRole
import pytest


# Erase Redis data before each test
@pytest.fixture(autouse=True)
async def clear_redis():
    db = ObjectFactory.get_instance(Database)

    client = db.get_client()
    client.flushdb()
    yield
    # Cleanup after tests
    client.flushdb()


@pytest.fixture(name="user_service")
def user_serv_fixture():
    """
    Fixture to provide an instance of UserServiceImpl.
    """
    return ObjectFactory.get_instance(UserService)


@pytest.fixture(name="user_repository")
def user_repo_fixture():
    """
    Fixture to provide an instance of UserRepositoryRedis.
    """
    return ObjectFactory.get_instance(UserRepository)


def test_create_user(user_service, user_repository):
    # Test valid user creation
    test_user = UserDto(
        username="testuser0",
        password="123"
    )

    created_user = user_service.create_user(test_user)
    assert created_user is not None
    assert created_user.username == "testuser0"
    assert created_user.hashed_password is not None
    assert UserRole.USER in created_user.roles

    # Verify user exists in Redis
    stored_user = user_repository.get_user("testuser0")
    assert stored_user == created_user


def test_login(user_service):
    # Test valid login
    test_user = UserDto(
        username="testuser1",
        password="123"
    )

    user_service.create_user(test_user)

    token = user_service.login(test_user)
    assert token is not None

    # Verify the token contains the correct username
    payload = auth_handler.decode_token(token)
    assert payload["username"] == "testuser1"
    assert UserRole.USER in payload["roles"]


def test_login_invalid_user(user_service):
    # Test invalid login
    test_user = UserDto(
        username="invaliduser",
        password="wrongpass"
    )

    with pytest.raises(ValueError) as exc_info:
        user_service.login(test_user)

    assert "Invalid username or password" in str(exc_info.value)


def test_remove_user(user_service, user_repository):
    # Test user removal
    test_user = UserDto(
        username="testuser2",
        password="123"
    )

    user_service.create_user(test_user)

    assert user_repository.get_user("testuser2") is not None

    assert user_service.remove_user("testuser2")

    assert user_repository.get_user("testuser2") is None


def test_remove_nonexistent_user(user_service):
    # Test removal of a non-existent user
    assert not user_service.remove_user("nonexistentuser")
