"""
Test cases for the MOMTopicManager class
"""

from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
import redis
import os

import json
import pytest
import time
from datetime import datetime, timedelta
from app.domain.models import MOMTopicStatus 
from app.domain.topics.topics_manager import MOMTopicManager
from app.domain.utils import TopicKeyBuilder


# Erase Redis data before each test
# @pytest.fixture(autouse=True)
# def clear_redis():
#     """Clear Redis database before and after each test"""
#     db = ObjectFactory.get_instance(Database)
#     client = db.get_client()
#     client.flushdb()  # Before test
#     yield
#     client.flushdb()  # After test

REDIS2_CONFIG = {
    'host': 'localhost',
    'port': 6380,
    'password': os.getenv('REDIS_PASSWORD'),
    'decode_responses': True
}

def create_redis2_connection():
    """Crea y retorna una conexión a redis2"""
    try:
        r = redis.Redis(**REDIS2_CONFIG)
        if r.ping():
            print("Conexión exitosa a redis2")
            return r
        raise ConnectionError("No se pudo conectar a redis2")
    except redis.AuthenticationError:
        print("Error de autenticación. Verifica la contraseña")
        return None
    except redis.ConnectionError:
        print("No se pudo conectar a redis2. Verifica si el servicio está corriendo")
        return None
    finally:
        r.close()

# @pytest.fixture(autouse=True)
# def create_redis2_connection_fixture():
#     """Fixture to provide a connection to redis2"""
#     db = create_redis2_connection()
#     db.flushdb()
#     yield db
#     db.flushdb()


@pytest.fixture(name="redis_connection")
def redis_connection_fixture():
    """Fixture to provide Redis connection"""
    db = ObjectFactory.get_instance(Database)
    return db.get_client()


@pytest.fixture(name="topic_manager")
def topic_manager_fixture(redis_connection):
    """Fixture to provide an instance of MOMTopicManager"""
    return MOMTopicManager(redis_connection, "test_user")


@pytest.fixture(name="topic_manager_alt")
def topic_manager_alt_fixture(redis_connection):
    """Fixture to provide an alternate user instance of MOMTopicManager"""
    return MOMTopicManager(redis_connection, "alt_user")

@pytest.fixture(name="topic_manager_alt2") 
def topic_manager_alt2_fixture(redis_connection): 
    """Fixture to provide an alternate user instance of MOMTopicManager""" 
    return MOMTopicManager(redis_connection, "alt_user2")

@pytest.fixture(name="user_managers")
def user_managers_fixture(redis_connection):
    """Fixture to provide multiple user instances of MOMTopicManager"""
    return [
        MOMTopicManager(redis_connection, f"user_{i}")
        for i in range(5)  # Create 5 different user managers
    ]

## Test for the subscription and unsubscription of a topic
def test_unsubscribe_creator_form_his_topic(topic_manager):
    """Test unsubscribing the creator from his topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name=topic_name)
    
    print("data oif response {topic.success} {topic.status} {topic.details}")
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    topic = topic_manager.subscriptions.unsubscribe(topic_name)
    assert topic is not None
    assert topic.success == False
    assert topic.status == MOMTopicStatus.ALREADY_SUBSCRIBED
    assert topic.details == "User is the owner of the topic and cannot unsubscribe"

def test_subscribe_to_topic(topic_manager, topic_manager_alt):
    """Test subscribing to a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    topic = topic_manager_alt.subscriptions.subscribe(topic_name)
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert topic.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

def test_unsubscribe_to_topic(topic_manager, topic_manager_alt):
    """Test unsubscribing from a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    topic = topic_manager_alt.subscriptions.subscribe(topic_name)
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert topic.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Unsubscribe from the topic
    result = topic_manager_alt.subscriptions.unsubscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_DELETED
    assert result.details == f"User {topic_manager_alt.user} unsubscribed from topic {topic_name}"

def test_subscribe_already_subscribed(topic_manager, topic_manager_alt):
    """Test subscribing to a topic when already subscribed"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Subscribe to the topic
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert result.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Try to subscribe again
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == False
    assert result.status == MOMTopicStatus.ALREADY_SUBSCRIBED
    assert result.details == f"User {topic_manager_alt.user} is already subscribed to topic {topic_name}"

def test_unsubscribe_already_unsubscribed(topic_manager, topic_manager_alt):
    """Test unsubscribing from a topic when already unsubscribed"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Subscribe to the topic
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert result.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Unsubscribe from the topic
    result = topic_manager_alt.subscriptions.unsubscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_DELETED
    assert result.details == f"User {topic_manager_alt.user} unsubscribed from topic {topic_name}"

    # Try to unsubscribe again
    result = topic_manager_alt.subscriptions.unsubscribe(topic_name)
    
    assert result is not None
    assert result.success == False
    assert result.status == MOMTopicStatus.NOT_SUBSCRIBED
    assert result.details == f"User {topic_manager_alt.user} is not subscribed to topic {topic_name}"

## Tests for the creation and deletion of a topic  
def test_create_topic(topic_manager, redis_connection):
    """Test creating a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)

    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Check if the topic metadata, subscribers, and messages keys exist in Redis
    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))
    #status3 = redis_connection.exists(TopicKeyBuilder.messages_key(topic_name))

    assert status1 == 1
    assert status2 == 1

def test_recreate_topic(topic_manager, redis_connection):
    """Test recreating a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    topic = topic_manager.create_topic(topic_name)
    assert topic is not None
    assert topic.success == False
    assert topic.status == MOMTopicStatus.TOPIC_EXISTS
    assert topic.details == "Topic exists"

    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))

    assert status1 == 1
    assert status2 == 1

def test_delete_topic(topic_manager, redis_connection):
    """Test deleting a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))

    assert status1 == 1
    assert status2 == 1

    # Delete the topic
    result = topic_manager.delete_topic(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.TOPIC_DELETED
    assert result.details == f"Topic deleted successfully"

    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))

    assert status1 == 0
    assert status2 == 0

def test_delete_the_topic_of_other(topic_manager, topic_manager_alt, redis_connection):
    """Test deleting the topic of another user"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))
    assert status1 == 1
    assert status2 == 1

    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    # Try to delete the topic as another user
    result = topic_manager_alt.delete_topic(topic_name)
    
    assert result is not None
    assert result.success == False
    assert result.status == MOMTopicStatus.INVALID_ARGUMENTS
    assert result.details == "Only the topic owner can delete it"

    status1 = redis_connection.exists(TopicKeyBuilder.metadata_key(topic_name))
    status2 = redis_connection.exists(TopicKeyBuilder.subscribers_key(topic_name))
    assert status1 == 1
    assert status2 == 1

def test_publis_message(topic_manager, redis_connection):
    """Test publishing a message to a topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Publish a message to the topic
    message = "Hello, World!"
    result = topic_manager.publish(message, topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
    assert result.details == f"Message published to topic {topic_name}"

    # Check if the message is stored in Redis
    messages_key = TopicKeyBuilder.messages_key(topic_name)
    messages = redis_connection.lrange(messages_key, 0, -1)
    
    assert messages is not None
    assert len(messages) == 1

def tests_publis_message_to_nonexistent_topic(topic_manager):
    """Test publishing a message to a nonexistent topic"""
    topic_name = "nonexistent_topic"
    message = "Hello, World!"
    
    result = topic_manager.publish(message, topic_name)
    
    assert result is not None
    assert result.success == False
    assert result.status == MOMTopicStatus.TOPIC_NOT_EXIST
    assert result.details == f"Topic {topic_name} does not exist"

def test_publish_message_in_a_topic_user_not_subscribed(topic_manager, topic_manager_alt, redis_connection):
    """Test publishing a message to a topic when the user is not subscribed"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Publish a message to the topic
    message = "Hello, World!"
    result = topic_manager_alt.publish(message, topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
    assert result.details == f"Message published to topic {topic_name}"

    # Check if the message is stored in Redis
    messages_key = TopicKeyBuilder.messages_key(topic_name)
    messages = redis_connection.lrange(messages_key, 0, -1)
    assert messages is not None
    assert len(messages) == 1

    # Check that the user not subscribed to the topic
    result = topic_manager_alt.subscriptions.unsubscribe(topic_name)
    assert result is not None
    assert result.success == False
    assert result.status == MOMTopicStatus.NOT_SUBSCRIBED
    assert result.details == f"User {topic_manager_alt.user} is not subscribed to topic {topic_name}"

def test_consume_my_own_messages(topic_manager, redis_connection):
    """Test consuming my own messages"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Publish a message to the topic
    message = "Hello, World!"
    result = topic_manager.publish(message, topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
    assert result.details == f"Message published to topic {topic_name}"

    # Consume the message from the topic
    result = topic_manager.consume(topic_name)

    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.NO_MESSAGES
    assert result.details == f"No new messages"

    # Eciste el mensaje pero no se puede consumir, ya que es el creador
    # Check if the message is still stored in Redis
    result1 = redis_connection.lrange(TopicKeyBuilder.messages_key(topic_name), 0, -1)
    assert result1 is not None
    assert len(result1) == 1

def test_consume_message_of_other_when_was_published_in_the_past(topic_manager, topic_manager_alt, redis_connection):
    """Test consuming a message from another user, but published in the past
        then it is not possible to consume it"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Publish a message to the topic
    message = "Hello, World!"
    result = topic_manager.publish(message, topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
    assert result.details == f"Message published to topic {topic_name}"

    # Subscribe to the topic as another user
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert result.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Consume the message from the topic as another user
    result = topic_manager_alt.consume(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.NO_MESSAGES
    assert result.details == f"No new messages"

    # Check if the message is still stored in Redis
    result1 = redis_connection.lrange(TopicKeyBuilder.messages_key(topic_name), 0, -1)
    assert result1 is not None
    assert len(result1) == 1

def test_consume_message_of_other(topic_manager, topic_manager_alt, redis_connection):
    """Test consuming a message from another user"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Subscribe to the topic as another user
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert result.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Publish a message to the topic
    message = "Hello, World!"
    result = topic_manager.publish(message, topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
    assert result.details == f"Message published to topic {topic_name}"

    # Consume the message from the topic as another user
    result = topic_manager_alt.consume(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.MESSAGE_CONSUMED
    assert result.details == message

    # Check if the message is still stored in Redis
    result1 = redis_connection.lrange(TopicKeyBuilder.messages_key(topic_name), 0, -1)
    assert result1 is not None
    assert len(result1) == 1

def test_consume_to_empty_topic(topic_manager, topic_manager_alt, redis_connection):
    """Test consuming from an empty topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
    assert topic is not None
    assert topic.success == True
    assert topic.status == MOMTopicStatus.TOPIC_CREATED
    assert topic.details == "Topic test_topic created successfully"

    # Subscribe to the topic as another user
    result = topic_manager_alt.subscriptions.subscribe(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    assert result.details == f"User {topic_manager_alt.user} subscribed to topic {topic_name}"

    # Consume from the empty topic
    result = topic_manager_alt.consume(topic_name)
    
    assert result is not None
    assert result.success == True
    assert result.status == MOMTopicStatus.NO_MESSAGES
    assert result.details == f"No new messages"

## Intensive tests

def test_multiple_publishers_and_consumers(redis_connection, topic_manager, user_managers):
    """
    Test scenario with multiple publishers posting to a topic and multiple consumers
    reading from it, verifying message consumption order and cleanup behavior.
    """
    topic_name = "multi_pub_sub_test"
    
    # Step 1: Create topic with the main test user
    result = topic_manager.create_topic(topic_name)
    assert result.success is True
    assert result.status == MOMTopicStatus.TOPIC_CREATED
    
    # Step 2: Subscribe all users to the topic
    for manager in user_managers:
        result = manager.subscriptions.subscribe(topic_name)
        assert result.success is True
        assert result.status == MOMTopicStatus.SUBSCRIPTION_CREATED
    
    # Step 3: Each user publishes multiple messages
    messages_by_user = {}
    total_messages = 0
    
    for i, manager in enumerate(user_managers):
        user_messages = []
        for j in range(10):  # Each user publishes 10 messages
            message = f"Message {j} from user_{i}"
            result = manager.publish(message, topic_name)
            assert result.success is True
            assert result.status == MOMTopicStatus.MESSAGE_PUBLISHED
            user_messages.append(message)
            total_messages += 1
        messages_by_user[f"user_{i}"] = user_messages
    
    # Add some messages from the topic owner too
    owner_messages = []
    for j in range(5):
        message = f"Message {j} from test_user (owner)"
        result = topic_manager.publish(message, topic_name)
        assert result.success is True
        owner_messages.append(message)
        total_messages += 1
    
    # Verify topic info shows correct message count
    result = topic_manager.get_topic_info(topic_name)
    assert result.success is True
    assert result.details["messages_in_queue"] == total_messages
    
    # Step 4: Each user consumes messages
    consumed_messages = {f"user_{i}": [] for i in range(5)}
    consumed_messages["test_user"] = []
    
    # Users read all messages
    for i, manager in enumerate(user_managers):
        # Each user will consume until they get NO_MESSAGES
        while True:
            result = manager.consume(topic_name)
            if result.status == MOMTopicStatus.NO_MESSAGES:
                break
            if result.status == MOMTopicStatus.MESSAGE_CONSUMED:
                consumed_messages[f"user_{i}"].append(result.details)
    
    # Topic owner also consumes messages
    while True:
        result = topic_manager.consume(topic_name)
        if result.status == MOMTopicStatus.NO_MESSAGES:
            break
        if result.status == MOMTopicStatus.MESSAGE_CONSUMED:
            consumed_messages["test_user"].append(result.details)
    
    # Verify each user received all messages except their own
    for i in range(5):
        user_id = f"user_{i}"
        # Each user should not see their own messages
        for msg in consumed_messages[user_id]:
            assert f"from {user_id}" not in msg
        
        # Users should see messages from all other users
        expected_message_count = total_messages - len(messages_by_user[user_id])
        assert len(consumed_messages[user_id]) == expected_message_count
    
    # Topic owner should not see their own messages either
    for msg in consumed_messages["test_user"]:
        assert "from test_user (owner)" not in msg
    assert len(consumed_messages["test_user"]) == total_messages - len(owner_messages)
    
    # Step 5: Check queue still contains all messages
    result = topic_manager.get_topic_info(topic_name)
    assert result.success is True
    assert result.details["messages_in_queue"] == total_messages
    
    # Step 6: Run cleanup and verify no messages were deleted
    # (since all subscribers have co nsumed their messages but messages remain for record)
    deleted_count = topic_manager._cleanup_processed_messages(topic_name)
    
    # All subscribers have read their messages, so the minimum offset should be the total count
    # of messages (as each has advanced past all messages)
    assert deleted_count == total_messages
    
    # Verify queue is now empty
    result = topic_manager.get_topic_info(topic_name)
    assert result.success is True

    # Verify that the numer of processed messages is now equal to the number of
    # message count of metadata
    metadata = result.details["metadata"]
    processed_count = int(metadata.get("processed_count", 0))
    assert 0 == result.details["messages_in_queue"]
    assert processed_count == deleted_count

def test_time_based_cleanup_with_lagging_consumers(redis_connection, topic_manager, user_managers, monkeypatch):
    """
    Test cleanup of messages based on time with some lagging consumers who
    haven't read all messages, verifying offset adjustments occur properly.
    """
    # Set a short persistence time for testing
    monkeypatch.setenv("PERSISTENCY_ON_TOPIC_TIME", "1")  # 1 minute
    
    topic_name = "time_cleanup_test"
    
    # Step 1: Create topic with the main test user
    result = topic_manager.create_topic(topic_name)
    assert result.success is True
    
    # Step 2: Subscribe only first 3 users to the topic
    active_subscribers = user_managers[:3]
    for manager in active_subscribers:
        result = manager.subscriptions.subscribe(topic_name)
        assert result.success is True
    
    # Step 3: Publish 50 messages to the topic
    for i in range(50):
        message = f"Test message {i}"
        result = topic_manager.publish(message, topic_name)
        assert result.success is True
    
    # Step 4: First user consumes all messages
    first_user = active_subscribers[0]
    consumed_by_first = []
    
    while True:
        result = first_user.consume(topic_name)
        if result.status == MOMTopicStatus.NO_MESSAGES:
            break
        if result.status == MOMTopicStatus.MESSAGE_CONSUMED:
            consumed_by_first.append(result.details)
    
    # Step 5: Second user consumes only half the messages
    second_user = active_subscribers[1]
    consumed_by_second = []
    
    for _ in range(25):  # Read only 25 messages
        result = second_user.consume(topic_name)
        if result.status == MOMTopicStatus.MESSAGE_CONSUMED:
            consumed_by_second.append(result.details)
    
    # Step 6: Third user doesn't consume any messages
    
    # Get offsets before cleanup
    info_result = topic_manager.get_topic_info(topic_name)
    offsets_before = info_result.details["subscriber_offsets"]
    
    # Step 7: Manipulate message timestamps to simulate older messages (for time-based cleanup)
    messages_key = TopicKeyBuilder.messages_key(topic_name)
    for i in range(20):
        message_json = redis_connection.lindex(messages_key, i)
        message_data = json.loads(message_json)
        # Establecer timestamp a 2 minutos atrás (como número)
        message_data["timestamp"] = (datetime.now() - timedelta(minutes=2)).timestamp()
        redis_connection.lset(messages_key, i, json.dumps(message_data))
    
    # Step 8: Run cleanup with time-based force
    deleted_count = topic_manager._cleanup_processed_messages(topic_name, force_cleanup_by_time=True)
    
    # Verify some messages were deleted due to time expiration
    assert deleted_count > 0
    assert deleted_count <= 20  # Should have deleted at most the first 20 messages
    
    # Step 9: Get updated offsets and verify they were adjusted for users who hadn't read those messages
    info_result = topic_manager.get_topic_info(topic_name)
    offsets_after = info_result.details["subscriber_offsets"]
    
    # First user should already have high offset (unaffected)
    # Second user might need adjustment if their offset was in the deleted range
    # Third user definitely needed adjustment as they hadn't read any messages
    
    # Check third user's offset was adjusted
    third_user_key = TopicKeyBuilder.subscriber_offset_field(active_subscribers[2].user)
    if third_user_key in offsets_before and third_user_key in offsets_after:
        assert offsets_after[third_user_key] >= deleted_count
    
    # Step 10: Try consuming messages with all users to verify consistency
    # First user should still see no new messages
    result = first_user.consume(topic_name)
    assert result.status == MOMTopicStatus.NO_MESSAGES
    
    # Second user should be able to continue consuming without issues
    result = second_user.consume(topic_name)
    assert result.status == MOMTopicStatus.MESSAGE_CONSUMED
    
    # Third user should be able to read messages starting after the deleted ones
    result = active_subscribers[2].consume(topic_name)
    assert result.status == MOMTopicStatus.MESSAGE_CONSUMED
    assert "Test message" in result.details
    # Message number should be >= deleted_count
    message_num = int(result.details.split("Test message ")[1])
    assert message_num >= deleted_count

def test_high_volume_publish_consume_with_periodic_cleanup(redis_connection, topic_manager, user_managers):
    """
    Test high volume scenario with periodic cleanups and multiple subscribers,
    verifying system integrity during high throughput operations.
    """
    topic_name = "high_volume_test"
    num_publishers = 3  # Use first 3 managers as publishers
    num_subscribers = 5  # All managers are subscribers
    messages_per_publisher = 100  # Each publisher sends 100 messages
    
    # Step 1: Create topic
    result = topic_manager.create_topic(topic_name)
    assert result.success is True
    
    # Step 2: Subscribe all users
    for manager in user_managers:
        result = manager.subscriptions.subscribe(topic_name)
        assert result.success is True
    
    # Step 3: High volume publishing in batches with periodic cleanups
    publishers = user_managers[:num_publishers]
    
    # Dictionary to track messages from each publisher
    published_messages = {f"user_{i}": [] for i in range(num_publishers)}
    
    # Publish in batches with periodic cleanup
    batch_size = 20
    for batch in range(messages_per_publisher // batch_size):
        # Each publisher sends a batch of messages
        for i, publisher in enumerate(publishers):
            for j in range(batch_size):
                message_id = batch * batch_size + j
                message = f"Publisher {i} - Message {message_id}"
                result = publisher.publish(message, topic_name)
                assert result.success is True
                published_messages[f"user_{i}"].append(message)
        
        # Some users consume messages between batches
        # Let's have users consume in round-robin fashion
        consuming_user = batch % len(user_managers)
        consumer = user_managers[consuming_user]
        
        # Each consumer reads a certain number of messages in this batch
        messages_to_consume = min(batch_size // 2, 5)  # Consume a fraction of the new messages
        for _ in range(messages_to_consume):
            result = consumer.consume(topic_name)
            # It's okay if we run out of messages
            if result.status != MOMTopicStatus.MESSAGE_CONSUMED:
                break
                
        # Run cleanup every other batch
        if batch % 2 == 1:
            deleted = topic_manager._cleanup_processed_messages(topic_name)
            # Record how many messages were cleaned up
            assert deleted >= 0  # May be 0 if minimum offset is still low
    
    # Step 4: Verify topic integrity
    info_result = topic_manager.get_topic_info(topic_name)
    assert info_result.success is True
    
    total_published = num_publishers * messages_per_publisher
    
    # Total messages in topic plus processed count should match total published
    message_count = info_result.details["messages_in_queue"]
    processed_count = int(info_result.details["metadata"].get(b"processed_count", 0))
    
    # Because of our cleanup operations, total message count may be less than published
    assert message_count + processed_count == total_published
    
    # Step 5: All subscribers consume remaining messages
    # Track consumed messages for verification
    consumed_messages = {user_managers[i].user: [] for i in range(len(user_managers))}
    
    for consumer in user_managers:
        while True:
            result = consumer.consume(topic_name)
            if result.status != MOMTopicStatus.MESSAGE_CONSUMED:
                break
            consumed_messages[consumer.user].append(result.details)
    
    # Step 6: Final cleanup should remove all messages
    deleted = topic_manager._cleanup_processed_messages(topic_name)
    
    # Verify cleanup removed remaining messages 
    # (as all users have consumed all messages they should)
    info_result = topic_manager.get_topic_info(topic_name)
    final_message_count = info_result.details["messages_in_queue"]
    final_processed_count = int(info_result.details["metadata"].get(b"processed_count", 0))
    
    # Either queue is empty or all messages are accounted for
    assert final_message_count == 0 or final_message_count + final_processed_count == total_published
    
    # Step 7: Verify each consumer received expected messages
    # Each consumer should receive all messages except those from themselves
    for i, consumer in enumerate(user_managers):
        user_id = consumer.user
        
        # Check that user didn't receive their own messages
        if i < num_publishers:
            own_publisher_prefix = f"Publisher {i} -"
            for message in consumed_messages[user_id]:
                assert own_publisher_prefix not in message