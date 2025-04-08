"""
Custom exceptions for database operations.
These exceptions are used to handle specific error cases
related to database interactions.
"""
class DatabaseConnectionError(Exception):
    """Exception raised when a database connection fails."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
