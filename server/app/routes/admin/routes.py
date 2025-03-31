"""
This module defines the admin endpoints of the API.
"""
from app.adapters.factory import ObjectFactory
from app.adapters.user_service import UserService
from app.auth.auth import auth_handler
from app.config.limiter import limiter
from app.config.logging import logger
from app.dtos.general_dtos import ResponseError
from app.dtos.user_dto import UserDto
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.delete("/users/remove/{user}",
            tags=["Admin", "Admin User Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to remove the specified user.",
            response_model=str,
            responses={
                500: {
                    "model": ResponseError, 
                    "description": "Internal server error."
                },
                429: {
                    "model": ResponseError, 
                    "description": "Too many requests."
                },
                401: {
                    "model": ResponseError,
                    "description": "Unauthorized."
                },
                403: {
                    "model": ResponseError,
                    "description": "Forbidden."
                }
            })
@limiter.limit("15/minute")
def remove_users(
    request: Request,
    user: str,
    user_service: UserService = Depends(
        lambda: ObjectFactory.get_instance(UserService)
    ),
    auth: dict = Depends(auth_handler.authenticate_as_admin)
): # pylint: disable=W0613
    """
    Endpoint to remove the specified user.
    
    Args:
        user (RemoveUserDto): User to be removed.
        auth (dict): Authenticated user information.

    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info("User removal attempt for %s.", user)

        if user_service.remove_user(user):
            return f"User {user} removed successfully."
        else:
            return f"User {user} not found."
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        ) from e
    except HTTPException as e:
        raise e
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)


@router.put("/users/create/",
            tags=["Admin", "Admin User Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to create the specified user.",
            response_model=str,
            responses={
                500: {
                    "model": ResponseError, 
                    "description": "Internal server error."
                },
                429: {
                    "model": ResponseError, 
                    "description": "Too many requests."
                },
                401: {
                    "model": ResponseError,
                    "description": "Unauthorized."
                },
                403: {
                    "model": ResponseError,
                    "description": "Forbidden."
                }
            })
@limiter.limit("15/minute")
def create_users(
    request: Request,
    user: UserDto,
    user_service: UserService = Depends(
        lambda: ObjectFactory.get_instance(UserService)
    ),
    auth: dict = Depends(auth_handler.authenticate_as_admin)
): # pylint: disable=W0613
    """
    Endpoint to create the specified user.
    
    Args:
        user (RemoveUserDto): User to be created.
        auth (dict): Authenticated user information.

    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info("User creation attempt for %s.", user.username)

        if user_service.create_user(user):
            return f"User {user.username} created successfully."
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        ) from e
    except HTTPException as e:
        raise e
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)
