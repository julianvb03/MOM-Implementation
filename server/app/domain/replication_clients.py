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
TARGET_REPLICA_NODE_ID = NODES_CONFIG[WHOAMI].get('whoreplica')
SOURCE_NODE_ID = None
for node_id, config in NODES_CONFIG.items():
    if config.get('whoreplica') == WHOAMI:
        SOURCE_NODE_ID = node_id
        break


def _create_client(node_id) -> tuple[grpc.Channel, TopicReplicationStub]:
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
        stub = TopicReplicationStub(channel)
        logger.info(f"Cliente gRPC creado exitosamente para {node_id} en {address}")
        return channel, stub
    except Exception as e:
        logger.error(f"Fallo al crear cliente gRPC para {node_id} en {address}: {e}")
        return None, None

# Cliente para replicar HACIA AFUERA (a nuestra réplica designada)
TARGET_REPLICA_CHANNEL, TARGET_REPLICA_STUB = _create_client(TARGET_REPLICA_NODE_ID)

# Cliente para replicar HACIA ATRÁS (al nodo que nos replica a nosotros)
SOURCE_NODE_CHANNEL, SOURCE_NODE_STUB = _create_client(SOURCE_NODE_ID)

def get_replica_client_stub():
    """Devuelve el stub para conectarse al nodo réplica de este nodo."""
    if not TARGET_REPLICA_STUB:
         logger.error(f"Intento de obtener stub de réplica ({TARGET_REPLICA_NODE_ID}), pero no se inicializó.")
    return TARGET_REPLICA_STUB

def get_source_client_stub():
    """Devuelve el stub para conectarse al nodo que replica a este nodo (nuestro origen)."""
    if not SOURCE_NODE_STUB:
        logger.error(f"Intento de obtener stub de origen ({SOURCE_NODE_ID}), pero no se inicializó.")
    return SOURCE_NODE_STUB

def close_all_replication_clients():
    logger.info("Cerrando canales de cliente gRPC de replicación...")
    if TARGET_REPLICA_CHANNEL:
        try:
            TARGET_REPLICA_CHANNEL.close()
            logger.info(f"Canal gRPC cerrado para réplica ({TARGET_REPLICA_NODE_ID}).")
        except Exception as e:
            logger.error(f"Error cerrando canal gRPC para réplica ({TARGET_REPLICA_NODE_ID}): {e}")
    if SOURCE_NODE_CHANNEL:
        try:
            SOURCE_NODE_CHANNEL.close()
            logger.info(f"Canal gRPC cerrado para origen ({SOURCE_NODE_ID}).")
        except Exception as e:
            logger.error(f"Error cerrando canal gRPC para origen ({SOURCE_NODE_ID}): {e}")
