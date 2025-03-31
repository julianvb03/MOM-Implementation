"""
Mom Management dtos for the application.
"""
from pydantic import BaseModel, Field
from enum import Enum

class MomType(str, Enum):
    """Allowed user roles"""
    QUEUE = "queue"
    TOPIC = "topic"


class QueueTopic(BaseModel):
    """
    QueueTopic dto for creating a new queue or topic.
    
    Attributes:
        name (str): Unique identifier for the queue or topic.
    """
    name: str = Field(
        ...,
        description="Unique identifier for the queue or topic",
        pattern=r"^[a-zA-Z0-9_-]+$",
        json_schema_extra={"example": "my_queue"}
    )


class CreateQueueTopic(QueueTopic):
    """
    QueueTopic dto for creating a new queue or topic.
    
    Attributes:
        name (str): Unique identifier for the queue or topic.
        type (MomType): Type of the queue or topic.
    """
    type: MomType = Field(
        ...,
        description="Type of the queue or topic",
        json_schema_extra={"example": "queue"}
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.type not in MomType:
            raise ValueError(
                f"Invalid type: {self.type}. Must be one of {list(MomType)}"
            )
