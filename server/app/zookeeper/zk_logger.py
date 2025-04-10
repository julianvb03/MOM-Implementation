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
