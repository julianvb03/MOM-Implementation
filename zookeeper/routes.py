from fastapi import APIRouter, HTTPException, Body
from zookeeper.zk_utils import get_redis_connection
from zookeeper.zk_registry import register_queue_or_topic, get_queue_topic_info
import json

router = APIRouter(prefix="/zookeeper", tags=["Zookeeper"])


@router.get("/nodes")
def list_registered_nodes():
    """Return all active MOM nodes registered in Zookeeper."""
    redis = get_redis_connection()
    try:
        nodes = redis.smembers("zookeeper:nodes")
        return {"nodes": list(nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue_topic")
def get_queue_topic_registry():
    """Return queue/topic assignments stored in Redis."""
    redis = get_redis_connection()
    try:
        entries = redis.hgetall("zookeeper:queue_topic_registry")
        decoded = {k: json.loads(v) for k, v in entries.items()}
        return {"registry": decoded}
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
            entries = redis.lrange(key, 0, -1)
            logs[key] = [json.loads(e) for e in entries]
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue_topic/registry")
def register_queue_topic(payload: dict = Body(...)):
    """
    Register or delete a queue or topic in the registry.

    Example payload:
    {
        "name": "my_topic",
        "type": "topic",
        "operation": "create",
        "origin_node": "A",
        "replica_nodes": ["B", "C"]
    }
    """
    try:
        register_queue_or_topic(
            name=payload["name"],
            type_=payload["type"],
            operation=payload["operation"],
            origin_node=payload["origin_node"],
            replica_nodes=payload["replica_nodes"]
        )
        return {"status": "success", "registry": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue_topic/registry/{name}")
def get_queue_topic_assignment(name: str):
    """Return a specific queue/topic registry entry."""
    try:
        info = get_queue_topic_info(name)
        if info:
            return {"queue_or_topic": name, "info": info}
        else:
            raise HTTPException(status_code=404, detail=f"Not found: {name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
