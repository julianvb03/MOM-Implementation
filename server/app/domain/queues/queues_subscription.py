"""
This module provides a service for managing subscriptions to message queues,
including subscribing and unsubscribing users to/from queues,
this way isolating the subscription logic from the queue management logic.
"""

from app.domain.models import QueueOperationResult, MOMQueueStatus
from app.domain.logger_config import logger
from app.domain.utils import KeyBuilder
from app.domain.queues.queues_validator import QueueValidator
from app.domain.queue_replication_clients import (
    get_source_queue_client,
    get_target_queue_client,
)
from app.domain.models import NODES_CONFIG, WHOAMI
from app.domain.queues.queues_replication import QueueReplicationClient


class SubscriptionService:
    """
    This class handles the subscription management for message queues,
    including subscribing and unsubscribing users to/from queues.
    """

    def __init__(self, redis, user: str):
        self.redis = redis
        self.user = user
        self.validator = QueueValidator(redis, user)

        # Obtener los stubs de replicación
        replica_stub = get_target_queue_client()
        source_stub = get_source_queue_client()

        current_node_config = NODES_CONFIG[WHOAMI]
        replica_node = current_node_config["whoreplica"]

        # Crear clientes de replicación con los stubs
        # replication_client apunta al nodo replicante
        # replication_principal apunta al nodo principal
        self.replication_client = QueueReplicationClient(
            stub=replica_stub, target_node_desc=f"nodo réplica ({replica_node})"
        )
        self.replication_principal = QueueReplicationClient(
            stub=source_stub, target_node_desc=f"nodo principal ({WHOAMI})"
        )

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
                result.replication_result = False
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is True:
                result.success = False
                result.replication_result = False
                return result

            subscribers_key = KeyBuilder.subscribers_key(queue_name)
            self.redis.sadd(subscribers_key, self.user)

            # Verificar si soy el nodo principal para este queue
            metadata_key = KeyBuilder.metadata_key(queue_name)
            result = self.redis.hget(metadata_key, "original_node")
            principal = bool(int(result))

            # Replicación
            replication_op = False
            if not principal:
                # Si no soy principal, replico al nodo original
                replication_op = self.replication_principal.subscribe(
                    queue_name, self.user
                )
            else:
                # Si soy principal, replico a quien me replica a mí
                replication_op = self.replication_client.subscribe(
                    queue_name, self.user
                )

            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.SUCCES_OPERATION,
                details=f"User {self.user} subscribed to {queue_name}",
                replication_result=replication_op,
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception("Error subscribing to queue '%s'", queue_name)
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False,
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
                result.replication_result = False
                return result

            result = self.validator.validate_user_is_owner(queue_name)
            if result.success is True:
                result.success = False
                result.details = "User is the owner of the queue and cannot unsubscribe" # pylint: disable=C0301
                return result

            result = self.validator.validate_user_subscribed(queue_name)
            if result.success is False:
                result.success = False
                return result

            subscribers_key = KeyBuilder.subscribers_key(queue_name)
            self.redis.srem(subscribers_key, self.user)

            # Verificar si soy el nodo principal para este queue
            metadata_key = KeyBuilder.metadata_key(queue_name)
            result = self.redis.hget(metadata_key, "original_node")
            principal = bool(int(result))
            # Replicación
            replication_op = False
            if not principal:
                # Si no soy principal, replico al nodo original
                replication_op = self.replication_principal.unsubscribe(
                    queue_name, self.user
                )
            else:
                # Si soy principal, replico a quien me replica a mí
                replication_op = self.replication_client.unsubscribe(
                    queue_name, self.user
                )

            return QueueOperationResult(
                success=True,
                status=MOMQueueStatus.SUCCES_OPERATION,
                details=f"User {self.user} unsubscribed from {queue_name}",
                replication_result=replication_op,
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception("Error unsubscribing from queue '%s'", queue_name)
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False,
            )
