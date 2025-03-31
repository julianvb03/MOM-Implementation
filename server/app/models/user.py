"""
User model for the application.
"""
from pydantic import BaseModel, Field, field_validator, field_serializer
from enum import Enum
from typing import List


class UserRole(str, Enum):
    """Allowed user roles"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model for the application.
    
    Attributes:
        username (str): Unique identifier for the user.
        hashed_password (str): Hashed version of the user's password.
        roles (list[str]): 
            List of roles assigned to the user. Defaults to ["user"].
    """
    username: str = Field(
        ...,
        description="Unique identifier for the user",
        min_length=5,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        json_schema_extra={"example": "john_doe"}
    )
    hashed_password: str = Field(
        ...,
        description="BCrypt hashed password",
        json_schema_extra={
            "example": "EixZaYVK1fsbw1ZfbX3OXePaWxn96pWQoeG6Lruj3vjPVgaYlJG"
        }
    )
    roles: List[UserRole] = Field(
        default_factory=lambda: [UserRole.USER],
        description="List of roles assigned to the user"
    )

    @field_serializer("roles")
    def serialize_roles(self, roles: List[UserRole]) -> List[str]:
        return [role.value for role in roles]

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: List[UserRole]) -> List[UserRole]:
        """Ensure at least one role is assigned"""
        if not v:
            raise ValueError("User must have at least one role")
        return v
