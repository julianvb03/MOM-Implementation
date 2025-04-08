from app.domain.models import MOMTopicStatus 
from app.domain.topics.topics_manager import MOMTopicManager
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
        print("Error: El número de test debe ser un entero (0 o 1)")
        sys.exit(1)
    
    if n_test is None:
        print("Error: El número de test debe ser un entero (0 o 1)")
        sys.exit(1)
    
    if n_test == 0:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.create_topic("test_topic")

    if n_test == 1:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.delete_topic("test_topic")

    if n_test == 2:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.publish("test_message3", "test_topic")

    if n_test == 3:
        topic_manager = MOMTopicManager(client, "test_user")
        result = topic_manager.consume("test_topic")
        
    print("Result Status: ", result.status, "Success:", result.status, "Details:", result.details, "Replication:", result.replication_result)
    #flush_redis()


#redis-cli -p 6379 -a ${REDIS_PASSWORD} KEYS "*test_topic*"
#redis-cli -p 6380 -a ${REDIS_PASSWORD} KEYS "*test_topic*"