from fastapi import APIRouter, HTTPException
from zookeeper.zk_utils import get_redis_connection
import json

router = APIRouter(prefix="/zookeeper", tags=["Zookeeper"])


@router.get("/nodes")
def list_registered_nodes():
    """Return all active MOM nodes registered in Zookeeper."""
    redis = get_redis_connection()
    try:
        nodes = redis.smembers("zookeeper:nodes")
        return {"nodes": [n.decode() for n in nodes]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
def get_topics_and_assignments():
    """Return topic assignments stored in Redis."""
    redis = get_redis_connection()
    try:
        topics = redis.hgetall("zookeeper:topics")
        decoded = {k.decode(): v.decode() for k, v in topics.items()}
        return {"topics": decoded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
def get_all_logs():
    """Return all logs stored in Redis (e.g. node down, publish attempts)."""
    redis = get_redis_connection()
    try:
        keys = redis.keys("log:*")
        logs = {}
        for key in keys:
            key_str = key.decode()
            entries = redis.lrange(key_str, 0, -1)
            logs[key_str] = [json.loads(e.decode()) for e in entries]
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{node_id}")
def get_logs_for_node(node_id: str):
    """Return logs for a specific MOM node (e.g. mom-1)."""
    redis = get_redis_connection()
    try:
        key = f"log:{node_id}"
        entries = redis.lrange(key, 0, -1)
        return {"node": node_id, "logs": [json.loads(e.decode()) for e in entries]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))