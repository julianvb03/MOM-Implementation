"""
This module defines the root endpoints of the API.
"""
from app.adapters.factory import ObjectFactory
from app.adapters.user_service import UserService
from app.auth.auth import auth_handler
from app.config.limiter import limiter
from app.config.logging import logger
from app.dtos.general_dtos import ResponseError
from app.dtos.user_dto import UserDto, UserLoginResponse
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.get("/",
            tags=["Root"],
            status_code=status.HTTP_200_OK,
            summary="Root endpoint.",
            response_model=str,
            responses={
                500: {
                    "model": ResponseError, 
                    "description": "Internal server error."
                },
                429: {
                    "model": ResponseError, 
                    "description": "Too many requests."
                }
            })
@limiter.limit("15/minute")
def root(request: Request): # pylint: disable=W0613
    """
    Root endpoint.

    Returns:
        (str): Welcome message.
    """
    try:
        logger.info("Root endpoint.")
        return "Welcome to MOM TET API!"
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)


@router.post("/login/",
                tags=["Authentication"],
                status_code=status.HTTP_200_OK,
                summary="User login.",
                response_model=UserLoginResponse,
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
@limiter.limit("100/minute")
def login(
    request: Request,
    user: UserDto,
    user_service: UserService = Depends(
        lambda: ObjectFactory.get_instance(UserService)
    )
): # pylint: disable=W0613
    """
    User login endpoint.

    Args:
        user (UserLogin): User credentials.

    Returns:
        (UserLoginResponse): JWT token.

    Raises:
        HTTPException: If the user is not found or the password is incorrect.
    """
    try:
        logger.info("User login attempt for %s.", user.username)


        token = user_service.login(user=user)

        return UserLoginResponse(access_token=token, token_type="Bearer")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except ValueError as e:
        logger.error("User login attempt for %s.", user.username)
        raise HTTPException(
            status_code=401,
            detail=str(e)
        ) from e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)


@router.get("/protected/",
            tags=["Protected"],
            status_code=status.HTTP_200_OK,
            summary="Protected endpoint to test authentication.",
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
@limiter.limit("5/minute")
def protected(
    request: Request,
    auth: dict = Depends(auth_handler.authenticate)
): # pylint: disable=W0613
    """
    Root endpoint.

    Returns:
        (str): Welcome message.
    """
    try:
        logger.info("Protected endpoint.")
        # pylint: disable=inconsistent-quotes
        return f"This is a protected endpoint. Welcome, {auth['username']}!"
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        ) from e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)


@router.get("/admin/protected/",
            tags=["Protected"],
            status_code=status.HTTP_200_OK,
            summary="Protected endpoint to test admin authentication.",
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
@limiter.limit("5/minute")
def protected_admin(
    request: Request,
    auth: dict = Depends(auth_handler.authenticate_as_admin)
): # pylint: disable=W0613
    """
    Root endpoint.

    Returns:
        (str): Welcome message.
    """
    try:
        logger.info("Protected endpoint.")
        # pylint: disable=inconsistent-quotes
        return "This is the protected admin endpoint" \
            + f". Welcome, {auth['username']}!"
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail="Too many requests."
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        ) from e
    except HTTPException as e:
        raise e
    except Exception as e: # pylint: disable=W0718
        raise_exception(e, logger)
