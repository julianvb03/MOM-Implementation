"""
This class handles the management of topic subscriptions in a Redis database,
including subscribing and unsubscribing users to/from topics.
    it uses the TopicValidator class for validating topic operations.
    It also provides methods for checking the status of topics and
    managing topic metadata. The class is initialized with a Redis
    connection and a user identifier.
"""

from app.domain.models import TopicOperationResult, MOMTopicStatus
from app.domain.logger_config import logger
from app.domain.utils import TopicKeyBuilder
from app.domain.topics.topics_validator import TopicValidator
from app.domain.models import NODES_CONFIG, WHOAMI
from app.domain.topics.topics_replication import TopicReplicationClient
from app.domain.replication_clients import (
    get_replica_client_stub,
    get_source_client_stub,
)
from app.adapters.factory import ObjectFactory
from app.adapters.db import Database


class TopicSubscriptionService:
    """
    Service for managing topic subscriptions.
    """
    def __init__(self, redis, user: str):
        self.redis = redis
        self.redis_backup = ObjectFactory.get_instance(Database, ObjectFactory.BACK_UP_DATABASE).get_client()
        self.redis_nodes = ObjectFactory.get_instance(Database, ObjectFactory.NODES_DATABASE).get_client()
        self.user = user
        self.validator = TopicValidator(redis, user)

        # Obtener los stubs de replicación
        replica_stub = get_source_client_stub()
        source_stub = get_replica_client_stub()

        # Obtener la configuración del nodo actual
        current_node_config = NODES_CONFIG[WHOAMI]
        replica_node = current_node_config["whoreplica"]

        # Crear clientes de replicación con los stubs
        self.replication_client = TopicReplicationClient(
            stub=replica_stub, target_node_desc=f"nodo réplica ({replica_node})"
        )
        self.replication_principal = TopicReplicationClient(
            stub=source_stub, target_node_desc=f"nodo principal ({WHOAMI})"
        )

    def subscribe(self, topic_name: str, endpoint: bool = False) -> TopicOperationResult:
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                # Verificamos si el tópico existe en algún nodo usando SMEMBERS
                nodes = ["A", "B", "C"]
                topic_exists_somewhere = False
                target_nodes = []

                for node in nodes:
                    # Verificamos si "topic:topic_name" está en el set del nodo
                    members = self.redis_nodes.smembers(node)
                    if f"topic:{topic_name}" in members:
                        topic_exists_somewhere = True
                        target_nodes.append(node)

                if not topic_exists_somewhere:
                    return TopicOperationResult(
                        success=False,
                        status=MOMTopicStatus.TOPIC_NOT_EXIST,
                        details="El tópico no existe en ningún nodo",
                        replication_result=False
                    )

                # Si el tópico existe en algún nodo, intentamos el forward
                nodes.remove(WHOAMI)
                for node in nodes:
                    if node in target_nodes:  # Solo intentamos forward a nodos donde sabemos que existe el tópico
                        result = self.replication_client.forward_subscribe(
                            topic_name=topic_name,
                            user=self.user,
                            node=node
                        )
                        if result.success:
                            return result

                result.success = False
                result.replication_result = False
                return result

            result = self.validator.validate_user_subscribed(topic_name)
            if result.success:
                return TopicOperationResult(
                    success=False,
                    status=MOMTopicStatus.ALREADY_SUBSCRIBED,
                    details=f"User {self.user} is already subscribed to topic {topic_name}", # pylint: disable=C0301
                    replication_result=False,
                )

            # Verificar si soy el nodo principal para este tópico
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            result = self.redis.hget(metadata_key, "original_node")
            principal = bool(int(result))

            # Realizar la suscripción local
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            self.redis.sadd(subscribers_key, self.user)

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(self.user)
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)

            current_index = self.redis.hget(metadata_key, "message_count")
            initial_offset = int(current_index) if current_index is not None else 0  # pylint: disable=C0301

            self.redis.hset(offset_key, offset_field, initial_offset)

            if endpoint:
                # Realizar todas las operaciones en el backup
                self.redis_backup.sadd(subscribers_key, self.user)
                self.redis_backup.hset(offset_key, offset_field, initial_offset)


            # Replicar la suscripción según el rol del nodo
            replication_op = False
            if principal:
                replication_op = self.replication_client.replicate_subscribe(
                    topic_name, self.user
                )
            else:
                replication_op = self.replication_principal.replicate_subscribe(
                    topic_name, self.user
                )

            return TopicOperationResult(
                success=True,
                status=MOMTopicStatus.SUBSCRIPTION_CREATED,
                details=f"User {self.user} subscribed to topic {topic_name}",
                replication_result=replication_op,
            )

        except Exception as e: # pylint: disable=W0703
            logger.exception("Error subscribing to topic '%s'", topic_name)
            return TopicOperationResult(
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False,
            )

    def unsubscribe(self, topic_name: str, endpoint: bool = False) -> TopicOperationResult:
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                # Verificamos si el tópico existe en algún nodo usando SMEMBERS
                nodes = ["A", "B", "C"]
                topic_exists_somewhere = False
                target_nodes = []

                for node in nodes:
                    # Verificamos si "topic:topic_name" está en el set del nodo
                    members = self.redis_nodes.smembers(node)
                    if f"topic:{topic_name}" in members:
                        topic_exists_somewhere = True
                        target_nodes.append(node)

                if not topic_exists_somewhere:
                    return TopicOperationResult(
                        success=False,
                        status=MOMTopicStatus.TOPIC_NOT_EXIST,
                        details="El tópico no existe en ningún nodo",
                        replication_result=False
                    )

                # Si el tópico existe en algún nodo, intentamos el forward
                nodes.remove(WHOAMI)
                for node in nodes:
                    if node in target_nodes:  # Solo intentamos forward a nodos donde sabemos que existe el tópico
                        result = self.replication_client.forward_unsubscribe(
                            topic_name=topic_name,
                            user=self.user,
                            node=node
                        )
                        if result.success:
                            return result

                result.success = False
                result.replication_result = False
                return result

            result = self.validator.validate_user_is_owner(topic_name)
            if result.success:
                return TopicOperationResult(
                    success=False,
                    status=MOMTopicStatus.ALREADY_SUBSCRIBED,
                    details="User is the owner of the topic and cannot unsubscribe", # pylint: disable=C0301
                    replication_result=False,
                )

            result = self.validator.validate_user_subscribed(topic_name)
            if not result.success:
                result.success = False
                result.replication_result = False
                return result

            # Verificar si soy el nodo principal para este tópico
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            result = self.redis.hget(metadata_key, "original_node")
            principal = bool(int(result))

            # Realizar la desuscripción local
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            self.redis.srem(subscribers_key, self.user)

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(self.user)
            self.redis.hdel(offset_key, offset_field)

            if endpoint:
                # Realizar todas las operaciones en el backup
                self.redis_backup.srem(subscribers_key, self.user)
                self.redis_backup.hdel(offset_key, offset_field)

            # Replicar la desuscripción según el rol del nodo
            replication_op = False
            if principal:
                replication_op = self.replication_client.replicate_unsubscribe(
                    topic_name, self.user
                )
            else:
                replication_op = self.replication_principal.replicate_unsubscribe(  # pylint: disable=C0301
                    topic_name, self.user
                )

            return TopicOperationResult(
                success=True,
                status=MOMTopicStatus.SUBSCRIPTION_DELETED,
                details=f"User {self.user} unsubscribed from topic {topic_name}", # pylint: disable=C0301
                replication_result=replication_op,
            )

        except Exception as e: # pylint: disable=W0703
            logger.exception("Error unsubscribing from topic '%s'", topic_name)
            return TopicOperationResult(
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details=str(e),
                replication_result=False,
            )
