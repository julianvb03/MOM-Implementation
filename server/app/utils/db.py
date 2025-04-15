"""
This module contains utility functions for database operations.
It includes a function to initialize the database with default values.
"""
from app.auth.auth import auth_handler
from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
from app.config.env import DEFAULT_USER_PASSWORD, DEFAULT_USER_NAME, WHOAMI
from app.dtos.admin.mom_management_dto import QueueTopic
from app.exceptions.database_exceptions import DatabaseConnectionError
from app.models.user import User, UserRole
from typing import List


def initialize_database():
    """
    Initializes the database with default values.
    This function checks if the default admin user exists in the database.
    If not, it creates the admin user with a hashed password.
    It also sets some initial configurations for Redis.
    """
    db = ObjectFactory.get_instance(Database, ObjectFactory.USERS_DATABASE)
    client = db.get_client()
    if not client:
        raise DatabaseConnectionError("Database client not initialized")

    admin_user = client.hget("users", DEFAULT_USER_NAME)
    if not admin_user:
        hashed_password = auth_handler.hash_password(DEFAULT_USER_PASSWORD)
        admin = User(
            username=DEFAULT_USER_NAME,
            hashed_password=hashed_password,
            roles=[UserRole.ADMIN]
        )
        client.hset("users", DEFAULT_USER_NAME, admin.model_dump_json())
        print(f"Created default user: {DEFAULT_USER_NAME}")

    # Set Redis configurations
    client.config_set("maxmemory", "256mb")
    client.config_set("maxmemory-policy", "allkeys-lru")
    

def get_elements_from_db() -> List[QueueTopic]:
    """
    Function to get all the elements from the database.
    """
    db = ObjectFactory.get_instance(Database, ObjectFactory.NODES_DATABASE)
    client = db.get_client()
    if not client:
        raise DatabaseConnectionError("Database client not initialized")

    keys = client.lrange(WHOAMI)
    elements = []
    for key in keys:
        name = key.decode().split(":")[2]
        type_ = key.decode().split(":")[1]
        elements.append(QueueTopic(name=name, type_=type_))
    return elements


def generate_keys(name: str, type_: str) -> List[str]:
    """
    Function to generate keys for the database based on the type and name.
    """
    base = f"mom:{type_}s:{name}"
    keys = [base]
    if type_ == "queue":
        keys += [
            f"{base}:metadata",
            f"{base}:subscribers"
        ]
    elif type_ == "topic":
        keys = [
            f"{base}:metadata",
            f"{base}:offsets",
            f"{base}:messages",
            f"{base}:subscribers"
        ]
    return keys


def backup_database(elements: List[QueueTopic]):
    """
    Backs up the database by copying the data from the backup database to the local database.
    
    Args:
        elements (List[QueueTopic]): A list of QueueTopic objects to be backed up.
    """
    db = ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    backup_db = ObjectFactory.get_instance(Database, ObjectFactory.BACK_UP_DATABASE)

    client = db.get_client()
    backup_client = backup_db.get_client()

    if not client or not backup_client:
        raise DatabaseConnectionError("Database client not initialized")

    for element in elements:
        keys = generate_keys(element.name, element.type.value)
        for key in keys:
            data_type = backup_client.type(key)
            if data_type == "none":
                continue
            
            if data_type == "string":
                value = backup_client.get(key)
                client.set(key, value)
            if data_type == "hash":
                data = backup_client.hgetall(key)
                client.hmset(key, data)
            elif data_type == "list":
                data = backup_client.lrange(key, 0, -1)
                client.rpush(key, *data)
            elif data_type == "set":
                data = backup_client.smembers(key)
                client.sadd(key, *data)
            elif data_type == "zset":
                data = backup_client.zrange(key, 0, -1, withscores=True)
                client.zadd(key, {k: v for k, v in data})
