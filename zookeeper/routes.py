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


@router.get("/registry/node/{node_id}")
def get_queues_and_topics_for_node(node_id: str):
    """Return all queues and topics assigned to a specific node."""
    try:
        redis = get_redis_connection()
        entries = redis.hgetall("zookeeper:queue_topic_registry")
        result = []

        for _, value in entries.items():
            data = json.loads(value)
            if data["origin_node"] == node_id or node_id in data["replica_nodes"]:
                result.append({"name": data["name"], "type": data["type"]})

        if not result:
            raise HTTPException(status_code=404, detail="No assignments found for this node")
        return result
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


@router.delete("/queue_topic/registry")
def delete_queue_topic_assignment(payload: dict = Body(...)):
    """
    Delete a queue or topic assignment.
    """
    try:
        redis = get_redis_connection()
        redis.hdel("zookeeper:queue_topic_registry", payload["name"])
        keys = redis.keys("zookeeper:node:*")
        for key in keys:
            redis.srem(key, json.dumps({"name": payload["name"], "type": payload["type"]}))
        return {"status": "success", "message": "Assignment removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue_topic/assigned_nodes")
def get_nodes_with_assignment(name: str, type: str):
    """Get nodes that have a given queue or topic."""
    try:
        redis = get_redis_connection()
        result = []
        keys = redis.keys("zookeeper:node:*")
        for key in keys:
            entries = redis.smembers(key)
            for entry in entries:
                decoded = json.loads(entry)
                if decoded.get("name") == name and decoded.get("type") == type:
                    result.append(key.decode().split(":")[-1])
        return {"nodes": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/health")
def check_node_health(node: str):
    """Check if a node is alive."""
    try:
        redis = get_redis_connection()
        active = redis.smembers("zookeeper:nodes")
        return {"node": node, "alive": node in active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/assignments")
def get_assignments_for_node(node: str):
    """Get all topics/queues assigned to a node."""
    try:
        redis = get_redis_connection()
        key = f"zookeeper:node:{node}"
        entries = redis.smembers(key)
        decoded = [json.loads(e) for e in entries]
        return {"node": node, "assignments": decoded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
