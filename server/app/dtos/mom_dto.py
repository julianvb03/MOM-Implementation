"""
Mom Interaction dtos for the application.
"""
from app.dtos.admin.mom_management_dto import QueueTopic
from pydantic import BaseModel, Field


class MessageQueueTopic(QueueTopic):
    """
    QueueTopic dto for creating a new queue or topic.
    
    Attributes:
        name (str): Unique identifier for the queue or topic.
        message (str): Message to be sent to the queue or topic.
    """
    message: str = Field(
        ...,
        description="Message to be sent to the queue or topic",
        json_schema_extra={"example": "Hello, World!"}
    )


class QueueTopicResponse(BaseModel):
    """
    QueueTopic dto for answering a base action request to a queue or topic.
    
    Attributes:
        success (bool): Success status of the action.
        message (str): Message receive from the topic or queue,
        or success/error messages.
    """
    success: bool = Field(
        ...,
        description="Success status of the action",
        json_schema_extra={"example": True}
    )
    message: str = Field(
        ...,
        description="Message receive from the topic or queue," \
        + " or success/error messages",
        json_schema_extra={"example": "Queue test_queue created successfully."}
    )
