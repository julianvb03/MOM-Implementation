import json
from zookeeper.zk_utils import get_redis_connection

REGISTRY_KEY = "zookeeper:queue_topic_registry"

def register_queue_or_topic(name: str, type_: str, operation: str, origin_node: str, replica_nodes: list[str]):
    """
    Stores or deletes a queue/topic entry in Redis.

    Args:
        name (str): Name of the queue or topic.
        type_ (str): Either "queue" or "topic".
        operation (str): Either "create" or "delete".
        origin_node (str): The primary MOM node.
        replica_nodes (list): Backup MOM nodes.
    """
    redis = get_redis_connection()

    entry = {
        "name": name,
        "type": type_,
        "operation": operation,
        "origin_node": origin_node,
        "replica_nodes": replica_nodes
    }

    if operation == "create":
        redis.hset(REGISTRY_KEY, name, json.dumps(entry))
    elif operation == "delete":
        redis.hdel(REGISTRY_KEY, name)

def get_queue_topic_info(name: str):
    """Retrieve the registry info for a queue/topic by name."""
    redis = get_redis_connection()
    raw = redis.hget(REGISTRY_KEY, name)
    return json.loads(raw) if raw else None

def list_registered_queue_topics():
    """Returns all registered queues/topics with full info."""
    redis = get_redis_connection()
    all_entries = redis.hgetall(REGISTRY_KEY)
    return {k: json.loads(v) for k, v in all_entries.items()}
