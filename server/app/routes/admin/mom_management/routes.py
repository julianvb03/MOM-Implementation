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
from app.dtos.mom_dto import QueueTopicResponse
from app.dtos.admin.mom_management_dto import QueueTopic, MomType
from app.utils.exceptions import raise_exception
from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from slowapi.errors import RateLimitExceeded


router = APIRouter()


@router.put("/queue_topic/create/",
            tags=["Admin", "Admin Mom Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to create a topic or " \
                + "queue in the message broker.",
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
@limiter.limit("15/minute")
def create_queue_topic(
    request: Request,
    queue_topic: QueueTopic,
    auth: dict = Depends(auth_handler.authenticate_as_admin),
    db_manager: Database = Depends(
        lambda: ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    ),
): # pylint: disable=W0613
    """
    Endpoint to create a topic or queue in the message broker.
    
    Args:
        queue_topic (QueueTopic): Queue or topic to be created.
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
        success: bool = False
        message: str = ""
        details: str = ""

        if queue_topic.type == MomType.QUEUE:
            manager = MOMQueueManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.create_queue(queue_name=queue_topic.name)
            success = result.success
            message = result.details
            details = result.status.value
        else:
            manager = MOMTopicManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.create_topic(topic_name=queue_topic.name)
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


@router.delete("/queue_topic/delete/{name}",
            tags=["Admin", "Admin Mom Management"],
            status_code=status.HTTP_200_OK,
            summary="Endpoint to delete a topic " \
                + "or queue in the message broker.",
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
@limiter.limit("15/minute")
def delete_queue_topic(
    request: Request,
    name: str,
    mom_type: MomType = Query(
        ...,
        description="Type of the queue or topic to delete",
        examples="queue"
    ),
    auth: dict = Depends(auth_handler.authenticate_as_admin),
    db_manager: Database = Depends(
        lambda: ObjectFactory.get_instance(Database, ObjectFactory.MOM_DATABASE)
    ),
): # pylint: disable=W0613
    """
    Endpoint to delete a topic or queue in the message broker.
    
    Args:
        name (str): Name of the queue or topic to be deleted.
        type (MomType): Type of the queue or topic to be deleted.
        auth (dict): Authenticated user information.
    Returns:
        (str): Success message or error message.
    """
    try:
        queue_topic = QueueTopic(name=name, type=mom_type)
        logger.info(
            "%s removal attempt for %s.",
            "Queue" if queue_topic.type.value == "queue" else "Topic",
            queue_topic.name
        )

        success: bool = False
        message: str = ""
        details: str = ""

        if queue_topic.type == MomType.QUEUE:
            manager = MOMQueueManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.delete_queue(queue_name=queue_topic.name)
            success = result.success
            message = result.details
            details = result.status.value
        else:
            manager = MOMTopicManager(
                redis_connection=db_manager.get_client(), user=auth["username"]
            )
            result = manager.delete_topic(topic_name=queue_topic.name)
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
