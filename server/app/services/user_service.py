"""
User Service Module
This module provides services related to user operations.
It includes functions to create users, get user details,
and delete users.
"""
from app.adapters.user_repository import UserRepository
from app.adapters.user_service import UserService
from app.auth.auth import auth_handler
from app.dtos.user_dto import UserDto
from app.models.user import User, UserRole

class UserServiceImpl(UserService):
    """
    UserService class to handle user-related operations.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user: UserDto) -> User:
        """
        Create a new user in the system.

        Args:
            user (User): User object containing username and password.

        Returns:
            User: Created user object.
        """

        if self.user_repository.user_exists(user.username):
            raise ValueError("Username already exists")

        return self.user_repository.create_user(User(
            username=user.username,
            hashed_password=auth_handler.hash_password(user.password),
            roles=[UserRole.USER]
        ))

    def login(self, user: UserDto) -> str:
        """
        Authenticate a user.

        Args:
            user (UserDto): User DTO object containing username and password.

        Returns:
            str: JWT token for the authenticated user.
        """
        db_user = self.user_repository.get_user(user.username)

        if db_user is None or not auth_handler.verify_password(
            user.password,
            db_user.hashed_password
        ):
            raise ValueError("Invalid username or password")

        token = auth_handler.create_token({
            "username": db_user.username,
            "roles": db_user.serialize_roles(db_user.roles)
        })

        return token

    def remove_user(self, username: str) -> bool:
        """
        Delete a user from the system.

        Args:
            username (str): 
                Username of the user to be deleted from the JWT token.
        Returns:
            bool: True if user was deleted successfully, False otherwise.
        """
        return self.user_repository.delete_user(username)
