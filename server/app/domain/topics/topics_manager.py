"""
This class handles the management of topics in a 
Redis-based message system, including creating, deleting,
publishing, and consuming messages.
"""

import os
import json
from datetime import datetime, timedelta
from app.domain.models import TopicOperationResult, MOMTopicStatus
from app.domain.logger_config import logger
from app.domain.utils import TopicKeyBuilder, limpiar_user
from app.domain.topics.topics_subscription import TopicSubscriptionService
from app.domain.topics.topics_validator import TopicValidator


class MOMTopicManager:
    """
    Manager for topic operations in a Redis-based message system.
    Supports n:m communications where messages persist until all 
    subscribers consume them.
    """

    def __init__(self, redis_connection, user: str):
        self.redis = redis_connection
        self.user = user
        self.subscriptions = TopicSubscriptionService(self.redis, self.user)
        self.validator = TopicValidator(self.redis, user)

    def create_topic(self, topic_name: str) -> TopicOperationResult:
        """
        Create a new topic with the specified name.
        Args:
            topic_name (str): The name of the topic to create.
        Returns:
            TopicOperationResult: Result of the topic creation operation.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if result.success:
                result.success = False
                return result

            metadata_key = TopicKeyBuilder.metadata_key(topic_name)

            metadata = {
                "name": topic_name,
                "owner": self.user,
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "processed_count": 0,
            }

            self.redis.hset(metadata_key, mapping=metadata)

            result = self.subscriptions.subscribe(topic_name)
            if not result.success:
                self.redis.delete(metadata_key)
                return result

            return TopicOperationResult(
                True,
                MOMTopicStatus.TOPIC_CREATED,
                f"Topic {topic_name} created successfully",
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Unexpected error creating topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def publish(self, message: str, topic_name: str) -> TopicOperationResult:
        """
        Publish a string message to the specified topic.
        Args:
            message (str): The string message to publish.
            topic_name (str): The name of the topic to publish to.
        Returns:
            TopicOperationResult: Result of the publish operation.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            # Se decidio que el usuario no debe estar subscrito para encolar mensajes
            # result = self.validator.validate_user_subscribed(topic_name)
            # if not result.success:
            #     return result

            full_message = {
                "timestamp": datetime.now().isoformat(),
                "publisher": self.user,
                "payload": message,
            }

            messages_key = TopicKeyBuilder.messages_key(topic_name)
            message_index = self.redis.rpush(
                messages_key, json.dumps(full_message)
            )

            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            self.redis.hincrby(metadata_key, "message_count", 1)

            # self._cleanup_processed_messages(topic_name)

            return TopicOperationResult(
                True,
                MOMTopicStatus.MESSAGE_PUBLISHED,
                f"Message published to topic {topic_name}", # pylint: disable=C0301
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(
                f"Error publishing message to topic '{topic_name}'"
            )
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def consume(self, topic_name: str) -> TopicOperationResult:
        """
        Consume string messages from a topic based on the subscriber's current
        offset. Default is now to consume only one message at a time for 
        better control. Messages remain in the topic for other subscribers.

        Args:
            topic_name (str): The name of the topic to consume from.
            count (int): Maximum number of messages to consume (default: 1).

        Returns:
            TopicOperationResult: Result containing consumed string messages.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            result = self.validator.validate_user_subscribed(topic_name)
            if not result.success:
                return result

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(self.user)
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)

            current_offset = int(self.redis.hget(offset_key, offset_field) or 0)
            total_messages_history = self.redis.hget(
                metadata_key, "message_count"
            )
            total_deleted_messages = self.redis.hget(
                metadata_key, "processed_count"
            )
            real_offset = current_offset - int(total_deleted_messages or 0)
            total_messages_in_topic = self.redis.llen(
                TopicKeyBuilder.messages_key(topic_name)
            )

            if current_offset > int(total_messages_history):
                return TopicOperationResult(
                    True,
                    MOMTopicStatus.INCONSISTENT_STATE,
                    "No new messages available for this subscription",
                )

            if real_offset >= total_messages_in_topic:
                return TopicOperationResult(
                    True,
                    MOMTopicStatus.NO_MESSAGES,
                    "No new messages available for this subscription",
                )

            raw_message = self.redis.lindex(
                TopicKeyBuilder.messages_key(topic_name), real_offset
            )
            message_data = json.loads(raw_message)
            message_owner = limpiar_user(message_data["publisher"])

            # Para no ver mensajes propios
            if message_owner == self.user:
                # Para evitar recursión infinita
                new_offset = current_offset + 1
                self.redis.hset(offset_key, offset_field, new_offset)
                return self.consume(topic_name)

            new_offset = current_offset + 1
            self.redis.hset(offset_key, offset_field, new_offset)

            # deleted_messages = self._cleanup_processed_messages(topic_name)
            # logger.info(f"Deleted {deleted_messages} processed messages from topic '{topic_name}'") # pylint: disable=C0301

            return TopicOperationResult(
                True,
                MOMTopicStatus.MESSAGE_CONSUMED,
                message_data["payload"],

            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(
                f"Error consuming messages from topic '{topic_name}'"
            )
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def _cleanup_processed_messages(self, topic_name: str, force_cleanup_by_time: bool = False) -> int:
        """
        Clean up messages that have been processed by all subscribers or 
        have exceeded the persistence time limit.
        
        Args:
            topic_name (str): The name of the topic to clean up.
            force_cleanup_by_time (bool): Whether to force cleanup based on time even if some 
                                        subscribers haven't read the messages.
        
        Returns:
            int: Number of messages deleted from the topic.
        """
        try:
            # Verificar que el topico existe
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                logger.warning(f"Cannot cleanup nonexistent topic '{topic_name}'")
                return 0
                
            # Obtener claves necesarias
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            
            # Verificar si hay mensajes para limpiar
            total_messages = self.redis.llen(messages_key)
            if total_messages == 0:
                return 0
                
            # Obtener todos los offsets de los suscriptores
            subscriber_offsets = self.redis.hgetall(offset_key)
            if not subscriber_offsets:
                logger.warning(f"No subscribers found for topic '{topic_name}'")
                return 0
                
            # Convertir todos los offsets a enteros
            offsets = [int(offset) for offset in subscriber_offsets.values()]
            
            # El offset mínimo representa la posición del mensaje que algún suscriptor 
            # todavía no ha leído
            min_offset = min(offsets) if offsets else 0
            total_deleted_messages = self.redis.hget(metadata_key, "processed_count")
            if not total_deleted_messages:
                total_deleted_messages = 0
            else:
                total_deleted_messages = int(total_deleted_messages)
            
            real_min_offset = min_offset - total_deleted_messages
            
            # Determinar cuántos mensajes pueden ser eliminados basados en que todos los 
            # hayan leído
            messages_to_delete_by_subscription = max(0, real_min_offset)
            
            # Si se fuerza la limpieza por tiempo, verificar mensajes expirados
            messages_to_delete_by_time = 0
            if force_cleanup_by_time:
                persistency_time = int(os.getenv("PERSISTENCY_ON_TOPIC_TIME", 60))  # tiempo en minutos
                cutoff_time = datetime.now() - timedelta(minutes=persistency_time)
                
                # Verificar cada mensaje hasta el mínimo offset para ver si ha expirado
                for idx in range(messages_to_delete_by_subscription, total_messages):
                    message_json = self.redis.lindex(messages_key, idx)
                    if not message_json:
                        continue
                        
                    message_data = json.loads(message_json)
                    message_time = datetime.fromisoformat(message_data["timestamp"])
                    
                    if message_time < cutoff_time:
                        messages_to_delete_by_time += 1
                    else:
                        # Los mensajes están ordenados por tiempo, así que si este no expiró,
                        # los siguientes tampoco
                        break
                        
            total_messages_to_delete = messages_to_delete_by_subscription + messages_to_delete_by_time
            
            if total_messages_to_delete <= 0:
                return 0
                
            # Si hay mensajes para eliminar por tiempo, ajustar los offsets de todos los suscriptores
            if messages_to_delete_by_time > 0:
                for subscriber, offset in subscriber_offsets.items():
                    current_offset = int(offset)
                    if current_offset < min_offset + messages_to_delete_by_time:
                        # Actualizar el offset para que apunte al siguiente mensaje disponible
                        new_offset = min_offset + messages_to_delete_by_time
                        self.redis.hset(offset_key, subscriber, new_offset)
                        
            # Eliminar los mensajes
            pipeline = self.redis.pipeline()
            
            # Eliminar los mensajes procesados (LTRIM retiene el rango indicado)
            pipeline.ltrim(messages_key, total_messages_to_delete, -1)
            
            # Actualizar contador de mensajes procesados
            pipeline.hincrby(metadata_key, "processed_count", total_messages_to_delete)
            
            pipeline.execute()
            
            logger.info(f"Cleaned up {total_messages_to_delete} messages from topic '{topic_name}' " + 
                    f"({messages_to_delete_by_subscription} by subscription, {messages_to_delete_by_time} by time)")
            
            return total_messages_to_delete
            
        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Error cleaning up messages for topic '{topic_name}': {str(e)}")
            return 0

    def get_topic_info(self, topic_name: str) -> TopicOperationResult:
        """
        Get information about the specified topic.
        Args:
            topic_name (str): The name of the topic to get information about.
        Returns:
            TopicOperationResult: Result of the topic information retrieval.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            metadata = {
                k: v for k, v in self.redis.hgetall(metadata_key).items()
            }

            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            subscribers = [s for s in self.redis.smembers(subscribers_key)]

            messages_key = TopicKeyBuilder.messages_key(topic_name)
            message_count = self.redis.llen(messages_key)

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offsets = {
                k: int(v) for k, v in self.redis.hgetall(offset_key).items()
            }

            topic_info = {
                "metadata": metadata,
                "subscribers": subscribers,
                "message_count": message_count,
                "subscriber_offsets": offsets,
            }

            return TopicOperationResult(
                True,
                MOMTopicStatus.TOPIC_EXISTS,
                topic_info,
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Error fetching topic info for '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def delete_topic(self, topic_name: str) -> TopicOperationResult:
        """
        Delete the specified topic and all its messages.
        Only the owner can delete a topic.

        Args:
            topic_name (str): The name of the topic to delete.
        Returns:
            TopicOperationResult: Result of the topic deletion operation.
        """
        try:
            # Check if topic exists
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            # Check if user is the owner
            result = self.validator.validate_user_is_owner(topic_name)
            if not result.success:
                return TopicOperationResult(
                    False,
                    MOMTopicStatus.INVALID_ARGUMENTS,
                    "Only the topic owner can delete it",
                )

            # Delete all topic-related keys
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)

            self.redis.delete(
                metadata_key, subscribers_key, messages_key, offset_key
            )

            return TopicOperationResult(
                True,
                MOMTopicStatus.TOPIC_DELETED,
                f"Topic {topic_name} deleted successfully",
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Error deleting topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def get_user_topics(self) -> TopicOperationResult:
        """
        Get all topics the user is subscribed to.

        Returns:
            TopicOperationResult: Result with list of topics.
        """
        try:
            topic_pattern = f"{TopicKeyBuilder.TOPIC_PREFIX}:*:{TopicKeyBuilder.SUBSCRIBERS_SUFFIX}" # pylint: disable=C0301
            subscriber_keys = self.redis.keys(topic_pattern)

            subscribed_topics = []
            for key in subscriber_keys:
                topic_name = key.split(":")[2]

                if self.redis.sismember(key, self.user):
                    subscribed_topics.append(topic_name)

            return TopicOperationResult(
                True,
                MOMTopicStatus.SUBSCRIPTION_CREATED,
                {"subscribed_topics": subscribed_topics},
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception("Error fetching user topics")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def schedule_cleanup(self, topic_name: str = None) -> TopicOperationResult:
        """
        Schedule or execute cleanup of processed messages for a specific topic or all topics.
        
        Args:
            topic_name (str, optional): The name of the topic to clean up. If None, clean up all topics.
        
        Returns:
            TopicOperationResult: Result of the cleanup operation.
        """
        try:
            if topic_name:
                # Limpiar un tema específico
                deleted_count = self._cleanup_processed_messages(topic_name, force_cleanup_by_time=True)
                return TopicOperationResult(
                    True,
                    MOMTopicStatus.MESSAGES_CLEANED,
                    f"Cleaned up {deleted_count} messages from topic '{topic_name}'"
                )
            else:
                # Limpiar todos los temas
                # Buscar todos los temas usando un patrón en las claves
                metadata_pattern = TopicKeyBuilder.metadata_key_pattern()
                all_metadata_keys = self.redis.keys(metadata_pattern)
                
                total_deleted = 0
                for metadata_key in all_metadata_keys:
                    # Extraer el nombre del tema de la clave de metadata
                    topic_name = metadata_key.decode().split(":")[-1]
                    deleted_count = self._cleanup_processed_messages(topic_name, force_cleanup_by_time=True)
                    total_deleted += deleted_count
                    
                return TopicOperationResult(
                    True,
                    MOMTopicStatus.MESSAGES_CLEANED,
                    f"Cleaned up {total_deleted} messages from all topics"
                )
                
        except Exception as e:  # pylint: disable=W0718
            logger.exception(f"Error scheduling cleanup: {str(e)}")
            return TopicOperationResult(
                False,
                MOMTopicStatus.OPERATION_FAILED,
                f"Error scheduling cleanup: {str(e)}"
            )