"""
Factory class to create and manage instances of different classes
"""
from app.adapters.db import Database
from app.adapters.user_repository import UserRepository
from app.adapters.user_service import UserService
from app.config.db import RedisDatabase
from app.config.env import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,
    REDIS_USERS_HOST, REDIS_USERS_PORT, REDIS_USERS_PASSWORD
)
from app.repositories.user_repository import UserRepositoryRedis
from app.services.user_service import UserServiceImpl

class ObjectFactory:
    """
    Factory class to create and manage instances of different classes
    """
    _instances = {}
    
    USERS_DATABASE = "UsersDatabase"
    MOM_DATABASE = "MomDatabase"

    @staticmethod
    def get_instance(interface: type, db_type: str = None) -> object:
        """
        Get an instance of the specified interface
        
        Args:
            interface (type): The interface class to get an instance of
        Returns:
            object: An instance of the specified interface
        """
        key = (interface, db_type) if db_type else interface
        
        # Check if the instance already exists for Singleton pattern
        if key in ObjectFactory._instances:
            return ObjectFactory._instances[key]

        # Create a new instance if it doesn't exist
        if interface == Database:
            if db_type == ObjectFactory.USERS_DATABASE:
                instance = RedisDatabase(
                    host=REDIS_USERS_HOST,
                    port=REDIS_USERS_PORT,
                    password=REDIS_USERS_PASSWORD
                )
            else:
                instance = RedisDatabase(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD
                )
            ObjectFactory._instances[key] = instance
            return instance
        if interface == UserRepository:
            db_instance = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
            instance = UserRepositoryRedis(db=db_instance)
            ObjectFactory._instances[key] = instance
            return instance
        if interface == UserService:
            user_repository = ObjectFactory.get_instance(UserRepository)
            instance = UserServiceImpl(user_repository=user_repository)
            ObjectFactory._instances[key] = instance
            return instance
        else:
            raise ValueError(f"Unknown interface: {key}")
