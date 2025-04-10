from kazoo.client import KazooClient
from redis import Redis
import os


def is_node_up(zk_client: KazooClient, node_id: str) -> bool:
    """
    Check if a MOM node is currently registered in ZooKeeper.
    Returns True if the node is alive.
    """
    try:
        return zk_client.exists(f"/mom_nodes/{node_id}") is not None
    except Exception as e:
        print(f"[ZK_MONITOR] Error checking node {node_id}: {e}")
        return False

def get_active_nodes():
    """
    Returns the list of active MOM nodes stored in Redis.
    """
    redis = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )
    return list(redis.smembers("active_moms"))