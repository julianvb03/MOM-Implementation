import json
from datetime import datetime
from redis import Redis


def log_event(redis_client: Redis, event: str, origin: str, target: str = None, topics: list = None, notes: str = None):
    """
    Register a log event in Redis.
    Example use cases: node_down, publish_fail, sync_started, recovery
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "origin": origin,
        "target": target,
        "topics": topics,
        "notes": notes
    }
    redis_client.rpush("log:events", json.dumps(log_entry))
    print(f"[ZK_LOGGER] Logged event: {log_entry}")

def log_node_failure(node_id: str):
    """
    Example: register a node down event.
    """
    from redis import Redis
    import os
    import json
    from datetime import datetime

    redis = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "node_down",
        "origin": node_id
    }

    redis.rpush("log:events", json.dumps(log_entry))
    print(f"[ZK_LOGGER] Node failure logged: {log_entry}")


def log_topic_event(topic: str, event: str):
    """
    Example: register a topic-related event.
    """
    from redis import Redis
    import os
    import json
    from datetime import datetime

    redis = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "topic": topic
    }

    redis.rpush("log:events", json.dumps(log_entry))
    print(f"[ZK_LOGGER] Topic event logged: {log_entry}")
