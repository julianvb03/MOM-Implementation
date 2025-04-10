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

    def enqueue(self, queue_name: str, user: str, message: str, uuid: str, timestamp: float):
        if not self.stub:
            logger.error("No hay stub disponible para replicación")
            return False

        try:
            request = EnqueueRequest(
                queue_name=queue_name,
                requester=user,
                message=message,
                uuid=uuid,
                timestamp=timestamp
            )

            logger.info(f"Enviando solicitud de encolamiento a {self.target_node_desc}")
            response = self.stub.QueueReplicateEnqueue(request)

            if response.success:
                logger.info("Encolamiento replicado exitosamente")
                return True
            else:
                logger.error(f"Error en replicación: {response.message}")
                return False
        
        except grpc.RpcError as e:
            logger.error(f"Error gRPC en replicación: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en replicación: {str(e)}")
            return False
            

    def dequeue(self, queue_name: str, user: str, uuid: str) -> bool:
        """
        Replica una operación de dequeue en el nodo remoto.
        
        Args:
            queue_name (str): Nombre de la cola
            user (str): Usuario que realiza la operación
            uuid (str): UUID del mensaje a desencolar
            
        Returns:
            bool: True si la replicación fue exitosa, False en caso contrario
        """
        if not self.stub:
            logger.error("No hay stub disponible para replicación")
            return False
            
        try:
            request = DequeueRequest(
                queue_name=queue_name,
                requester=user,
                uuid=uuid
            )
            
            response = self.stub.QueueReplicateDequeue(request)
            if response.success:
                logger.info(f"Dequeue replicado exitosamente en {self.target_node_desc}")
                return True
            else:
                logger.error(f"Error en replicación de dequeue: {response.message}")
                return False
                
        except Exception as e:
            logger.error(f"Error inesperado en replicación de dequeue: {str(e)}")
            return False

    def subscribe(self, queue_name: str, user: str):
        if not self.stub:
            return False

        try:
            request = QueueSubscribeRequest(
                queue_name=queue_name,
                requester=user
            )
            
            response = self.stub.QueueReplicateSubscribe(request)
            
            if response.success:
                return True
            else:
                return False
                
        except grpc.RpcError as e:
            return False
        except Exception as e:
            return False

    def unsubscribe(self, queue_name: str, user: str):
        if not self.stub:
            return False

        try:
            request = QueueUnsubscribeRequest(
                queue_name=queue_name,
                requester=user
            )
            
            response = self.stub.QueueReplicateUnsubscribe(request)
            
            if response.success:
                return True
            else:
                return False
                
        except grpc.RpcError as e:
            return False
        except Exception as e:
            return False