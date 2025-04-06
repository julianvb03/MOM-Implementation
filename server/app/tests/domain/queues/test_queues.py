"""
Test cases for the MOMQueueManager class
"""

from app.adapters.db import Database
from app.adapters.factory import ObjectFactory

import json
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.domain.models import MOMQueueStatus, QueueOperationResult
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.utils import KeyBuilder
from app.domain.queues.queues_subscription import SubscriptionService
from app.domain.queues.queues_validator import QueueValidator


# Erase Redis data before each test
@pytest.fixture(autouse=True)
async def clear_redis():
    """Clear Redis database before and after each test"""
    db = ObjectFactory.get_instance(Database)
    client = db.get_client()
    client.flushdb()
    yield
    # Cleanup after tests
    client.flushdb()


@pytest.fixture(name="redis_connection")
def redis_connection_fixture():
    """Fixture to provide Redis connection"""
    db = ObjectFactory.get_instance(Database)
    return db.get_client()


@pytest.fixture(name="queue_manager")
def queue_manager_fixture(redis_connection):
    """Fixture to provide an instance of MOMQueueManager"""
    return MOMQueueManager(redis_connection, "test_user")


@pytest.fixture(name="queue_manager_alt")
def queue_manager_alt_fixture(redis_connection):
    """Fixture to provide an alternate user instance of MOMQueueManager"""
    return MOMQueueManager(redis_connection, "alt_user")

class TestMOMQueueManager:
    """Test suite for MOMQueueManager class"""

    @pytest.fixture
    def setup(self):
        """Fixture to initialize test environment for MOMQueueManager"""
        self.redis_mock = MagicMock()
        self.user = "test_user"
        self.queue_manager = MOMQueueManager(self.redis_mock, self.user)
        # Mock dependencies
        self.queue_manager.subscriptions = MagicMock(spec=SubscriptionService)
        self.queue_manager.validator = MagicMock(spec=QueueValidator)
        
        # Common test variables
        self.queue_name = "test_queue"
        self.queue_key = KeyBuilder.queue_key(self.queue_name)
        self.metadata_key = KeyBuilder.metadata_key(self.queue_name)
        self.subscribers_key = KeyBuilder.subscribers_key(self.queue_name)

    def test_create_queue_success(self, setup):
        """Test successful queue creation"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        self.queue_manager.subscriptions.subscribe.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User subscribed"
        )

        # Execute
        result = self.queue_manager.create_queue(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.QUEUE_CREATED
        self.redis_mock.hset.assert_called_once()
        self.queue_manager.subscriptions.subscribe.assert_called_once_with(self.queue_name)

    def test_create_queue_already_exists(self, setup):
        """Test queue creation when queue already exists"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )

        # Execute
        result = self.queue_manager.create_queue(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        self.redis_mock.hset.assert_not_called()
        self.queue_manager.subscriptions.subscribe.assert_not_called()

    def test_create_queue_invalid_message_limit(self, setup):
        """Test queue creation with invalid message limit"""
        # Execute with limits out of range
        result_too_small = self.queue_manager.create_queue(self.queue_name, message_limit=0)
        result_too_large = self.queue_manager.create_queue(self.queue_name, message_limit=2**32)

        # Verify
        assert result_too_small.success is False
        assert result_too_small.status == MOMQueueStatus.INVALID_ARGUMENTS
        assert result_too_large.success is False
        assert result_too_large.status == MOMQueueStatus.INVALID_ARGUMENTS

    def test_create_queue_subscription_failure(self, setup):
        """Test queue creation with subscription failure"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        self.queue_manager.subscriptions.subscribe.return_value = QueueOperationResult(
            False, MOMQueueStatus.INTERNAL_ERROR, "Subscription failed"
        )

        # Execute
        result = self.queue_manager.create_queue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        self.redis_mock.delete.assert_called_once_with(self.metadata_key, self.queue_key)

    def test_create_queue_exception(self, setup):
        """Test queue creation with exception"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.side_effect = Exception("Test exception")

        # Execute
        result = self.queue_manager.create_queue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        assert "Test exception" in result.details

    def test_enqueue_success(self, setup):
        """Test successful message enqueue"""
        # Setup
        message = "test message"
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        
        # Execute
        expected_time = datetime(2025, 4, 5, 12, 0, 0, tzinfo=timezone.utc)

        with patch('app.domain.queues.queues_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = expected_time
            result = self.queue_manager.enqueue(message, self.queue_name)


        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        self.redis_mock.rpush.assert_called_once()
        self.redis_mock.hincrby.assert_called_once_with(self.metadata_key, "total_messages", 1)

    def test_enqueue_queue_not_exists(self, setup):
        """Test message enqueue when queue does not exist"""
        # Setup
        message = "test message"
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        
        # Execute
        result = self.queue_manager.enqueue(message, self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST
        self.redis_mock.rpush.assert_not_called()
        self.redis_mock.hincrby.assert_not_called()

    def test_enqueue_exception(self, setup):
        """Test message enqueue with exception"""
        # Setup
        message = "test message"
        self.queue_manager.validator.validate_queue_exists.side_effect = Exception("Test exception")
        
        # Execute
        result = self.queue_manager.enqueue(message, self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        assert "Test exception" in result.details

    def test_dequeue_success(self, setup):
        """Test successful message dequeue"""
        # Setup
        expected_message = "dequeued message"
        message_json = json.dumps({
            "id": "message-id",
            "timestamp": "2025-04-05T12:00:00Z",
            "payload": json.dumps(expected_message)
        })
        
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        self.redis_mock.lpop.return_value = message_json
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        assert result.details == expected_message
        self.redis_mock.hincrby.assert_called_once_with(self.metadata_key, "total_messages", -1)

    def test_dequeue_blocking(self, setup):
        """Test blocking dequeue operation"""
        # Setup
        expected_message = "dequeued message"
        message_json = json.dumps({
            "id": "message-id",
            "timestamp": "2025-04-05T12:00:00Z",
            "payload": json.dumps(expected_message)
        })
        
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        self.redis_mock.blpop.return_value = (self.queue_key, message_json)
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name, block=True, timeout=1)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        assert result.details == expected_message
        self.redis_mock.blpop.assert_called_once_with(self.queue_key, timeout=1)
        self.redis_mock.hincrby.assert_called_once_with(self.metadata_key, "total_messages", -1)

    def test_dequeue_empty(self, setup):
        """Test dequeue from empty queue"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        self.redis_mock.lpop.return_value = None
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.EMPTY_QUEUE
        self.redis_mock.hincrby.assert_not_called()

    def test_dequeue_blocking_timeout(self, setup):
        """Test blocking dequeue with timeout"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        self.redis_mock.blpop.return_value = None
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name, block=True, timeout=1)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.EMPTY_QUEUE
        self.redis_mock.hincrby.assert_not_called()

    def test_dequeue_queue_not_exists(self, setup):
        """Test dequeue when queue does not exist"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST
        self.redis_mock.lpop.assert_not_called()
        self.redis_mock.hincrby.assert_not_called()

    def test_dequeue_not_subscribed(self, setup):
        """Test dequeue when user is not subscribed"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            False, MOMQueueStatus.INVALID_ARGUMENTS, "User is not subscribed"
        )
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INVALID_ARGUMENTS
        self.redis_mock.lpop.assert_not_called()
        self.redis_mock.hincrby.assert_not_called()

    def test_dequeue_exception(self, setup):
        """Test dequeue with exception"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.side_effect = Exception("Test exception")
        
        # Execute
        result = self.queue_manager.dequeue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        assert "Test exception" in result.details

    def test_get_queue_info_success(self, setup):
        """Test successful queue info retrieval"""
        # Setup
        queue_metadata = {
            b"name": b"test_queue",
            b"owner": b"test_user",
            b"created_at": b"2025-04-05T12:00:00",
            b"total_messages": b"0"
        }
        
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        self.redis_mock.hgetall.return_value = queue_metadata
        
        # Execute
        result = self.queue_manager.get_queue_info(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        # Check that all metadata is in the result details
        for key, value in queue_metadata.items():
            assert key.decode('utf-8') in result.details
            assert value.decode('utf-8') in result.details

    def test_get_queue_info_queue_not_exists(self, setup):
        """Test queue info retrieval when queue does not exist"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        
        # Execute
        result = self.queue_manager.get_queue_info(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST
        self.redis_mock.hgetall.assert_not_called()

    def test_get_queue_info_not_subscribed(self, setup):
        """Test queue info retrieval when user is not subscribed"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_subscribed.return_value = QueueOperationResult(
            False, MOMQueueStatus.INVALID_ARGUMENTS, "User is not subscribed"
        )
        
        # Execute
        result = self.queue_manager.get_queue_info(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INVALID_ARGUMENTS
        self.redis_mock.hgetall.assert_not_called()

    def test_get_queue_info_exception(self, setup):
        """Test queue info retrieval with exception"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.side_effect = Exception("Test exception")
        
        # Execute
        result = self.queue_manager.get_queue_info(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        assert "Test exception" in result.details

    def test_delete_queue_success(self, setup):
        """Test successful queue deletion"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_is_owner.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is owner"
        )
        
        # Execute
        result = self.queue_manager.delete_queue(self.queue_name)

        # Verify
        assert result.success is True
        assert result.status == MOMQueueStatus.SUCCES_OPERATION
        self.redis_mock.delete.assert_called_once_with(
            self.queue_key, self.metadata_key, self.subscribers_key
        )

    def test_delete_queue_not_exists(self, setup):
        """Test queue deletion when queue does not exist"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            False, MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST, "Queue does not exist"
        )
        
        # Execute
        result = self.queue_manager.delete_queue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.METADATA_OR_QUEUE_NOT_EXIST
        self.redis_mock.delete.assert_not_called()

    def test_delete_queue_not_owner(self, setup):
        """Test queue deletion when user is not the owner"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        self.queue_manager.validator.validate_user_is_owner.return_value = QueueOperationResult(
            False, MOMQueueStatus.INVALID_ARGUMENTS, "User is not owner"
        )
        
        # Execute
        result = self.queue_manager.delete_queue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INVALID_ARGUMENTS
        self.redis_mock.delete.assert_not_called()

    def test_delete_queue_exception(self, setup):
        """Test queue deletion with exception"""
        # Setup
        self.queue_manager.validator.validate_queue_exists.side_effect = Exception("Test exception")
        
        # Execute
        result = self.queue_manager.delete_queue(self.queue_name)

        # Verify
        assert result.success is False
        assert result.status == MOMQueueStatus.INTERNAL_ERROR
        assert "Test exception" in result.details

    @pytest.mark.asyncio
    async def test_multiple_users_enqueue_and_dequeue(redis_connection, queue_manager, queue_manager_alt):
        """Test multiple users interacting with the same queue"""

        queue_name = "shared_queue"
        
        # test_user crea la cola
        result_create = queue_manager.create_queue(queue_name)
        assert result_create.success

        # alt_user se suscribe manualmente (mocking interno asumido)
        queue_manager_alt.subscriptions = MagicMock(spec=SubscriptionService)
        queue_manager_alt.validator = MagicMock(spec=QueueValidator)
        queue_manager_alt.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        queue_manager_alt.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )
        queue_manager.redis.sadd(KeyBuilder.subscribers_key(queue_name), "alt_user")

        # test_user envía un mensaje
        msg1 = "Hello from test_user"
        result_enqueue_1 = queue_manager.enqueue(msg1, queue_name)
        assert result_enqueue_1.success
        
        # alt_user saca el mensaje
        queue_manager_alt.redis = queue_manager.redis
        result_dequeue_1 = queue_manager_alt.dequeue(queue_name)
        assert result_dequeue_1.success
        assert result_dequeue_1.details == msg1

    @pytest.mark.asyncio
    async def test_alt_user_not_subscribed(redis_connection, queue_manager, queue_manager_alt):
        """Test alt_user cannot dequeue without subscription"""
        
        queue_name = "queue_for_subscription_check"
        
        # test_user crea la cola
        result_create = queue_manager.create_queue(queue_name)
        assert result_create.success

        # test_user hace enqueue
        queue_manager.enqueue("message 1", queue_name)

        # alt_user intenta hacer dequeue sin suscripción
        queue_manager_alt.validator = MagicMock(spec=QueueValidator)
        queue_manager_alt.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        queue_manager_alt.validator.validate_user_subscribed.return_value = QueueOperationResult(
            False, MOMQueueStatus.INVALID_ARGUMENTS, "User is not subscribed"
        )

        result = queue_manager_alt.dequeue(queue_name)
        assert result.success is False
        assert result.status == MOMQueueStatus.INVALID_ARGUMENTS

    @pytest.mark.asyncio
    async def test_multiple_users_enqueue_fifo(redis_connection, queue_manager, queue_manager_alt):
        """Test FIFO order preserved with multiple users enqueueing"""

        queue_name = "fifo_test_queue"
        
        queue_manager.create_queue(queue_name)
        queue_manager.redis.sadd(KeyBuilder.subscribers_key(queue_name), "alt_user")

        queue_manager_alt.validator = MagicMock(spec=QueueValidator)
        queue_manager_alt.validator.validate_queue_exists.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "Queue exists"
        )
        queue_manager_alt.validator.validate_user_subscribed.return_value = QueueOperationResult(
            True, MOMQueueStatus.SUCCES_OPERATION, "User is subscribed"
        )

        queue_manager.enqueue("msg from test_user", queue_name)
        queue_manager_alt.enqueue("msg from alt_user", queue_name)

        msg1 = queue_manager.dequeue(queue_name)
        msg2 = queue_manager.dequeue(queue_name)

        assert msg1.details == "msg from test_user"
        assert msg2.details == "msg from alt_user"
