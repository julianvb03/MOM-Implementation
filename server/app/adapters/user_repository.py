"""Database Adapter Interface"""
from abc import ABC, abstractmethod
from app.models.user import User
from typing import Optional


class UserRepository(ABC):
    """
    Abstract base class for user repositories.
    This class defines the interface for database operations.
    """

    @abstractmethod
    def create_user(self, user: User) -> User:
        pass

    @abstractmethod
    def get_user(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        pass
