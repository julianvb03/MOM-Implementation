"""
    This module defines the QueueOperationResult class and the
    QueueException class.
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

## Information about the replication of messages
NODE_A_IP = os.getenv("NODE_A_IP")
NODE_B_IP = os.getenv("NODE_B_IP")
NODE_C_IP = os.getenv("NODE_C_IP")
GRPC_PORT = os.getenv("GRPC_PORT")
WHOAMI = os.getenv("WHOAMI")

if NODE_A_IP is None or NODE_B_IP is None or NODE_C_IP is None:
    raise ValueError("Environment variables NODE_A_IP, NODE_B_IP, and NODE_C_IP must be set") # pylint: disable=C0301
if GRPC_PORT is None:
    raise ValueError("Environment variable GRPC_PORT must be set")
if WHOAMI is None:
    raise ValueError("Environment variable WHOAMI must be set")
if WHOAMI not in ["A", "B", "C"]:
    raise ValueError("Environment variable WHOAMI must be A, B or C")

NODES_CONFIG = {
    "A": {"ip": NODE_A_IP, "grpc_port": GRPC_PORT, "whoreplica": "C"},
    "B": {"ip": NODE_B_IP, "grpc_port": GRPC_PORT, "whoreplica": "A"},
    "C": {"ip": NODE_C_IP, "grpc_port": GRPC_PORT, "whoreplica": "B"},
}

class ReplicationStatus(Enum):
    """
    Enum for replication status messages.
    """
    REPLICATION_SUCCESS = 0
    REPLICATION_FAILED = 1
    REPLICATION_NOT_REQUIRED = 2
    INVALID_REPLICATION_STATUS = 3
    REPLICATE_NODE_DISCONNECTED = 4

class MOMQueueStatus(Enum):
    QUEUE_CREATED = "Queue and metadata created successfully"
    METADATA_EXISTS = "Metadata for the queue already exists"
    QUEUE_EXISTS = "Queue already exists"
    METADATA_OR_QUEUE_NOT_EXIST = "Queue or metadata not exist for a queue with that name" # pylint: disable=C0301
    INVALID_ARGUMENTS = "The parameters doesn't work on this context"
    INTERNAL_ERROR = "Unexpected error"
    SUCCES_OPERATION = "The operation was realized without problems"
    EMPTY_QUEUE = "The queue is empty"

@dataclass
class QueueOperationResult:
    success: bool
    status: MOMQueueStatus
    details: Optional[str] = None
    replication_result: bool = None

class QueueException(Exception):
    def __init__(self, status: MOMQueueStatus, message: str = ""):
        self.status = status
        super().__init__(message)

class MOMTopicStatus(Enum):
    """
    Enum for MOM topic status messages.
    """
    TOPIC_CREATED = "Topic and metadata created successfully"
    TOPIC_EXISTS = "Topic already exists"
    TOPIC_NOT_EXIST = "Topic does not exist"
    MESSAGE_PUBLISHED = "Message published to topic successfully"
    MESSAGE_CONSUMED = "Message consumed from topic successfully"
    NO_MESSAGES = "No messages available for this subscription"
    MESSAGES_CLEANED = "Messages cleaned successfully"
    ALREADY_SUBSCRIBED = "User is already subscribed to this topic"
    NOT_SUBSCRIBED = "User is not subscribed to this topic"
    SUBSCRIPTION_CREATED = "Subscription created successfully"
    SUBSCRIPTION_DELETED = "Subscription deleted successfully"
    INTERNAL_ERROR = "Internal error occurred"
    TOPIC_DELETED = "Topic deleted successfully"
    INVALID_ARGUMENTS = "Invalid arguments provided"
    INCONSISTENT_STATE = "Inconsistent state detected"
    REPLICATION_FAILED = "Replication failed"

@dataclass
class TopicOperationResult:
    success: bool
    status: MOMTopicStatus
    details: Optional[str] = None
    replication_result: bool = None

class TopicException(Exception):
    def __init__(self, status: MOMTopicStatus, message: str = ""):
        self.status = status
        super().__init__(message)
