"""
This module contains the QueueValidator class, which is responsible
for validatin queue operations in a Redis-based message queue system,
isolating the validation logic for better maintainability and readability.
"""

from app.domain.utils import KeyBuilder
from app.domain.models import QueueOperationResult, MOMQueueStatus


class QueueValidator:
    """
    This class handles the validation of queue operations in a Redis-based
    """

    def __init__(self, redis, user):
        self.redis = redis
        self.user = user

    def validate_queue_exists(self, queue_name: str) -> QueueOperationResult:
        """
        Validate if the queue exists in Redis.
        Args:
            queue_name (str): The name of the queue to validate.
        Returns:
            QueueOperationResult: Result of the validation.

        """
        metadata_key = KeyBuilder.metadata_key(queue_name)
        if not self.redis.exists(metadata_key):
            return QueueOperationResult(
                False,
                MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST,
                "Queue does not exist",
            )

        return QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )

    def validate_user_subscribed(self, queue_name: str) -> QueueOperationResult:
        """
        Validate if the user is subscribed to the queue.
        Args:
            queue_name (str): The name of the queue to validate.
        Returns:
            QueueOperationResult: Result of the validation.
        """
        subscribers_key = KeyBuilder.subscribers_key(queue_name)
        if not self.redis.sismember(subscribers_key, self.user):
            return QueueOperationResult(
                False,
                MOMQueueStatus.INVALID_ARGUMENTS,
                "User is not subscribed",
            )

        return QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )

    def validate_user_is_owner(self, queue_name: str) -> QueueOperationResult:
        metadata_key = KeyBuilder.metadata_key(queue_name)
        owner = self.redis.hget(metadata_key, "owner")
        if owner and owner != self.user:
            return QueueOperationResult(
                False,
                MOMQueueStatus.INVALID_ARGUMENTS,
                "Operation not allowed for non-owner",
            )

        return QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is owner"
        )
