from fastapi import FastAPI
from zookeeper.zookeeper_manager import ZookeeperManager
from zookeeper.zk_logger import log_node_failure, log_topic_event
from zookeeper.zk_monitor import get_active_nodes
from zookeeper.routes import router as zk_admin_router
from zookeeper.env import API_NAME, API_VERSION

# ✅ Primero crea la app
app = FastAPI(
    title="Zookeeper Service",
    version=API_VERSION,
    description="Zookeeper FastAPI microservice for coordination",
    docs_url=f"/api/{API_VERSION}/{API_NAME}/admin/zookeeper/docs",
    openapi_url=f"/api/{API_VERSION}/{API_NAME}/admin/zookeeper/openapi.json",
)

# ✅ Luego incluye las rutas
app.include_router(zk_admin_router, prefix=f"/api/{API_VERSION}/{API_NAME}/admin/zookeeper")

# ✅ Inicia Zookeeper al arrancar
zk_manager = ZookeeperManager()

@app.on_event("startup")
def start_zookeeper():
    zk_manager.start()

# ✅ Endpoints de prueba para nodos y tópicos

@app.get("/zk/nodes")
def get_nodes():
    return {"active_nodes": get_active_nodes()}

@app.post("/zk/failure/{node_id}")
def simulate_failure(node_id: str):
    log_node_failure(node_id)
    return {"status": "node_failure_logged", "node": node_id}

@app.post("/zk/topic")
def simulate_topic_log(topic: str, event: str):
    log_topic_event(topic, event)
    return {"status": "topic_event_logged", "topic": topic, "event": event}
