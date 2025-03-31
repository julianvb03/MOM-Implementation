"""Database Adapter Interface"""
from abc import ABC, abstractmethod

class Database(ABC):
    """
    Abstract base class for database adapters.
    This class defines the interface for database operations.
    """

    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def close(self):
        pass
