"""
User model for the application.
"""
from pydantic import BaseModel, Field

class UserDto(BaseModel):
    """
    User dto for user interaction with the model.
    
    Attributes:
        username (str): Unique identifier for the user.
        password (str): User's password.
    """
    username: str = Field(
        ...,
        description="Unique identifier for the user",
        min_length=5,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        json_schema_extra={"example": "john_doe"}
    )
    password: str = Field(
        ...,
        description="Password",
        json_schema_extra={
            "example": "my_secure_password123*"
        },
    )


class UserLoginResponse(BaseModel):
    """
    Data model for user login operations.
    
    This model is used for user login responses. It contains the `access_token` attribute, which is a JWT token and the token type.

    Attributes:
        access_token (str): JWT token for user authentication.
        token_type (str): Type of token.
    """
    access_token: str = Field(description="JWT token for user authentication.")
    token_type: str = Field(description="Type of token.")
