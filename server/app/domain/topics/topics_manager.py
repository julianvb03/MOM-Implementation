"""
This class handles the management of topics in a
Redis-based message system, including creating, deleting,
publishing, and consuming messages.
"""

import os
import json
import redis
from datetime import datetime
from app.domain.models import TopicOperationResult, MOMTopicStatus
from app.domain.logger_config import logger
from app.domain.utils import TopicKeyBuilder
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
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            with self.redis.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(metadata_key)
                        if pipe.exists(metadata_key):
                            return TopicOperationResult(
                                False,
                                MOMTopicStatus.TOPIC_EXISTS,
                                "Topic exists",
                            )

                        # Inicia transacción
                        pipe.multi()

                        # Crear metadata
                        metadata = {
                            "name": topic_name,
                            "owner": self.user,
                            "created_at": datetime.now().timestamp(),
                            "message_count": 0,
                            "processed_count": 0,
                        }
                        pipe.hset(metadata_key, mapping=metadata)

                        # Suscribir al usuario (dentro de la misma transacción)
                        subscribers_key = TopicKeyBuilder.subscribers_key(topic_name) # pylint: disable=C0301
                        pipe.sadd(subscribers_key, self.user)

                        # Inicializar offset
                        offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name) # pylint: disable=C0301
                        offset_field = TopicKeyBuilder.subscriber_offset_field(self.user) # pylint: disable=C0301
                        pipe.hsetnx(offset_key, offset_field, 0)

                        pipe.execute()  # Ejecuta todo atómicamente
                        return TopicOperationResult(
                            True,
                            MOMTopicStatus.TOPIC_CREATED,
                            f"Topic {topic_name} created successfully",
                        )
                    except redis.WatchError:
                        # Reintentar si otra transacción modificó metadata_key
                        continue
        except Exception as e: # pylint: disable=W0718
            logger.exception("Error creating topic '%s'", topic_name)
            return TopicOperationResult(False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)) # pylint: disable=C0301

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
            with self.redis.pipeline() as pipe:
                # Validar existencia del tópico
                result = self.validator.validate_topic_exists(topic_name)
                if not result.success:
                    return result

                # Preparar mensaje
                full_message = {
                    "timestamp": datetime.now().timestamp(),
                    "publisher": self.user,
                    "payload": message,
                }

                # Ejecutar en transacción
                pipe.multi()
                messages_key = TopicKeyBuilder.messages_key(topic_name)
                pipe.rpush(messages_key, json.dumps(full_message))
                metadata_key = TopicKeyBuilder.metadata_key(topic_name)
                pipe.hincrby(metadata_key, "message_count", 1)
                pipe.execute()  # Atomicidad garantizada

                return TopicOperationResult(
                    True,
                    MOMTopicStatus.MESSAGE_PUBLISHED,
                    f"Message published to topic {topic_name}",
                )
        except Exception as e: # pylint: disable=W0718
            logger.exception("Error publishing to topic '%s'", topic_name)
            return TopicOperationResult(False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)) # pylint: disable=C0301

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
            lua_script = """
            local offset_key = KEYS[1]
            local messages_key = KEYS[2]
            local metadata_key = KEYS[3]
            local user = ARGV[1]

            -- Obtener campo del offset
            local offset_field = "subscriber_offset:" .. user
            local current_offset = tonumber(redis.call('HGET', offset_key, offset_field))
            
            -- Validar offset inicializado
            if not current_offset then
                return {"ERROR", "OFFSET_NOT_INITIALIZED"}
            end

            -- Obtener mensajes procesados
            local total_deleted = tonumber(redis.call('HGET', metadata_key, 'processed_count') or 0)

            -- Calcular offset real
            local real_offset = current_offset - total_deleted
            if real_offset < 0 then
                return {"ERROR", "INVALID_OFFSET"}
            end

            -- Verificar si hay mensajes
            local total_messages = redis.call('LLEN', messages_key)
            if real_offset >= total_messages then
                return {"NO_MESSAGES"}
            end

            -- Leer mensaje
            local raw_message = redis.call('LINDEX', messages_key, real_offset)
            if not raw_message then
                return {"NO_MESSAGES"}
            end

            -- Decodificar mensaje
            local success, message_data = pcall(cjson.decode, raw_message)
            if not success or type(message_data) ~= "table" then
                return {"ERROR", "MESSAGE_CORRUPTED"}
            end

            -- Saltar mensajes propios
            if message_data.publisher == user then
                redis.call('HSET', offset_key, offset_field, current_offset + 1)
                local new_real_offset = (current_offset + 1) - total_deleted
                if new_real_offset >= redis.call('LLEN', messages_key) then
                    return {"NO_MESSAGES"}
                else
                    return {"SELF_MESSAGE"}
                end
            end

            -- Actualizar offset y retornar mensaje
            redis.call('HSET', offset_key, offset_field, current_offset + 1)
            return {"MESSAGE", raw_message}
            """

            keys = [
                TopicKeyBuilder.subscriber_offsets_key(topic_name),
                TopicKeyBuilder.messages_key(topic_name),
                TopicKeyBuilder.metadata_key(topic_name),
            ]

            result = self.redis.eval(lua_script, 3, *keys, self.user)

            # Manejo de resultados
            if isinstance(result, list):
                status = result[0].decode() if isinstance(result[0], bytes) else result[0] # pylint: disable=C0301

                if status == "NO_MESSAGES":
                    return TopicOperationResult(
                        True,
                        MOMTopicStatus.NO_MESSAGES,
                        "No new messages"
                    )

                elif status == "SELF_MESSAGE":
                    return self.consume(topic_name)  # Reintentar recursivamente

                elif status == "MESSAGE":
                    message_data = json.loads(result[1])
                    return TopicOperationResult(
                        True,
                        MOMTopicStatus.MESSAGE_CONSUMED,
                        message_data.get("payload", "")
                    )

                elif status == "ERROR":
                    error_details = result[1].decode() if len(result) > 1 else "Unknown error" # pylint: disable=C0301
                    return TopicOperationResult(
                        False,
                        MOMTopicStatus.INTERNAL_ERROR,
                        error_details
                    )

            return TopicOperationResult(
                False,
                MOMTopicStatus.INTERNAL_ERROR,
                "Invalid response format"
            )

        except redis.exceptions.ResponseError as e:
            logger.error("Redis protocol error: %s", str(e))
            return TopicOperationResult(
                False,
                MOMTopicStatus.INTERNAL_ERROR,
                f"Protocol error: {str(e)}"
            )

        except Exception as e: # pylint: disable=W0718
            logger.error("System error: %s", str(e))
            return TopicOperationResult(
                False,
                MOMTopicStatus.TOPIC_NOT_EXIST,
                str(e)
            )

    def _cleanup_processed_messages(
        self, topic_name: str, force_cleanup_by_time: bool = False
    ) -> int:
        """
        Clean up messages that have been processed by all subscribers or
        have exceeded the persistence time limit.

        Args:
            topic_name (str): The name of the topic to clean up.
            force_cleanup_by_time (bool): Whether to force cleanup based on time 
                        even if some subscribers haven't read the messages.

        Returns:
            int: Number of messages deleted from the topic.
        """
        try:
            # Validar existencia del tópico
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return 0

            # Obtener claves necesarias
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)

            # Script Lua para atomicidad
            lua_script = """
            local messages_key = KEYS[1]
            local offset_key = KEYS[2]
            local metadata_key = KEYS[3]
            local force_cleanup = ARGV[1] == 'true'
            local persistency_time = tonumber(ARGV[2])

            -- 1. Obtener offsets y metadatos
            local subscriber_offsets = redis.call('HGETALL', offset_key)
            local total_messages = redis.call('LLEN', messages_key)
            local total_deleted = tonumber(redis.call('HGET', metadata_key, 'processed_count') or 0)

            -- 2. Calcular mensajes a eliminar por suscripción
            local min_offset = math.huge
            for i = 1, #subscriber_offsets, 2 do
                local offset = tonumber(subscriber_offsets[i+1])
                min_offset = math.min(min_offset, offset)
            end
            local real_min_offset = min_offset - total_deleted
            local messages_to_delete_by_subscription = math.max(0, real_min_offset)

            -- 3. Calcular mensajes a eliminar por tiempo
            local messages_to_delete_by_time = 0
            if force_cleanup then
                local cutoff = tonumber(redis.call('TIME')[1]) - (persistency_time * 60)
                for i = messages_to_delete_by_subscription, total_messages - 1 do
                    local msg = redis.call('LINDEX', messages_key, i)
                    if not msg then break end
                    local timestamp = tonumber(cjson.decode(msg)['timestamp'])
                    if timestamp < cutoff then
                        messages_to_delete_by_time = messages_to_delete_by_time + 1
                    else
                        break
                    end
                end
            end

            -- 4. Total de mensajes a eliminar
            local total_messages_to_delete = messages_to_delete_by_subscription + messages_to_delete_by_time

            -- 5. Ajustar offsets si hay limpieza por tiempo
            if messages_to_delete_by_time > 0 then
                for i = 1, #subscriber_offsets, 2 do
                    local subscriber = subscriber_offsets[i]
                    local current_offset = tonumber(subscriber_offsets[i+1])
                    if current_offset < (min_offset + messages_to_delete_by_time) then
                        redis.call('HSET', offset_key, subscriber, min_offset + messages_to_delete_by_time)
                    end
                end
            end

            -- 6. Eliminar mensajes y actualizar metadatos
            if total_messages_to_delete > 0 then
                redis.call('LTRIM', messages_key, total_messages_to_delete, -1)
                redis.call('HINCRBY', metadata_key, 'processed_count', total_messages_to_delete)
            end

            return total_messages_to_delete
            """

            # Ejecutar script
            persistency_time = int(os.getenv("PERSISTENCY_ON_TOPIC_TIME", "60"))
            deleted = self.redis.eval(
                lua_script,
                3,
                messages_key,
                offset_key,
                metadata_key,
                str(force_cleanup_by_time).lower(),
                persistency_time
            )

            logger.info("Cleaned up %d messages from topic '%s'", deleted, topic_name) # pylint: disable=C0301
            return deleted

        except Exception: # pylint: disable=W0718
            logger.exception("Error cleaning up messages for topic '%s'", topic_name) # pylint: disable=C0301
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
                "messages_in_queue": message_count,
                "subscriber_offsets": offsets,
            }

            return TopicOperationResult(
                True,
                MOMTopicStatus.TOPIC_EXISTS,
                topic_info,
            )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(
                "Error fetching topic info for '%s'", topic_name
            )  # pylint: disable=C0301
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
            with self.redis.pipeline() as pipe:
                # Validar existencia y ownership
                result = self.validator.validate_topic_exists(topic_name)
                if not result.success:
                    return result
                result = self.validator.validate_user_is_owner(topic_name)
                if not result.success:
                    return TopicOperationResult(
                        False,
                        MOMTopicStatus.INVALID_ARGUMENTS,
                        "Only the topic owner can delete it",
                        )

                # Eliminar en transacción
                pipe.multi()
                keys = [
                    TopicKeyBuilder.metadata_key(topic_name),
                    TopicKeyBuilder.subscribers_key(topic_name),
                    TopicKeyBuilder.messages_key(topic_name),
                    TopicKeyBuilder.subscriber_offsets_key(topic_name),
                ]
                pipe.delete(*keys)
                pipe.execute()  # Borrado atómico

                return TopicOperationResult(
                    True,
                    MOMTopicStatus.TOPIC_DELETED,
                    f"Topic {topic_name} deleted successfully",
                )
        except Exception as e: # pylint: disable=W0718
            logger.exception("Error deleting topic '%s'", topic_name)
            return TopicOperationResult(False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)) # pylint: disable=C0301

    def get_user_topics(self) -> TopicOperationResult:
        """
        Get all topics the user is subscribed to.

        Returns:
            TopicOperationResult: Result with list of topics.
        """
        try:
            topic_pattern = f"{TopicKeyBuilder.TOPIC_PREFIX}:*:{TopicKeyBuilder.SUBSCRIBERS_SUFFIX}"  # pylint: disable=C0301
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
        Schedule or execute cleanup of processed messages for a specific 
        topic or all topics.

        Args:
            topic_name (str, optional): The name of the topic to clean up. If 
                None, clean up all topics.

        Returns:
            TopicOperationResult: Result of the cleanup operation.
        """
        try:
            if topic_name:
                # Limpiar un tema específico
                deleted_count = self._cleanup_processed_messages(
                    topic_name, force_cleanup_by_time=True
                )  # pylint: disable=C0301
                return TopicOperationResult(
                    True,
                    MOMTopicStatus.MESSAGES_CLEANED,
                    f"Cleaned up {deleted_count} messages from topic '{topic_name}'",  # pylint: disable=C0301
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
                    deleted_count = self._cleanup_processed_messages(
                        topic_name, force_cleanup_by_time=True
                    )  # pylint: disable=C0301
                    total_deleted += deleted_count

                return TopicOperationResult(
                    True,
                    MOMTopicStatus.MESSAGES_CLEANED,
                    f"Cleaned up {total_deleted} messages from all topics",
                )

        except Exception as e:  # pylint: disable=W0718
            logger.exception(
                "Error scheduling cleanup for topic '%s'", topic_name
            )  # pylint: disable=C0301
            return TopicOperationResult(
                False,
                MOMTopicStatus.OPERATION_FAILED,
                f"Error scheduling cleanup: {str(e)}",
            )
