"""
    This module contains the code for the replication clients for QueueReplicationStub.
    It creates the clients for the target and source nodes.
    If avoid to create the clients, it will use the existing ones.
"""
import grpc
from app.domain.models import NODES_CONFIG, WHOAMI
from app.domain.logger_config import logger
from app.grpc.replication_service_pb2_grpc import QueueReplicationStub

TARGET_QUEUE_NODE_ID = NODES_CONFIG[WHOAMI].get('whoreplica')
SOURCE_QUEUE_NODE_ID = None
for node_id, config in NODES_CONFIG.items():
    if config.get('whoreplica') == WHOAMI:
        SOURCE_QUEUE_NODE_ID = node_id
        break


def _create_queue_client(node_id) -> tuple[grpc.Channel, QueueReplicationStub]:
    """Helper function to create a client for a specific node."""
    if not node_id:
        return None, None

    config = NODES_CONFIG.get(node_id)
    if not config:
        logger.error(f"No se encontró configuración para el nodo '{node_id}'.")
        return None, None

    address = f"{config.get('ip')}:{config.get('grpc_port')}"
    if None in (config.get('ip'), config.get('grpc_port')):
        logger.error(f"Configuración incompleta para nodo '{node_id}'. IP o Puerto faltante.")
        return None, None

    try:
        channel = grpc.insecure_channel(address)
        stub = QueueReplicationStub(channel)
        logger.info(f"Cliente gRPC creado exitosamente para {node_id} en {address}")
        return channel, stub
    except Exception as e:
        logger.error(f"Fallo al crear cliente gRPC para {node_id} en {address}: {e}")
        return None, None


# --- Create clients for target and source nodes ---
TARGET_QUEUE_CHANNEL, TARGET_QUEUE_CLIENT = _create_queue_client(TARGET_QUEUE_NODE_ID)
SOURCE_QUEUE_CHANNEL, SOURCE_QUEUE_CLIENT = _create_queue_client(SOURCE_QUEUE_NODE_ID)


def get_target_queue_client() -> QueueReplicationStub:
    """Get the client for the target queue node."""
    if not TARGET_QUEUE_CLIENT:
        logger.error("Target QueueReplicationStub client is not available.")
    return TARGET_QUEUE_CLIENT


def get_source_queue_client() -> QueueReplicationStub:
    """Get the client for the source queue node."""
    if not SOURCE_QUEUE_CLIENT:
        logger.error("Source QueueReplicationStub client is not available.")
    return SOURCE_QUEUE_CLIENT


def get_queue_client(node_id):
    """Public function to get or create a QueueReplicationStub client."""
    return _create_queue_client(node_id)