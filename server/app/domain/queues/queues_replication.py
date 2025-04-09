import grpc
from app.domain.models import NODES_CONFIG, WHOAMI, ReplicationStatus
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    CreateQueueRequest,
    DeleteQueueRequest,
    EnqueueRequest,
    QueueSubscribeRequest,
    QueueUnsubscribeRequest,
    DequeueRequest

)
from app.grpc.replication_service_pb2_grpc import QueueReplicationStub

class QueueReplicationClient:
    """Client for topic replication via gRPC"""
    
    def __init__(self, stub: QueueReplicationStub, target_node_desc: str):
        """
        Initialize the client with a pre-created gRPC stub.
        Args:
            stub (TopicReplicationStub): The gRPC stub to use for calls.
            target_node_desc (str): Description of the destination node (for logging).
        """
        self.stub = stub
        self.target_node_desc = target_node_desc

    def create_queue(self, queue_name: str, owner: str, created_at: float):
        if not self.stub:
            return False

        try:
            request = CreateQueueRequest(
                queue_name=queue_name,
                owner=owner,
                created_at=created_at
            )
            
            response = self.stub.QueueReplicateCreate(request)
            
            if response.success:
                return True
            else:
                return False
                
        except grpc.RpcError as e:
            return False
        except Exception as e:
            return False
    
    def delete_queue(self, queue_name: str, owner: str):
        if not self.stub:
            return False

        try:
            request = DeleteQueueRequest(
                queue_name=queue_name,
                requester=owner
            )
            
            response = self.stub.QueueReplicateDelete(request)
            
            if response.success:
                return True
            else:
                return False
                
        except grpc.RpcError as e:
            return False
        except Exception as e:
            return False

    def enqueue(self, queue_name: str, message: str):
        pass

    def dequeue(self, queue_name: str):
        pass

    def subscribe(self, queue_name: str):
        pass

    def unsubscribe(self, queue_name: str):
        pass