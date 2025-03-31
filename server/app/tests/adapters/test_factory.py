"""Test the db initialization"""
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.adapters.user_repository import UserRepository
from app.adapters.user_service import UserService
from app.config.db import RedisDatabase
from app.repositories.user_repository import UserRepositoryRedis
from app.services.user_service import UserServiceImpl


def test_redis_client():
    """Test that the Redis Database is created correctly."""
    db = ObjectFactory.get_instance(Database)

    assert isinstance(
        db,
        RedisDatabase
    ), "Database should be of type RedisDatabase"


def test_user_repository():
    """Test that the UserRepository is created correctly."""
    user_repo = ObjectFactory.get_instance(UserRepository)

    assert isinstance(
        user_repo,
        UserRepositoryRedis
    ), "UserRepository should be of type UserRepositoryRedis"


def test_user_service():
    """Test that the UserService is created correctly."""
    user_service = ObjectFactory.get_instance(UserService)

    assert isinstance(
        user_service,
        UserServiceImpl
    ), "UserService should be of type UserServiceImpl"
