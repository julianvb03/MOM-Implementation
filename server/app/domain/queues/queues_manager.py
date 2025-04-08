"""
This module provides a class for managing message queues using Redis,
including creating, deleting, enqueuing, and dequeuing messages.
"""

import json
import uuid
from datetime import datetime, timezone
from app.domain.models import MOMQueueStatus, QueueOperationResult
from app.domain.logger_config import logger
from app.domain.utils import KeyBuilder
from app.domain.queues.queues_subscription import SubscriptionService
from app.domain.queues.queues_validator import QueueValidator

class MOMQueueManager:
    """
    This class handles the management of message queues in a Redis database,
    including creating, deleting, enqueuing, and dequeuing messages,
    it uses the SubscriptionService and QueueValidator classes for managing 
    subscriptionsand validating queue operations.
    It also provides methods for getting queue information and checking the
    status of queues. The class is initialized with a Redis connection and a 
    user identifier.
    """

    def __init__(self, redis_connection, user: str):
        self.redis = redis_connection
        self.user = user
        self.subscriptions = SubscriptionService(self.redis, self.user)
        self.validator = QueueValidator(self.redis, user)

    def create_queue(
        self, queue_name: str, message_limit: int = 1000
    ) -> QueueOperationResult:
        """
        Create a new queue with the specified name and message limit.
        Args:
            queue_name (str): The name of the queue to create.
            message_limit (int): The maximum number of messages 
                allowed in the queue.
        Returns:
            QueueOperationResult: Result of the queue creation operation.
        """
        try:
            if not 1 <= message_limit <= (2**32 - 1):
                return QueueOperationResult(
                    False,
                    MOMQueueStatus.INVALID_ARGUMENTS,
                    "Message limit out of valid range",
                )

            queue_key = KeyBuilder.queue_key(queue_name)
            metadata_key = KeyBuilder.metadata_key(queue_name)

            result = self.validator.validate_queue_exists(queue_name)
            if result.success is True:
                return result

            metadata = {
                "name": queue_name,
                "owner": self.user,
                "created_at": datetime.now().isoformat(),
                "total_messages": 0,
            }

            self.redis.hset(metadata_key, mapping=metadata)
            # replicate data on ()
            result = self.subscriptions.subscribe(queue_name)

            if result.success is False:
                self.redis.delete(metadata_key, queue_key)
                return result

            return QueueOperationResult(
                True,
                MOMQueueStatus.QUEUE_CREATED,
                f"Queue {queue_name} created successfully",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Unexpected error creating queue '%s'", queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def enqueue(self, message: str, queue_name: str) -> QueueOperationResult:
        """
        Enqueue a message to the specified queue.
        Args:
            message (str): The message to enqueue.
            queue_name (str): The name of the queue to enqueue the message to.
        Returns:
            QueueOperationResult: Result of the enqueue operation.
        """
        try:
            queue_key = KeyBuilder.queue_key(queue_name)
            metadata_key = KeyBuilder.metadata_key(queue_name)

            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            # Se decidio que el usuario no debe estar subscrito para
            # encolar mensajes
            # result = self.validator.validate_user_subscribed(queue_name)
            # if result.success is False:
            #     return result

            message_id = str(uuid.uuid4())
            full_message = {
                "id": message_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": json.dumps(message),
            }
            self.redis.rpush(queue_key, json.dumps(full_message))
            self.redis.hincrby(metadata_key, "total_messages", 1)
            ## TO DO
            ## Garantizar la replicación de los mensajes

            return QueueOperationResult(
                True,
                MOMQueueStatus.SUCCES_OPERATION,
                "Message enqueued successfully",
            )
        except Exception as e: # pylint: disable=W0718
            logger.exception("Error dequeueing message to '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def dequeue(
        self, queue_name: str, block: bool = False, timeout: int = 0
    ) -> QueueOperationResult:
        """
        Dequeue a message from the specified queue.
        Args:
            queue_name (str): The name of the queue to dequeue from.
            block (bool): Whether to block until a message is available.
            timeout (int): Timeout for blocking dequeue.
        Returns:
            QueueOperationResult: Result of the dequeue operation.
        """
        queue_key = KeyBuilder.queue_key(queue_name)
        metadata_key = KeyBuilder.metadata_key(queue_name)

        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is False:
                return result

            if block:
                result = self.redis.blpop(queue_key, timeout=timeout)
                if not result:
                    return QueueOperationResult(
                        True, MOMQueueStatus.EMPTY_QUEUE, ""
                    )
                message = json.loads(result[1])
            else:
                message_json = self.redis.lpop(queue_key)
                if not message_json:
                    return QueueOperationResult(
                        True, MOMQueueStatus.EMPTY_QUEUE, ""
                    )
                message = json.loads(message_json)

            self.redis.hincrby(metadata_key, "total_messages", -1)
            return QueueOperationResult(
                True,
                MOMQueueStatus.SUCCES_OPERATION,
                json.loads(message["payload"]),
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error dequeueing from  '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def get_queue_info(self, queue_name: str) -> QueueOperationResult:
        """
        Get information about the specified queue, specifically 
        its metadata on a string format.
        Args:
            queue_name (str): The name of the queue to get information about.
        Returns:
            QueueOperationResult: Result of the queue information retrieval.
        """
        metadata_key = KeyBuilder.metadata_key(queue_name)
        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is False:
                return result

            metadata = {
                k: v for k, v in self.redis.hgetall(metadata_key).items()
            }
            return QueueOperationResult(
                True, MOMQueueStatus.SUCCES_OPERATION, str(metadata)
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error fetching queue info for '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def delete_queue(self, queue_name: str) -> QueueOperationResult:
        """
        Delete the specified queue and its metadata.
        Args:
            queue_name (str): The name of the queue to delete.
        Returns:
            QueueOperationResult: Result of the queue deletion operation.
        """
        queue_key = KeyBuilder.queue_key(queue_name)
        metadata_key = KeyBuilder.metadata_key(queue_name)
        subscribers_key = KeyBuilder.subscribers_key(queue_name)

        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                return result

            result = self.validator.validate_user_is_owner(queue_name)
            if result.success is False:
                return result

            self.redis.delete(queue_key, metadata_key, subscribers_key)
            return QueueOperationResult(
                True,
                MOMQueueStatus.SUCCES_OPERATION,
                f"Queue '{queue_name}' deleted successfully",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error deleting queue '%s'",queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )
