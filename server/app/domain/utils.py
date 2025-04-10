"""
Utils for MOM
"""

from app.domain.models import QueueOperationResult, MOMQueueStatus
from app.domain.logger_config import logger

class KeyBuilder:
    """
    Class for building repetitive keys
    """
    QUEUE_PREFIX = "mom:queues"
    METADATA_SUFFIX = "metadata"
    SUBSCRIBERS_SUFFIX = "subscribers"

    @classmethod
    def queue_key(cls, name: str) -> str:
        return f"{cls.QUEUE_PREFIX}:{name}"

    @classmethod
    def metadata_key(cls, name: str) -> str:
        return f"{cls.queue_key(name)}:{cls.METADATA_SUFFIX}"

    @classmethod
    def subscribers_key(cls, name: str) -> str:
        return f"{cls.queue_key(name)}:{cls.SUBSCRIBERS_SUFFIX}"

def handle_redis_errors(log_message: str):
    """
    This wrapper executes an operation over the database that might fail
    Args:
      log_message: A message for write on the log file.

    Returns:
      QueueOperationResult: With the information of the operation.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e: # pylint: disable=W0718
                logger.exception(log_message)
                return QueueOperationResult(
                    success = False,
                    status = MOMQueueStatus.INTERNAL_ERROR,
                    details = str(e)
                )
        return wrapper
    return decorator

class TopicKeyBuilder:
    """
    Utility class for building Redis keys for topic-related operations
    """
    TOPIC_PREFIX = "mom:topics"
    METADATA_SUFFIX = "metadata"
    SUBSCRIBERS_SUFFIX = "subscribers"
    MESSAGES_SUFFIX = "messages"
    SUBSCRIBER_OFFSETS_SUFFIX = "offsets"

    @classmethod
    def topic_key(cls, name: str) -> str:
        return f"{cls.TOPIC_PREFIX}:{name}"

    @classmethod
    def metadata_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.METADATA_SUFFIX}"

    @classmethod
    def subscribers_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.SUBSCRIBERS_SUFFIX}"

    @classmethod
    def messages_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.MESSAGES_SUFFIX}"

    @classmethod
    def subscriber_offsets_key(cls, topic_name: str) -> str:
        return f"{cls.topic_key(topic_name)}:{cls.SUBSCRIBER_OFFSETS_SUFFIX}"

    @classmethod
    def subscriber_offset_field(cls, subscriber: str) -> str:
        return f"subscriber_offset:{subscriber}"

def limpiar_user(texto):
    texto = texto.replace("'", "")
    texto = texto.replace("[", "").replace("]", "")
    return texto
