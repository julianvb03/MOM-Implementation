"""
Test cases for the MOMTopicManager class
"""

from app.adapters.db import Database
from app.adapters.factory import ObjectFactory

import json
import pytest
from datetime import datetime
from app.domain.models import MOMTopicStatus 
from app.domain.topics.topics_manager import MOMTopicManager
from app.domain.utils import TopicKeyBuilder


# Erase Redis data before each test
@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis database before and after each test"""
    db = ObjectFactory.get_instance(Database)
    client = db.get_client()
    client.flushdb()  # Before test
    yield
    client.flushdb()  # After test


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

## Test for the subscription and unsubscription of a topic
def test_unsubscribe_creator_form_his_topic(topic_manager):
    """Test unsubscribing the creator from his topic"""
    topic_name = "test_topic"
    topic = topic_manager.create_topic(topic_name)
    
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
    assert result.details == f"Topic test_topic deleted successfully"

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
    assert result.details == f"No new messages available for this subscription"

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
    assert result.details == f"No new messages available for this subscription"

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
    assert result.details == f"No new messages available for this subscription"

