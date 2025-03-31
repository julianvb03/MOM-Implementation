"""User Repository Module"""
from typing import Optional
from app.adapters.db import Database
from app.adapters.user_repository import UserRepository
from app.models.user import User


class UserRepositoryRedis(UserRepository):
    """
    Class to handle user-related operations in the database.
    """
    def __init__(self, db: Database):
        self.db = db
        self.client = None

    def initialize_db(self):
        """
        Initialize the repository by setting up the database client.
        """
        self.client = self.db.get_client()

    def create_user(self, user: User) -> User:
        """
        Create a new user with hashed password
        
        Args:
            user (User): User object containing username and password.
            
        Returns:
            User: Created user object.
        """
        if self.client is None:
            self.initialize_db()

        if self.client.hexists("users", user.username):
            raise ValueError("Username already exists")

        self.client.hset(
            "users", 
            user.username,
            user.model_dump_json()
        )
        return user

    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username (str): Username of the user to retrieve.
            
        Returns:
            User: User object if found, None otherwise.
        """
        if self.client is None:
            self.initialize_db()

        user_data = self.client.hget("users", username)
        if not user_data:
            return None
        return User.model_validate_json(user_data)

    def delete_user(self, username: str) -> bool:
        """
        Delete user by username
        """
        if self.client is None:
            self.initialize_db()

        deleted = self.client.hdel("users", username)
        if deleted == 0:
            return False
        return True
