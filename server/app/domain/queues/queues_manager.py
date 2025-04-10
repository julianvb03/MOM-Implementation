"""
This module provides a class for managing message queues using Redis,
including creating, deleting, enqueuing, and dequeuing messages.
"""

import json
import uuid as uuid_lib
from datetime import datetime, timezone
from app.domain.models import MOMQueueStatus, QueueOperationResult
from app.domain.logger_config import logger
from app.domain.utils import KeyBuilder
from app.domain.queues.queues_subscription import SubscriptionService
from app.domain.queues.queues_validator import QueueValidator
from app.domain.queue_replication_clients import get_source_queue_client, get_target_queue_client
from app.domain.models import NODES_CONFIG, WHOAMI
from app.domain.queues.queues_replication import QueueReplicationClient
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

        # Obtener los stubs de replicación
        replica_stub = get_target_queue_client()
        source_stub = get_source_queue_client()

        current_node_config = NODES_CONFIG[WHOAMI]
        replica_node = current_node_config["whoreplica"]

        # Crear clientes de replicación con los stubs
        # replication_client apunta al nodo replicante
        # replication_principal apunta al nodo principal
        self.replication_client = QueueReplicationClient(
        stub=replica_stub,
        target_node_desc=f"nodo réplica ({replica_node})"
        )
        self.replication_principal = QueueReplicationClient(
            stub=source_stub,
            target_node_desc=f"nodo principal ({WHOAMI})"
        )

    def create_queue(
        self, queue_name: str, message_limit: int = 1000,
        principal: bool = True, created_at: str = None
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
            if result.success:
                result.success = False
                result.replication_result = False
                return result

            if created_at is None:
                created_at = datetime.now().timestamp()

            metadata = {
                "name": queue_name,
                "owner": self.user,
                "created_at": created_at,
                "total_messages": 0,
                "original_node": int(principal)
            }

            self.redis.hset(metadata_key, mapping=metadata)
            result = self.subscriptions.subscribe(queue_name)

            if result.success is False:
                self.redis.delete(metadata_key, queue_key)
                return result

            # Replication
            if principal:
                result = self.replication_client.create_queue(
                    queue_name=queue_name,
                    owner=self.user,
                    created_at=created_at
                )
                if result is False:
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.INTERNAL_ERROR,
                        details=f"Queue {queue_name} created successfully",
                        replication_result=False
                    )

            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.QUEUE_CREATED,
                details=f"Queue {queue_name} created successfully",
                replication_result=True
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Unexpected error creating queue '%s'", queue_name)
            return QueueOperationResult(
                False, MOMQueueStatus.INTERNAL_ERROR, str(e)
            )

    def enqueue(self, message: str, queue_name: str,
                uuid: str = None, timestamp = None,
                im_replicating = False) -> QueueOperationResult:
        """
        Enqueue a message to the specified queue.
        Args:
            message (str): The message to enqueue.
            queue_name (str): The name of the queue to enqueue the message to.
            uuid (str): The UUID of the message.
            timestamp (float): The timestamp of the message.
        Returns:
            QueueOperationResult: Result of the enqueue operation.
        """
        try:
            queue_key = KeyBuilder.queue_key(queue_name)
            metadata_key = KeyBuilder.metadata_key(queue_name)

            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                result.success = False
                result.replication_result = False
                return result

            # Se decidio que el usuario no debe estar subscrito para
            # encolar mensajes
            # result = self.validator.validate_user_subscribed(queue_name)
            # if result.success is False:
            #     return result

            principal = bool(int(self.redis.hget(metadata_key, "original_node"))) # pylint: disable=C0301
            if principal and uuid is None:
                uuid = str(uuid_lib.uuid4())
            if principal and timestamp is None:
                timestamp = datetime.now(timezone.utc).timestamp()

            full_message = {
                "id": uuid,
                "timestamp": timestamp,
                "payload": json.dumps(message),
            }
            self.redis.rpush(queue_key, json.dumps(full_message))
            self.redis.hincrby(metadata_key, "total_messages", 1)
            ## TO DO
            ## Garantizar la replicación de los mensajes
            replication_result = True  # Asumir éxito por defecto
            if not im_replicating:  # Solo replicar si no es una replicación
                if principal:
                    replication_result = self.replication_client.enqueue(
                        queue_name=queue_name,
                        user=self.user,
                        message=message,
                        uuid=uuid,
                        timestamp=timestamp
                    )
                else:
                    replication_result = self.replication_principal.enqueue(
                        queue_name=queue_name,
                        user=self.user,
                        message=message,
                        uuid=uuid,
                        timestamp=timestamp
                    )

            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.SUCCES_OPERATION,
                details="Message enqueued successfully",
                replication_result=replication_result
            )
        except Exception as e: # pylint: disable=W0718
            logger.exception("Error enqueueing message to '%s'", queue_name)
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False
            )

    def dequeue(
        self, queue_name: str, uuid: str = None, im_replicating: bool = False
    ) -> QueueOperationResult:
        """
        Dequeue a message from the specified queue.
        Args:
            queue_name (str): The name of the queue to dequeue from.
            uuid (str): The UUID of the message to dequeue.
            im_replicating (bool): Whether this is a replication operation.
        Returns:
            QueueOperationResult: Result of the dequeue operation.
        """
        queue_key = KeyBuilder.queue_key(queue_name)
        metadata_key = KeyBuilder.metadata_key(queue_name)

        try:
            result = self.validator.validate_queue_exists(queue_name)
            if result.success is False:
                result.replication_result = False
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is False:
                result.replication_result = False
                return result

            principal = bool(int(self.redis.hget(metadata_key, "original_node"))) # pylint: disable=C0301

            if uuid is not None:
                # Caso con UUID específico
                messages = self.redis.lrange(queue_key, 0, -1)
                message_to_dequeue = None
                for msg in messages:
                    msg_data = json.loads(msg)
                    if msg_data["id"] == uuid:
                        message_to_dequeue = msg_data
                        # Eliminar el mensaje específico
                        self.redis.lrem(queue_key, 1, msg)
                        break

                if not message_to_dequeue:
                    return QueueOperationResult(
                        success=False,
                        status=MOMQueueStatus.MESSAGE_NOT_FOUND,
                        details="Message not found",
                        replication_result=False
                    )
            else:
                # Caso de pop normal
                message_json = self.redis.lpop(queue_key)
                if not message_json:
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.EMPTY_QUEUE,
                        details="",
                        replication_result=False
                    )
                message_to_dequeue = json.loads(message_json)

            self.redis.hincrby(metadata_key, "total_messages", -1)

            # Replicación
            replication_result = True
            if not im_replicating:
                if not principal:
                    # Si no soy principal, replico al nodo original
                    replication_result = self.replication_principal.dequeue(
                        queue_name=queue_name,
                        user=self.user,
                        uuid=message_to_dequeue["id"]
                    )
                else:
                    # Si soy principal, replico a quien me replica a mí
                    replication_result = self.replication_client.dequeue(
                        queue_name=queue_name,
                        user=self.user,
                        uuid=message_to_dequeue["id"]
                    )

            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.SUCCES_OPERATION,
                details=json.loads(message_to_dequeue["payload"]),
                replication_result=replication_result
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

            principal = bool(int(self.redis.hget(metadata_key, "original_node"))) # pylint: disable=C0301
            self.redis.delete(queue_key, metadata_key, subscribers_key)
            if principal:
                result = self.replication_client.delete_queue(
                    queue_name=queue_name,
                    owner=self.user
                )
                if result is False:
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.INTERNAL_ERROR,
                        details="Queue deleted successfully, but replication failed", # pylint: disable=C0301
                        replication_result=False
                    )

            # Replication
            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.SUCCES_OPERATION,
                details=f"Queue '{queue_name}' deleted successfully",
                replication_result=True
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception("Error deleting queue '%s'",queue_name)
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False
            )
