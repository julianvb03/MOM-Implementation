"""
    This module defines the QueueOperationResult class and the 
    QueueException class.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict

class MOMQueueStatus(Enum):
    QUEUE_CREATED = "Queue and metadata created successfully"
    METADATA_EXISTS = "Metadata for the queue already exists"
    QUEUE_EXISTS = "Queue already exists"
    METADATA_OR_QUEUE_NOT_EXIST = "Queue or metadata not exist for a queue with that name"
    INVALID_ARGUMENTS = "The parameters doesn't work on this context"
    INTERNAL_ERROR = "Unexpected error"
    SUCCES_OPERATION = "The operation was realized without problems"
    EMPTY_QUEUE = "The queue is empty"

@dataclass
class QueueOperationResult:
    success: bool
    status: MOMQueueStatus
    details: Optional[str] = None

class QueueException(Exception):
    def __init__(self, status: MOMQueueStatus, message: str = ""):
        self.status = status
        super().__init__(message)

class MOMTopicStatus(Enum):
    TOPIC_CREATED = "Topic and metadata created successfully"
    TOPIC_EXISTS = "Topic already exists"
    TOPIC_NOT_EXIST = "Topic does not exist"
    MESSAGE_PUBLISHED = "Message published to topic successfully"
    NO_MESSAGES = "No messages available for this subscription"
    ALREADY_SUBSCRIBED = "User is already subscribed to this topic"
    NOT_SUBSCRIBED = "User is not subscribed to this topic"
    SUBSCRIPTION_CREATED = "Subscription created successfully"
    SUBSCRIPTION_DELETED = "Subscription deleted successfully"
    INTERNAL_ERROR = "Internal error occurred"
    INCONSISTENT_STATE = "Inconsistent state detected"

@dataclass
class TopicOperationResult:
    success: bool
    status: MOMTopicStatus
    details: Optional[Dict | str] = None


class TopicException(Exception):
    def __init__(self, status: MOMTopicStatus, message: str = ""):
        self.status = status
        super().__init__(message)