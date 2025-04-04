"""
This module provides a service for managing subscriptions to message queues,
including subscribing and unsubscribing users to/from queues,
this way isolating the subscription logic from the queue management logic.
"""

from models import QueueOperationResult, MOMQueueStatus
from logger_config import logger
from utils import KeyBuilder
from queues.queues_validator import QueueValidator


class SubscriptionService:
    """
    This class handles the subscription management for message queues,
    including subscribing and unsubscribing users to/from queues.
    """
    def __init__(self, redis, user: str):
        self.redis = redis
        self.user = user
        self.validator = QueueValidator(redis, user)

    def subscribe(self, queue_name: str) -> QueueOperationResult:
        """
        Subscribe the user to a queue.
        Args:
            queue_name (str): The name of the queue to subscribe to.
        Returns:
            QueueOperationResult: Result of the subscription operation.
        """
        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is True:
                return result

            subscribers_key = KeyBuilder.subscribers_key(queue_name)
            self.redis.sadd(subscribers_key, self.user)

            return QueueOperationResult(
                True,
                MOMQueueStatus.SUCCES_OPERATION,
                f"User {self.user} subscribed to {queue_name}",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error subscribing to queue '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def unsubscribe(self, queue_name: str) -> QueueOperationResult:
        """
        Unsubscribe the user from a queue.
        Args:
            queue_name (str): The name of the queue to unsubscribe from.
        Returns:
            QueueOperationResult: Result of the unsubscription operation.
        """
        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            result = self.validator.validate_user_is_owner(queue_name)
            if result.success is True:
                result.details = (
                    "User is the owner of the queue and cannot unsubscribe"
                )
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is False:
                return result

            subscribers_key = KeyBuilder.subscribers_key(queue_name)
            self.redis.srem(subscribers_key, self.user)

            return QueueOperationResult(
                True,
                MOMQueueStatus.SUCCES_OPERATION,
                f"User {self.user} unsubscribed from {queue_name}",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error unsubscribing from queue '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )
