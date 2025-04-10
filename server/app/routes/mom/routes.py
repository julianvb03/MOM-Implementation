"""
This module defines the admin mom management endpoints of the API.
"""
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database
from app.auth.auth import auth_handler
from app.config.limiter import limiter
from app.config.logging import logger
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.topics.topics_manager import MOMTopicManager
from app.dtos.general_dtos import ResponseError
from app.dtos.admin.mom_management_dto import MomType
from app.dtos.mom_dto import QueueTopic, MessageQueueTopic, QueueTopicResponse
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.post("/subscribe/",
            tags=["Mom"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint for a user to subscribe to a topic or queue.",
            response_model=QueueTopicResponse,
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
@limiter.limit("200/minute")
def subscribe(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate),
    db_manager: Database = Depends(
        lambda: ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    ),
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
        queue_topic_type = "Queue" if (
            queue_topic.type.value == "queue"
        ) else "Topic"
        logger.info(
            "%s attempting to subscribe to %s %s.",
            auth["username"],
            queue_topic_type,
            queue_topic.name,
        )
        success: bool = False
        message: str = ""
        details: str = ""

        if queue_topic.type == MomType.QUEUE:
            manager = MOMQueueManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.subscriptions.subscribe(
                queue_name=queue_topic.name
            )
            success = result.success
            message = result.details
            details = result.status.value
        else:
            manager = MOMTopicManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.subscriptions.subscribe(
                topic_name=queue_topic.name
            )
            success = result.success
            message = result.details
            details = result.status.value

        logger.info(details)

        return QueueTopicResponse(
            success=success,
            message=message
        )
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
            response_model=QueueTopicResponse,
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
@limiter.limit("200/minute")
def unsubscribe(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate),
    db_manager: Database = Depends(
        lambda: ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    ),
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
        queue_topic_type = "Queue" if (
            queue_topic.type.value == "queue"
        ) else "Topic"
        logger.info(
            "%s attempting to unsubscribe to %s %s.",
            auth["username"],
            queue_topic_type,
            queue_topic.name,
        )
        success: bool = False
        message: str = ""
        details: str = ""

        if queue_topic.type == MomType.QUEUE:
            manager = MOMQueueManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.subscriptions.unsubscribe(
                queue_name=queue_topic.name
            )
            success = result.success
            message = result.details
            details = result.status.value
        else:
            manager = MOMTopicManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.subscriptions.unsubscribe(
                topic_name=queue_topic.name
            )
            success = result.success
            message = result.details
            details = result.status.value

        logger.info(details)
        return QueueTopicResponse(
            success=success,
            message=message
        )
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
            response_model=QueueTopicResponse,
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
    auth: dict = Depends(auth_handler.authenticate),
    db_manager: Database = Depends(
        lambda: ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    ),
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
        queue_topic_type = "Queue" if (
            message_queue_topic.type.value == "queue"
        ) else "Topic"
        logger.info(
            "%s attempting to publish a message to %s %s.",
            auth["username"],
            queue_topic_type,
            message_queue_topic.name,
        )
        success: bool = False
        message: str = ""
        details: str = ""

        if message_queue_topic.type == MomType.QUEUE:
            manager = MOMQueueManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.enqueue(
                queue_name=message_queue_topic.name,
                message=message_queue_topic.message
            )
            success = result.success
            message = result.details
            details = result.status.value
        else:
            manager = MOMTopicManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.publish(
                topic_name=message_queue_topic.name,
                message=message_queue_topic.message
            )
            success = result.success
            message = result.details
            details = result.status.value

        logger.info(details)
        return QueueTopicResponse(
            success=success,
            message=message
        )
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
        queue_topic_type = "Queue" if (
            queue_topic.type.value == "queue"
        ) else "Topic"
        logger.info(
            "%s attempting to receive a message from %s %s.",
            auth["username"],
            queue_topic_type,
            queue_topic.name,
        )

        # TODO: Implement the logic to create a
        # queue or topic in the message broker.
        # This is a placeholder implementation.
        return f"'message' received by {auth["username"]} from " \
            + f"{queue_topic_type} {queue_topic.name} successfully."
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
