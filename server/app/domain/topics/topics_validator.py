from datetime import datetime
from models import TopicOperationResult, MOMTopicStatus
from utils import TopicKeyBuilder

class TopicValidator:
    """
    Validator for topic operations
    """
    def __init__(self, redis, user):
        self.redis = redis
        self.user = user

    def validate_topic_exists(self, topic_name: str) -> TopicOperationResult:
        """
        Validate if the topic exists in Redis.
        Args:
            topic_name (str): The name of the topic to validate.
        Returns:
            TopicOperationResult: Result of the validation.
        """
        metadata_key = TopicKeyBuilder.metadata_key(topic_name)
        if not self.redis.exists(metadata_key):
            return TopicOperationResult(
                False,
                MOMTopicStatus.TOPIC_NOT_EXIST,
                f"Topic {topic_name} does not exist",
            )

        return TopicOperationResult(
            True, MOMTopicStatus.TOPIC_EXISTS, "Topic exists"
        )

    def validate_user_subscribed(self, topic_name: str) -> TopicOperationResult:
        """
        Validate if the user is subscribed to the topic.
        Args:
            topic_name (str): The name of the topic to validate.
        Returns:
            TopicOperationResult: Result of the validation.
        """
        subscribers_key = TopicKeyBuilder.subscribers_key(topic_name)
        if not self.redis.sismember(subscribers_key, self.user):
            return TopicOperationResult(
                False,
                MOMTopicStatus.NOT_SUBSCRIBED,
                f"User {self.user} is not subscribed to topic {topic_name}",
            )

        return TopicOperationResult(
            True, MOMTopicStatus.ALREADY_SUBSCRIBED, "User is subscribed"
        )

    def validate_user_is_owner(self, topic_name: str) -> TopicOperationResult:
        """
        Validate if the user is the owner of the topic.
        Args:
            topic_name (str): The name of the topic to validate.
        Returns:
            TopicOperationResult: Result of the validation.
        """
        metadata_key = TopicKeyBuilder.metadata_key(topic_name)
        owner = self.redis.hget(metadata_key, "owner")
        if owner and owner.decode() != self.user:
            return TopicOperationResult(
                False,
                MOMTopicStatus.NOT_SUBSCRIBED,
                "Operation not allowed for non-owner",
            )

        return TopicOperationResult(
            True, MOMTopicStatus.SUBSCRIPTION_CREATED, "User is owner"
        )
