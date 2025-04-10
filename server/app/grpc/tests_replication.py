from app.domain.models import MOMTopicStatus 
from app.domain.topics.topics_manager import MOMTopicManager
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.utils import TopicKeyBuilder
import sys

from app.adapters.db import Database
from app.adapters.factory import ObjectFactory

db = ObjectFactory.get_instance(Database)
client = db.get_client()

def flush_redis():
    client.flushdb()

if __name__ == "__main__":

    try:
        n_test = int(sys.argv[1])
    except ValueError:
        sys.exit(1)
    
    if n_test is None:
        sys.exit(1)
    
    if n_test == 0:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.create_topic("test_topic")

    if n_test == 1:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.delete_topic("test_topic")

    if n_test == 2:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.publish("ADSFASDFAFASFAS", "test_topic")

    if n_test == 3:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.consume("test_topic")
    
    if n_test == 4:
        topic_manager = MOMTopicManager(client, "test_user2")
        result = topic_manager.subscriptions.subscribe("test_topic")

    if n_test == 5:
        topic_manager = MOMTopicManager(client, "test_user2")
        result = topic_manager.subscriptions.unsubscribe("test_topic")

    if n_test == 6:
        queue_manager = MOMQueueManager(client, "test_user")
        result = queue_manager.create_queue(queue_name="test_queue")

    if n_test == 7:
        queue_manager = MOMQueueManager(client, "test_user")
        result = queue_manager.delete_queue(queue_name="test_queue")

    if n_test == 8:
        queue_manager = MOMQueueManager(client, "user_random")
        result = queue_manager.subscriptions.subscribe("test_queue")

    if n_test == 9:
        queue_manager = MOMQueueManager(client, "user_random")
        result = queue_manager.subscriptions.unsubscribe("test_queue")
    
    if n_test == 10:
        queue_manager = MOMQueueManager(client, "test_user")
        result = queue_manager.enqueue("hola mia amor", "test_queue")

    if n_test == 11:
        queue_manager = MOMQueueManager(client, "user_random")
        result = queue_manager.dequeue("test_queue")

    if n_test == 12:
        queue_manager = MOMQueueManager(client, "test_user")
        result = queue_manager.dequeue("test_queue")

        
    print("Result Status: ", result.status, "Success:", result.status, "Details:", result.details, "Replication:", result.replication_result)
    #flush_redis()


#redis-cli -p 6379 -a ${REDIS_PASSWORD} KEYS "*test_topic*"
#redis-cli -p 6380 -a ${REDIS_PASSWORD} KEYS "*test_topic*"