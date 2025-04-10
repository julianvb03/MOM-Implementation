from kazoo.client import KazooClient


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
