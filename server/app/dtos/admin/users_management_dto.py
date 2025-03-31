"""
User Management dtos for the application.
"""
from pydantic import BaseModel, Field

class RemoveUserDto(BaseModel):
    """
    User dto for user removal.
    
    Attributes:
        username (str): Unique identifier for the user.
    """
    username: str = Field(
        ...,
        description="Unique identifier for the user",
        min_length=5,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        json_schema_extra={"example": "john_doe"}
    )
