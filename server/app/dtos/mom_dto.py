"""
Mom Interaction dtos for the application.
"""
from app.dtos.admin.mom_management_dto import QueueTopic
from pydantic import Field


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
