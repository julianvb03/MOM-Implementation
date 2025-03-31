from app.auth.auth import auth_handler
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.env import DEFAULT_USER_PASSWORD, DEFAULT_USER_NAME
from app.models.user import User, UserRole


def initialize_database():
    """
    Initializes the database with default values.
    This function checks if the default admin user exists in the database.
    If not, it creates the admin user with a hashed password.
    It also sets some initial configurations for Redis.
    """
    db = ObjectFactory.get_instance(Database)
    client = db.get_client()
    if not client:
        raise Exception("Database client not initialized")
    
    admin_user = client.hget("users", DEFAULT_USER_NAME)
    if not admin_user:
        hashed_password = auth_handler.hash_password(DEFAULT_USER_PASSWORD)
        admin = User(
            username=DEFAULT_USER_NAME,
            hashed_password=hashed_password,
            roles=[UserRole.ADMIN]
        )
        client.hset("users", DEFAULT_USER_NAME, admin.model_dump_json())
        
    # Set Redis configurations
    client.config_set("maxmemory", "256mb")
    client.config_set("maxmemory-policy", "allkeys-lru")
