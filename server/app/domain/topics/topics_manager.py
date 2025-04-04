import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from models import TopicOperationResult, MOMTopicStatus
from logger_config import logger
from utils import TopicKeyBuilder, limpiar_user
from topics.topics_subscription import TopicSubscriptionService
from topics.topics_validator import TopicValidator
 
class MOMTopicManager:
    """
    Manager for topic operations in a Redis-based message system.
    Supports n:m communications where messages persist until all subscribers consume them.
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

        except Exception as e:
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

            result = self.validator.validate_user_subscribed(topic_name)
            if not result.success:
                return result

            full_message = {
                "timestamp": datetime.now().isoformat(),
                "publisher": self.user,
                "payload": message,
            }
            
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            message_index = self.redis.rpush(messages_key, json.dumps(full_message))
            
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            self.redis.hincrby(metadata_key, "message_count", 1)

            #self._cleanup_processed_messages(topic_name)

            return TopicOperationResult(
                True,
                MOMTopicStatus.MESSAGE_PUBLISHED,
                f"Message published to topic {topic_name} at index {message_index}",
            )

        except Exception as e:
            logger.exception(f"Error publishing message to topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def consume(self, topic_name: str ) -> TopicOperationResult:
        """
        Consume string messages from a topic based on the subscriber's current offset.
        Default is now to consume only one message at a time for better control.
        Messages remain in the topic for other subscribers.
        
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
            total_messages_history = self.redis.hget(metadata_key, "message_count")
            total_deleted_messages = self.redis.hget(metadata_key, "processed_count")
            real_offset = current_offset - int(total_deleted_messages or 0)
            total_messages_in_topic = self.redis.llen(TopicKeyBuilder.messages_key(topic_name))

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
            
            raw_message = self.redis.lindex(TopicKeyBuilder.messages_key(topic_name), real_offset)
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
            
            #deleted_messages = self._cleanup_processed_messages(topic_name)
            #logger.info(f"Deleted {deleted_messages} processed messages from topic '{topic_name}'")
            
            return TopicOperationResult(
                True,
                MOMTopicStatus.MESSAGE_PUBLISHED,
                {
                    "messages": [message_data["payload"]],
                    "new_offset": new_offset
                },
            )

        except Exception as e:
            logger.exception(f"Error consuming messages from topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def _cleanup_processed_messages(self, topic_name: str) -> int:
        """
        Delete processed messages from the topic to save memory
        Only messages that all subscribers have consumed are deleted.
        Args:
            topic_name (str): The name of the topic to clean up.
        Returns:
            int: Number of messages removed from the topic.
        """
        try:
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            topic_owner = self.redis.hget(metadata_key, "owner")
            
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            subscribers = [s for s in self.redis.smembers(subscribers_key)]
            
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offsets = {k: int(v) for k, v in self.redis.hgetall(offset_key).items()}
            
            non_owner_offsets = {}
            for sub_key, offset in offsets.items():
                subscriber = sub_key.split(':')[-1]
                if limpiar_user(subscriber) != limpiar_user(topic_owner):
                    non_owner_offsets[subscriber] = offset
            
            if not non_owner_offsets:
                return 0
            
            min_offset = min(non_owner_offsets.values()) if non_owner_offsets else 0
            
            processed_count = int(self.redis.hget(metadata_key, "processed_count") or 0)
            
            messages_to_remove = min_offset - processed_count
            
            if messages_to_remove <= 0:
                return 0
                
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            for _ in range(messages_to_remove):
                self.redis.lpop(messages_key)
                
            self.redis.hset(metadata_key, "processed_count", min_offset)
            
            logger.info(f"Removed {messages_to_remove} processed messages from topic '{topic_name}'")
            return messages_to_remove
            
        except Exception as e:
            logger.exception(f"Error cleaning up messages from topic '{topic_name}'")
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
            metadata = {k: v for k, v in self.redis.hgetall(metadata_key).items()}
            
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            subscribers = [s for s in self.redis.smembers(subscribers_key)]
            
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            message_count = self.redis.llen(messages_key)
            
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offsets = {k: int(v) for k, v in self.redis.hgetall(offset_key).items()}
            
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

        except Exception as e:
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
                    MOMTopicStatus.NOT_SUBSCRIBED,
                    "Only the topic owner can delete it",
                )

            # Delete all topic-related keys
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)
            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            messages_key = TopicKeyBuilder.messages_key(topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            
            self.redis.delete(metadata_key, subscribers_key, messages_key, offset_key)
            
            return TopicOperationResult(
                True,
                MOMTopicStatus.SUBSCRIPTION_DELETED,
                f"Topic {topic_name} deleted successfully",
            )

        except Exception as e:
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
            topic_pattern = f"{TopicKeyBuilder.TOPIC_PREFIX}:*:{TopicKeyBuilder.SUBSCRIBERS_SUFFIX}"
            subscriber_keys = self.redis.keys(topic_pattern)
            
            subscribed_topics = []
            for key in subscriber_keys:
                topic_name = key.split(':')[2]
                
                if self.redis.sismember(key, self.user):
                    subscribed_topics.append(topic_name)
            
            return TopicOperationResult(
                True,
                MOMTopicStatus.SUBSCRIPTION_CREATED,
                {"subscribed_topics": subscribed_topics},
            )

        except Exception as e:
            logger.exception("Error fetching user topics")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )