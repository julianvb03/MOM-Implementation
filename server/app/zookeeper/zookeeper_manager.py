# app/zookeeper/zookeeper_manager.py

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
from redis import Redis
import os
import json
import time

from app.config import env

NODE_ID = env.NODE_ID
NODE_HOST = env.NODE_HOST
ZOOKEEPER_HOST = env.ZOOKEEPER_HOST
ZOOKEEPER_PORT = env.ZOOKEEPER_PORT

REDIS_HOST = env.REDIS_HOST
REDIS_PORT = int(env.REDIS_PORT)
REDIS_PASSWORD = env.REDIS_PASSWORD

class ZookeeperManager:
    def __init__(self):
        self.zk = KazooClient(hosts=f"{ZOOKEEPER_HOST}:{ZOOKEEPER_PORT}")
        self.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )

    def start(self):
        self.zk.start()
        self._register_node()
        self._watch_mom_nodes()

    def _register_node(self):
        path = f"/mom_nodes/{NODE_ID}"
        data = NODE_HOST.encode("utf-8")
        self.zk.ensure_path("/mom_nodes")
        try:
            self.zk.create(path, value=data, ephemeral=True)
            self._log_event(f"✅ Nodo registrado en Zookeeper: {NODE_ID}")
        except NodeExistsError:
            self._log_event(f"⚠️ Nodo ya registrado: {NODE_ID}")

    def _watch_mom_nodes(self):
        @self.zk.ChildrenWatch("/mom_nodes")
        def on_change(children):
            self._log_event(f"🔄 Cambio en nodos MOM activos: {children}")
            # Detectar nodos caídos
            known = self.redis.smembers("active_moms")
            fallen = list(set(known) - set(children))
            for node in fallen:
                self._log_event(f"❌ MOM caído detectado: {node}")
                self._handle_node_failure(node)
            # Actualizar set actual
            self.redis.delete("active_moms")
            for node in children:
                self.redis.sadd("active_moms", node)

    def _handle_node_failure(self, node_id):
        # Ejemplo: Reasignar tópico si era el primario
        topics = self.redis.smembers(f"topics:owned_by:{node_id}")
        for topic in topics:
            # Buscar una réplica en Redis
            replicas = self.redis.smembers(f"topic:{topic}:replicas")
            if replicas:
                new_primary = list(replicas)[0]
                self.redis.set(f"topic:{topic}:primary", new_primary)
                self._log_event(f"⚙️ Tópico {topic} reasignado de {node_id} → {new_primary}")
            else:
                self._log_event(f"⚠️ No hay réplica para el tópico {topic}, quedó sin dueño.")

    def _log_event(self, msg: str):
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "node": NODE_ID,
            "message": msg
        }
        print(f"[ZK-MANAGER] {msg}")
        self.redis.rpush("log:events", json.dumps(event))

    def stop(self):
        self.zk.stop()
        self.zk.close()
