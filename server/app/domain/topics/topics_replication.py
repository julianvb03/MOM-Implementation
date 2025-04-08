import grpc
from app.domain.models import NODES_CONFIG, WHOAMI, ReplicationStatus
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    ReplicationResponse,
    StatusCode,
    CreateTopicRequest,
    DeleteTopicRequest,
    ReplicationResponse,
    CreateQueueRequest,
)
from app.grpc.replication_service_pb2_grpc import TopicReplicationStub

class TopicReplicationClient:
    """Client for topic replication via gRPC"""
    
    def __init__(self):
        # Determinar el nodo de réplica basado en la configuración
        self.current_node = WHOAMI
        self.replica_node_id = NODES_CONFIG[self.current_node]['whoreplica']
        self.replica_address = f"{NODES_CONFIG[self.replica_node_id]['ip']}:{NODES_CONFIG[self.replica_node_id]['grpc_port']}"
        
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
        
