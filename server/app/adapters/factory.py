"""
Factory class to create and manage instances of different classes
"""
from app.adapters.db import Database
from app.adapters.user_repository import UserRepository
from app.adapters.user_service import UserService
from app.config.db import RedisDatabase
from app.config.env import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from app.repositories.user_repository import UserRepositoryRedis
from app.services.user_service import UserServiceImpl

class ObjectFactory:
    """
    Factory class to create and manage instances of different classes
    """
    _instances = {}

    @staticmethod
    def get_instance(interface: type) -> object:
        """
        Get an instance of the specified interface
        """
        # Check if the instance already exists for Singleton pattern
        if interface in ObjectFactory._instances:
            return ObjectFactory._instances[interface]

        # Create a new instance if it doesn't exist
        if interface == Database:
            instance = RedisDatabase(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD
            )
            ObjectFactory._instances[interface] = instance
            return instance
        if interface == UserRepository:
            db_instance = ObjectFactory.get_instance(Database)
            instance = UserRepositoryRedis(db=db_instance)
            ObjectFactory._instances[interface] = instance
            return instance
        if interface == UserService:
            user_repository = ObjectFactory.get_instance(UserRepository)
            instance = UserServiceImpl(user_repository=user_repository)
            ObjectFactory._instances[interface] = instance
            return instance
        else:
            raise ValueError(f"Unknown interface: {interface}")
