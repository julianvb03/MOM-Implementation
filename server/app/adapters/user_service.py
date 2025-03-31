"""Database Adapter Interface"""
from abc import ABC, abstractmethod
from app.models.user import User
from app.dtos.user_dto import UserDto


class UserService(ABC):
    """
    Abstract base class for user services.
    This class defines the interface for user-related operations.
    """

    @abstractmethod
    def create_user(self, user: UserDto) -> User:
        pass

    @abstractmethod
    def login(self, user: UserDto) -> str:
        pass

    @abstractmethod
    def remove_user(self, username: str) -> bool:
        pass
