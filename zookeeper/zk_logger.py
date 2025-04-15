# zookeeper/zk_logger.py

import os
import json
from datetime import datetime
from redis import Redis
from rich.console import Console
from rich.panel import Panel

console = Console()

def _get_redis_connection() -> Redis:
    return Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )

def log_event(redis_client: Redis, event: str, origin: str, target: str = None, topics: list = None, notes: str = None):
    """
    Register a custom event in Redis and print it nicely.
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
    
    console.print(Panel.fit(
        f"[bold cyan]📄 Event Logged[/]\n"
        f"[bold]Event:[/] {event}\n"
        f"[bold]Origin:[/] {origin}\n"
        f"[bold]Target:[/] {target or '—'}\n"
        f"[bold]Topics:[/] {topics or '—'}\n"
        f"[bold]Notes:[/] {notes or '—'}",
        title=f"[bold green]{event.upper()}[/]",
        subtitle=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        border_style="bright_magenta"
    ))

def log_node_failure(node_id: str):
    """
    Logs a node down event in Redis and prints it.
    """
    redis = _get_redis_connection()
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "node_down",
        "origin": node_id
    }
    redis.rpush("log:events", json.dumps(log_entry))

    console.log(f"[bold red]❌ Node DOWN[/] → {node_id}", style="bold red")

def log_topic_event(topic: str, event: str):
    """
    Logs a topic-related event in Redis and prints it.
    """
    redis = _get_redis_connection()
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "topic": topic
    }
    redis.rpush("log:events", json.dumps(log_entry))

    console.log(f"[bold yellow]📦 Topic Event:[/] {event.upper()} → {topic}", style="bold yellow")
