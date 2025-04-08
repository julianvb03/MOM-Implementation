"""
Test cases for the UserRepository class.
"""
from app.models.user import User, UserRole
from app.adapters.user_repository import UserRepository
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
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


@pytest.fixture(name="user_repository")
def user_repo_fixture():
    """
    Fixture to provide an instance of UserRepositoryRedis.
    """
    return ObjectFactory.get_instance(UserRepository)


def test_create_user(user_repository):
    # Test valid user creation
    test_user = User(
        username="testuser",
        hashed_password="hashedpass123",
        roles=[UserRole.USER]
    )

    created_user = user_repository.create_user(test_user)
    assert created_user == test_user

    # Verify user exists in Redis
    stored_user = user_repository.get_user("testuser")
    assert stored_user == test_user


def test_get_nonexistent_user(user_repository):
    result = user_repository.get_user("nonexistent")
    assert result is None


def test_delete_user(user_repository):
    test_user = User(
        username="todelete",
        hashed_password="hashed",
        roles=[UserRole.USER]
    )

    user_repository.create_user(test_user)
    assert user_repository.delete_user("todelete") is True

    # Verify deletion
    assert user_repository.get_user("todelete") is None


def test_delete_nonexistent_user(user_repository):
    assert user_repository.delete_user("ghostuser") is False


def test_user_serialization_roundtrip(user_repository):
    original_user = User(
        username="serialtest",
        hashed_password="hashed123",
        roles=[UserRole.ADMIN, UserRole.USER]
    )

    user_repository.create_user(original_user)
    retrieved_user = user_repository.get_user("serialtest")

    assert retrieved_user == original_user
    assert retrieved_user.model_dump() == original_user.model_dump()
