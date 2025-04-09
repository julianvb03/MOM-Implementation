import grpc
from app.domain.models import NODES_CONFIG, WHOAMI, ReplicationStatus
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    ReplicationResponse,
    StatusCode,
    CreateTopicRequest,
    DeleteTopicRequest,
    TopicPublishMessageRequest,
    TopicConsumeMessageRequest,
    ReplicationResponse,
    CreateQueueRequest,
)
from app.grpc.replication_service_pb2_grpc import TopicReplicationStub

class TopicReplicationClient:
    """Client for topic replication via gRPC"""
    
    def __init__(self, to_original_node: bool = False):
        # Determinar el nodo de réplica basado en la configuración
        self.current_node = WHOAMI
        self.replica_node_id = NODES_CONFIG[self.current_node]['whoreplica']
        if not to_original_node:
            self.replica_address = f"{NODES_CONFIG[self.replica_node_id]['ip']}:{NODES_CONFIG[self.replica_node_id]['grpc_port']}"
        else:
            self.replica_address = f"{NODES_CONFIG[self.current_node]['ip']}:{NODES_CONFIG[self.current_node]['grpc_port']}"
        
    def get_client(self):
        """Create and return a gRPC stub for the replication service"""
        try:
            channel = grpc.insecure_channel(self.replica_address)
            client = TopicReplicationStub(channel)
            return client
        except Exception as e:
            logger.error(f"Failed to create gRPC stub: {str(e)}")
            return None
            
    def replicate_create_topic(self, topic_name: str, owner: str, created_at) -> bool:
        """
        Replicate topic creation to the replica node
        
        Returns:
            tuple: (ReplicationStatus, message)
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("Failed to create gRPC client '%s'", self.replica_address)
                return False
            
            request = CreateTopicRequest(
                topic_name=topic_name,
                owner=owner,
                created_at=created_at,
                original_node=self.current_node,
            )
            
            response = client.TopicReplicateCreate(request)
            
            if response.success:
                return True
            else:
                return False
                
        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR: gRPC error replicating topic creation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR: Error replicating topic creation: {str(e)}")
            return False

    def replicate_delete_topic(self, topic_name: str, owner: str) -> bool:
        """
        Replicate topic deletion to the replica node
        
        Args:
            topic_name (str): The name of the topic to delete.
            owner (str): The owner of the topic.

        Returns:
            bool: True if the topic was deleted successfully, False otherwise.
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("Failed to create gRPC client '%s'", self.replica_address)
                return False

            request = DeleteTopicRequest(
                topic_name=topic_name,
                requester=owner,
            )

            response = client.TopicReplicateDelete(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR: gRPC error replicating topic deletion: {str(e)}")
            return False
        
    def replicate_publish_message(self, topic_name: str, publisher: str, message: str, timestamp: float) -> bool:
        """
        Replicate message publishing to the replica node
        
        Args:
            topic_name (str): The name of the topic.
            publisher (str): The user publishing the message.
            message (str): The message content.
            timestamp (float): The timestamp of the message.

        Returns:
            bool: True if the message was replicated successfully, False otherwise.
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("Failed to create gRPC client '%s'", self.replica_address)
                return False

            request = TopicPublishMessageRequest(
                topic_name=topic_name,
                publisher=publisher,
                message=message,
                timestamp=timestamp
            )

            response = client.TopicReplicatePublishMessage(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR: gRPC error replicating message: {str(e)}")
        return False

    def replicate_consume_message(self, topic_name: str, subscriber: str, offset: int) -> bool:
        """
        Replicate message consumption to the replica node
        
        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user consuming the message.
            offset (int): The new offset after consuming the message.
            timestamp (float): The timestamp of the consumption.

        Returns:
            bool: True if the offset was replicated successfully, False otherwise.
        """
        try:
            client = self.get_client()
            if not client:
                logger.error("Failed to create gRPC client '%s'", self.replica_address)
                return False

            request = TopicConsumeMessageRequest(
                topic_name=topic_name,
                subscriber=subscriber,
                offset=offset
            )

            response = client.TopicReplicateConsumeMessage(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR: gRPC error replicating consumption: {str(e)}")
            return False