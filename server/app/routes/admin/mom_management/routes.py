"""
This module defines the admin mom management endpoints of the API.
"""
from app.auth.auth import auth_handler
from app.config.limiter import limiter
from app.config.logging import logger
from app.dtos.general_dtos import ResponseError
from app.dtos.admin.mom_management_dto import CreateQueueTopic
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.put("/queue_topic/create/",
            tags=["Admin", "Admin Mom Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to create a topic or " \
                + "queue in the message broker.",
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
def create_queue_topic(
    request: Request,
    queue_topic: CreateQueueTopic,
    auth: dict = Depends(auth_handler.authenticate_as_admin)
): # pylint: disable=W0613
    """
    Endpoint to create a topic or queue in the message broker.
    
    Args:
        queue_topic (CreateQueueTopic): Queue or topic to be created.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info(
            "%s creation attempt for %s.",
            "Queue" if queue_topic.type.value == "queue" else "Topic",
            queue_topic.name
        )

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.

        # pylint: disable=inconsistent-quotes
        return f"{'Queue' if queue_topic.type.value == 'queue' else 'Topic'} " \
            + f"{queue_topic.name} created successfully."
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


@router.delete("/queue_topic/delete/{name}",
            tags=["Admin", "Admin Mom Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to delete a topic " \
                + "or queue in the message broker.",
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
def delete_queue_topic(
    request: Request,
    name: str,
    auth: dict = Depends(auth_handler.authenticate_as_admin)
): # pylint: disable=W0613
    """
    Endpoint to delete a topic or queue in the message broker.
    
    Args:
        name (str): Name of the queue or topic to be deleted.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info(
            "Queue/Topic removal attempt for %s.",
        )

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return "Queue/Topic " \
            + f"{name} removed successfully."
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
