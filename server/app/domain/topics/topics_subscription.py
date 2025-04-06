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

class TopicSubscriptionService:
    """
    Service for managing topic subscriptions
    """
    def __init__(self, redis, user: str):
        self.redis = redis
        self.user = user
        self.validator = TopicValidator(redis, user)

    def subscribe(self, topic_name: str) -> TopicOperationResult:
        """
        Subscribe the user to a topic.
        Args:
            topic_name (str): The name of the topic to subscribe to.
        Returns:
            TopicOperationResult: Result of the subscription operation.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            result = self.validator.validate_user_subscribed(topic_name)
            if result.success:
                return TopicOperationResult(
                    False,
                    MOMTopicStatus.ALREADY_SUBSCRIBED,
                    f"User {self.user} is already subscribed to topic {topic_name}", # pylint: disable=C0301
                )

            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            self.redis.sadd(subscribers_key, self.user)

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(self.user)
            metadata_key = TopicKeyBuilder.metadata_key(topic_name)

            current_index = self.redis.hget(metadata_key, "message_count")

            initial_offset = int(current_index) if current_index is not None else 0 # pylint: disable=C0301

            self.redis.hset(offset_key, offset_field, initial_offset)

            return TopicOperationResult(
                True,
                MOMTopicStatus.SUBSCRIPTION_CREATED,
                f"User {self.user} subscribed to topic {topic_name}",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception(f"Error subscribing to topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )

    def unsubscribe(self, topic_name: str) -> TopicOperationResult:
        """
        Unsubscribe the user from a topic.
        Args:
            topic_name (str): The name of the topic to unsubscribe from.
        Returns:
            TopicOperationResult: Result of the unsubscription operation.
        """
        try:
            result = self.validator.validate_topic_exists(topic_name)
            if not result.success:
                return result

            result = self.validator.validate_user_is_owner(topic_name)
            if result.success:
                return TopicOperationResult(
                    False,
                    MOMTopicStatus.ALREADY_SUBSCRIBED,
                    "User is the owner of the topic and cannot unsubscribe",
                )

            result = self.validator.validate_user_subscribed(topic_name)
            if not result.success:
                return result

            subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
            self.redis.srem(subscribers_key, self.user)

            offset_key = TopicKeyBuilder.subscriber_offsets_key(topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(self.user)
            self.redis.hdel(offset_key, offset_field)

            return TopicOperationResult(
                True,
                MOMTopicStatus.SUBSCRIPTION_DELETED,
                f"User {self.user} unsubscribed from topic {topic_name}",
            )

        except Exception as e: # pylint: disable=W0718
            logger.exception(f"Error unsubscribing from topic '{topic_name}'")
            return TopicOperationResult(
                False, MOMTopicStatus.TOPIC_NOT_EXIST, str(e)
            )
