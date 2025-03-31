"""
This module defines the admin mom management endpoints of the API.
"""
from app.auth.auth import auth_handler
from app.config.limiter import limiter
from app.config.logging import logger
from app.dtos.home_routing_dto import ResponseError
from app.dtos.mom_dto import QueueTopic, MessageQueueTopic
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.post("/subscribe/",
            tags=["Mom"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint for a user to subscribe to a topic or queue.",
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
@limiter.limit("20/minute")
def subscribe(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate)
): # pylint: disable=W0613
    """
    Endpoint to subscribe a user to a topic or
    queue in the message broker.
    
    Args:
        queue_topic (Queue): Queue or topic to be subscribed to.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info("Attempt to subscribe to %s.", queue_topic.name)

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return f"Subscribed to {queue_topic.name} successfully."
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


@router.post("/unsubscribe/",
            tags=["Mom"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint for a user to unsubscribe from a topic or queue.",
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
@limiter.limit("20/minute")
def unsubscribe(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate)
): # pylint: disable=W0613
    """
    Endpoint to unsubscribe a user from a topic or
    queue in the message broker.
    
    Args:
        queue_topic (Queue): Queue or topic to be unsubscribed from.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info("Attempt to unsubscribe of %s.", queue_topic.name)

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return f"Unsubscribed of {queue_topic.name} successfully."
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


@router.post("/send/",
            tags=["Mom"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint for a user to send" \
                + "a message to a topic or queue.",
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
@limiter.limit("20/minute")
def send_message(
    request: Request,
    message_queue_topic: MessageQueueTopic,
    auth: dict = Depends(auth_handler.authenticate)
): # pylint: disable=W0613
    """
    Endpoint to send a message to a topic or queue in the message broker.
    
    Args:
        message_queue_topic (MessageQueueTopic): Message to be sent.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info(
            "Attempt to publish a message to %s.",
            message_queue_topic.name
        )

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return f"'{message_queue_topic.message}' published to " \
            + f"{message_queue_topic.name} successfully."
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


@router.post("/receive/",
            tags=["Mom"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint for a user to receive" \
                + "a message from a topic or queue.",
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
@limiter.limit("20/minute")
def receive_message(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate)
): # pylint: disable=W0613
    """
    Endpoint to receive a message from a topic or queue in the message broker.
    
    Args:
        queue_topic (Queue): Queue or topic to receive messages from.
        auth (dict): Authenticated user information.
        
    Returns:
        (str): Success message or error message.
    """
    try:
        logger.info(
            "Attempt to receive a message from %s.",
            queue_topic.name
        )

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return "'message' received from " \
            + f"{queue_topic.name} successfully."
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
