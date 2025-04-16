"""
Utils for MOM
"""

import grpc
import os
from app.domain.models import QueueOperationResult, MOMQueueStatus
from app.domain.logger_config import logger
from typing import Dict, Tuple
from app.grpc.replication_service_pb2_grpc import (
    QueueReplicationStub,
    TopicReplicationStub
)

class KeyBuilder:
    """
    Class for building repetitive keys
    """
    QUEUE_PREFIX = "mom:queues"
    METADATA_SUFFIX = "metadata"
    SUBSCRIBERS_SUFFIX = "subscribers"

    @classmethod
    def queue_key(cls, name: str) -> str:
        return f"{cls.QUEUE_PREFIX}:{name}"

    @classmethod
    def metadata_key(cls, name: str) -> str:
        return f"{cls.queue_key(name)}:{cls.METADATA_SUFFIX}"

    @classmethod
    def subscribers_key(cls, name: str) -> str:
        return f"{cls.queue_key(name)}:{cls.SUBSCRIBERS_SUFFIX}"

def handle_redis_errors(log_message: str):
    """
    This wrapper executes an operation over the database that might fail
    Args:
      log_message: A message for write on the log file.

    Returns:
      QueueOperationResult: With the information of the operation.
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e: # pylint: disable=W0718
                logger.exception(log_message)
                return QueueOperationResult(
                    success = False,
                    status = MOMQueueStatus.INTERNAL_ERROR,
                    details = str(e)
                )
        return wrapper
    return decorator

class TopicKeyBuilder:
    """
    Utility class for building Redis keys for topic-related operations
    """
    TOPIC_PREFIX = "mom:topics"
    METADATA_SUFFIX = "metadata"
    SUBSCRIBERS_SUFFIX = "subscribers"
    MESSAGES_SUFFIX = "messages"
    SUBSCRIBER_OFFSETS_SUFFIX = "offsets"

    @classmethod
    def topic_key(cls, name: str) -> str:
        return f"{cls.TOPIC_PREFIX}:{name}"

    @classmethod
    def metadata_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.METADATA_SUFFIX}"

    @classmethod
    def subscribers_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.SUBSCRIBERS_SUFFIX}"

    @classmethod
    def messages_key(cls, name: str) -> str:
        return f"{cls.topic_key(name)}:{cls.MESSAGES_SUFFIX}"

    @classmethod
    def subscriber_offsets_key(cls, topic_name: str) -> str:
        return f"{cls.topic_key(topic_name)}:{cls.SUBSCRIBER_OFFSETS_SUFFIX}"

    @classmethod
    def subscriber_offset_field(cls, subscriber: str) -> str:
        return f"subscriber_offset:{subscriber}"

def limpiar_user(texto):
    texto = texto.replace("'", "")
    texto = texto.replace("[", "").replace("]", "")
    return texto

NODES = {
    "A": {
        "ip": os.getenv("NODE_A_IP", "localhost"),
        "grpc_port": os.getenv("GRPC_PORT", "50051")
    },
    "B": {
        "ip": os.getenv("NODE_B_IP", "localhost"),
        "grpc_port": os.getenv("GRPC_PORT", "50051")
    },
    "C": {
        "ip": os.getenv("NODE_C_IP", "localhost"),
        "grpc_port": os.getenv("GRPC_PORT", "50051")
    }
}

class NodeClients:
    """Class to handle the stubs of the connections to all nodes"""
    
    def __init__(self):
        self.queue_stubs: Dict[str, QueueReplicationStub] = {}
        self.topic_stubs: Dict[str, TopicReplicationStub] = {}
        self.channels: Dict[str, grpc.Channel] = {}
        self._initialize_stubs()

    def _initialize_stubs(self):
        """Initialize the connections with all nodes"""
        for node_id, config in NODES.items():
            try:
                address = f"{config['ip']}:{config['grpc_port']}"
                channel = grpc.insecure_channel(address)
                self.channels[node_id] = channel
                
                # Crear stubs para Queue y Topic
                self.queue_stubs[node_id] = QueueReplicationStub(channel)
                self.topic_stubs[node_id] = TopicReplicationStub(channel)
                
                logger.info(f"Conexión establecida con nodo {node_id} en {address}")
            except Exception as e:
                logger.error(f"Error conectando con nodo {node_id}: {str(e)}")
                self.channels[node_id] = None
                self.queue_stubs[node_id] = None
                self.topic_stubs[node_id] = None

    def get_stubs(self, node_id: str) -> Tuple[QueueReplicationStub, TopicReplicationStub]:
        """
        Get the stubs for a specific node
        Args:
            node_id (str): ID of the node (A, B, or C)
        Returns:
            Tuple[QueueReplicationStub, TopicReplicationStub]: Tuple with the stubs
        """
        return self.queue_stubs.get(node_id), self.topic_stubs.get(node_id)

    def close_all(self):
        """Close all connections"""
        for node_id, channel in self.channels.items():
            if channel:
                try:
                    channel.close()
                    logger.info(f"Conexión cerrada con nodo {node_id}")
                except Exception as e:
                    logger.error(f"Error cerrando conexión con nodo {node_id}: {str(e)}")

node_clients = NodeClients()

def get_node_stubs(node_id: str) -> Tuple[QueueReplicationStub, TopicReplicationStub]:
    """
    Helper function to get the stubs of a node
    Args:
        node_id (str): ID of the node (A, B, or C)
    Returns:
        Tuple[QueueReplicationStub, TopicReplicationStub]: Tuple with the stubs
    """
    return node_clients.get_stubs(node_id)