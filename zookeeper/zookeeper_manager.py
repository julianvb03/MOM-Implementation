"""Zookeeper Manager - Handles MOM node registration, monitoring, and failure recovery."""

import os
import json
import time
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
from redis import Redis

from zookeeper import env

# Environment variables
NODE_ID = env.NODE_ID
NODE_HOST = env.NODE_HOST
ZOOKEEPER_HOST = env.ZOOKEEPER_HOST
ZOOKEEPER_PORT = env.ZOOKEEPER_PORT

REDIS_HOST = env.REDIS_HOST
REDIS_PORT = int(env.REDIS_PORT)
REDIS_PASSWORD = env.REDIS_PASSWORD


class ZookeeperManager:
    def __init__(self):
        # Initialize Zookeeper and Redis clients
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
        """
        Registers this MOM node in Zookeeper using an ephemeral node.
        """
        path = f"/mom_nodes/{NODE_ID}"
        data = NODE_HOST.encode("utf-8")

        self.zk.ensure_path("/mom_nodes")

        try:
            self.zk.create(path, value=data, ephemeral=True)
            self._log_event(f"\033[92m✅ Nodo registrado en Zookeeper:\033[0m {NODE_ID}")
        except NodeExistsError:
            self._log_event(f"\033[93m⚠️ Nodo ya estaba registrado:\033[0m {NODE_ID}")

    def _watch_mom_nodes(self):
        """
        Watches /mom_nodes in Zookeeper for changes in registered nodes.
        """
        @self.zk.ChildrenWatch("/mom_nodes")
        def on_change(children):
            self._log_event(f"\033[96m🔄 Nodos MOM activos detectados:\033[0m {children}")
            
            # Detectar nodos caídos comparando con los almacenados
            known = self.redis.smembers("active_moms")
            fallen = list(set(known) - set(children))

            for node in fallen:
                self._log_event(f"\033[91m❌ MOM caído detectado:\033[0m {node}")
                self._handle_node_failure(node)

            # Actualizar set actual de nodos activos
            self.redis.delete("active_moms")
            for node in children:
                self.redis.sadd("active_moms", node)

    def _handle_node_failure(self, node_id):
        """
        Handles failover logic when a MOM node goes down.
        """
        topics = self.redis.smembers(f"topics:owned_by:{node_id}")

        for topic in topics:
            replicas = self.redis.smembers(f"topic:{topic}:replicas")
            if replicas:
                new_primary = list(replicas)[0]
                self.redis.set(f"topic:{topic}:primary", new_primary)
                self._log_event(f"\033[94m⚙️ Tópico {topic} reasignado de {node_id} → {new_primary}\033[0m")
            else:
                self._log_event(f"\033[91m⚠️ No hay réplica para el tópico {topic}, quedó sin dueño.\033[0m")

    def _log_event(self, msg: str):
        """
        Stores a log event in Redis and prints to console with formatting.
        """
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "node": NODE_ID,
            "message": msg
        }
        print(f"\033[95m[ZK-MANAGER]\033[0m {msg}")
        self.redis.rpush("log:events", json.dumps(event))

    def stop(self):
        self.zk.stop()
        self.zk.close()
