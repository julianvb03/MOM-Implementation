"""
    This module contains the code for the replication clients.
    It creates the clients for the target and source nodes.
    If avoid to create the clients, it will use the existing ones.
"""
import grpc
from app.domain.models import NODES_CONFIG, WHOAMI
from app.domain.logger_config import logger
from app.grpc.replication_service_pb2_grpc import TopicReplicationStub

# --- Determine target nodes ---
TARGET_REPLICA_NODE_ID = NODES_CONFIG[WHOAMI].get("whoreplica")
SOURCE_NODE_ID = None
for node_id, config in NODES_CONFIG.items():
    if config.get("whoreplica") == WHOAMI:
        SOURCE_NODE_ID = node_id
        break


def _create_client(node_id) -> tuple[grpc.Channel, TopicReplicationStub]: # pylint: disable=redefined-outer-name
    """Helper function to create a client for a specific node."""
    if not node_id:
        return None, None

    config = NODES_CONFIG.get(node_id) # pylint: disable=redefined-outer-name
    if not config:
        logger.error("No se encontró configuración para el nodo %s.", node_id)
        return None, None

    address = f"{config.get("ip")}:{config.get("grpc_port")}"
    if None in (config.get("ip"), config.get("grpc_port")):
        logger.error("Configuración incompleta para nodo %s. IP o Puerto faltante.", node_id) # pylint: disable=C0301
        return None, None

    try:
        channel = grpc.insecure_channel(address)
        stub = TopicReplicationStub(channel)
        return channel, stub
    except Exception: # pylint: disable=W0718
        logger.error("Fallo al crear cliente gRPC para %s en %s", node_id, address) # pylint: disable=C0301
        return None, None

# Cliente para replicar HACIA AFUERA (a nuestra réplica designada)
TARGET_REPLICA_CHANNEL, TARGET_REPLICA_STUB = _create_client(TARGET_REPLICA_NODE_ID) # pylint: disable=C0301

# Cliente para replicar HACIA ATRÁS (al nodo que nos replica a nosotros)
SOURCE_NODE_CHANNEL, SOURCE_NODE_STUB = _create_client(SOURCE_NODE_ID)

def get_replica_client_stub():
    """Devuelve el stub para conectarse al nodo réplica de este nodo."""
    if not TARGET_REPLICA_STUB:
        logger.error("Intento de obtener stub de réplica (%s), pero no se inicializó.", TARGET_REPLICA_NODE_ID) # pylint: disable=C0301
    return TARGET_REPLICA_STUB

def get_source_client_stub():
    """Devuelve el stub para conectarse al nodo que replica a este nodo (nuestro origen).""" # pylint: disable=C0301
    if not SOURCE_NODE_STUB:
        logger.error("Intento de obtener stub de origen (%s), pero no se inicializó.", SOURCE_NODE_ID) # pylint: disable=C0301
    return SOURCE_NODE_STUB

def close_all_replication_clients():
    logger.info("Cerrando canales de cliente gRPC de replicación...")
    if TARGET_REPLICA_CHANNEL:
        try:
            TARGET_REPLICA_CHANNEL.close()
        except Exception:  # pylint: disable=W0718
            logger.error("Error cerrando canal gRPC para réplica (%s)", TARGET_REPLICA_NODE_ID) # pylint: disable=C0301
    if SOURCE_NODE_CHANNEL:
        try:
            SOURCE_NODE_CHANNEL.close()
        except Exception:  # pylint: disable=W0718
            logger.error("Error cerrando canal gRPC para origen (%s)", SOURCE_NODE_ID) # pylint: disable=C0301
