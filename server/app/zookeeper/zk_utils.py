"""
Helper utilities for Zookeeper logging and Redis key management.
"""

import json
import datetime


def build_log_key():
    """
    Build the Redis log key where logs are stored.
    """
    return "log:events"


def format_event(event_type: str, source: str, target: str = None, topic: str = None, message: str = None):
    """
    Format a structured log event to store in Redis.

    Args:
        event_type (str): Type of event (e.g. 'node_down', 'publish_fail', 'replication').
        source (str): The origin node ID.
        target (str, optional): Affected node (e.g., failed or replica).
        topic (str, optional): Affected topic.
        message (str, optional): Message or extra detail.

    Returns:
        dict: JSON-serializable dictionary with event metadata.
    """
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "source": source,
        "target": target,
        "topic": topic,
        "message": message
    }


def encode_to_json(data: dict) -> str:
    """
    Safely encode a dictionary to JSON string.
    """
    return json.dumps(data)


def decode_from_json(data: str) -> dict:
    """
    Decode JSON string to Python dictionary.
    """
    return json.loads(data)
