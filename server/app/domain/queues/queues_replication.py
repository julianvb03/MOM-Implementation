"""
    This module contains the code for the replication clients 
    that do petitions over the gRPC interface.
"""
import grpc
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    CreateQueueRequest,
    DeleteQueueRequest,
    EnqueueRequest,
    QueueSubscribeRequest,
    QueueUnsubscribeRequest,
    DequeueRequest,
    QueueForwardEnqueueRequest,
    QueueForwardDequeueRequest,
    QueueForwardSubscribeRequest,
    QueueForwardUnsubscribeRequest,
)
from app.grpc.replication_service_pb2_grpc import QueueReplicationStub
from app.domain.utils import get_node_stubs
from app.domain.models import QueueOperationResult, MOMQueueStatus
import json

class QueueReplicationClient:
    """Client for topic replication via gRPC"""

    def __init__(self, stub: QueueReplicationStub, target_node_desc: str):
        """
        Initialize the client with a pre-created gRPC stub.
        Args:
            stub (TopicReplicationStub): The gRPC stub to use for calls.
            target_node_desc (str): Description of the destination
                node (for logging).
        """
        self.stub = stub
        self.target_node_desc = target_node_desc

    def create_queue(self, queue_name: str, owner: str, created_at: float):
        if not self.stub:
            return False

        try:
            request = CreateQueueRequest(
                queue_name=queue_name, owner=owner, created_at=created_at
            )

            response = self.stub.QueueReplicateCreate(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError:
            return False
        except Exception: # pylint: disable=W0718
            return False

    def delete_queue(self, queue_name: str, owner: str):
        if not self.stub:
            return False

        try:
            request = DeleteQueueRequest(queue_name=queue_name, requester=owner)

            response = self.stub.QueueReplicateDelete(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError:
            return False
        except Exception: # pylint: disable=W0718
            return False

    def enqueue(
        self, queue_name: str, user: str, message: str,
        uuid: str, timestamp: float
    ):
        if not self.stub:
            logger.error("No hay stub disponible para replicación")
            return False

        try:
            request = EnqueueRequest(
                queue_name=queue_name,
                requester=user,
                message=message,
                uuid=uuid,
                timestamp=timestamp,
            )

            response = self.stub.QueueReplicateEnqueue(request)

            if response.success:
                return True
            else:
                logger.error("Error en replicación: %s", response.message)
                return False

        except grpc.RpcError:
            logger.error("Error gRPC en replicación")
            return False
        except Exception: # pylint: disable=W0718
            logger.error("Error inesperado en replicación")
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
                queue_name=queue_name, requester=user, uuid=uuid
            ) # pylint: disable=C0301

            response = self.stub.QueueReplicateDequeue(request)
            if response.success:
                return True
            else:
                logger.error("Error en replicación de dequeue %s", response.message) # pylint: disable=C0301
                return False

        except Exception: # pylint: disable=W0718
            logger.error("Error inesperado en replicación de dequeue")
            return False

    def subscribe(self, queue_name: str, user: str):
        if not self.stub:
            return False

        try:
            request = QueueSubscribeRequest(
                queue_name=queue_name, requester=user
            ) # pylint: disable=C0301
            response = self.stub.QueueReplicateSubscribe(request)
            if response.success:
                return True
            else:
                return False

        except grpc.RpcError:
            return False
        except Exception: # pylint: disable=W0718
            return False

    def unsubscribe(self, queue_name: str, user: str):
        if not self.stub:
            return False

        try:
            request = QueueUnsubscribeRequest(
                queue_name=queue_name, requester=user
            ) # pylint: disable=C0301

            response = self.stub.QueueReplicateUnsubscribe(request)

            if response.success:
                return True
            else:
                return False

        except grpc.RpcError:
            return False
        except Exception: # pylint: disable=W0718
            return False

    def forward_enqueue(self, queue_name: str, user: str, message: str, node: str) -> QueueOperationResult:
        queue_stub, _ = get_node_stubs(node)

        if not queue_stub:
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details="Cannot forward enqueue to node"
            )

        try:
            request = QueueForwardEnqueueRequest(
                queue_name=queue_name,
                publisher=user,
                message=message,
            )
            response = queue_stub.QueueReplicateForwardEnqueue(request)
            # Aquí está el cambio clave - verificamos el mensaje de la respuesta
            if response.success:
                try:
                    # Intentamos parsear el mensaje como JSON por si viene en ese formato
                    message_data = json.loads(response.message)
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details=message_data.get("details", "Message enqueued successfully")
                    )
                except json.JSONDecodeError:
                    # Si no es JSON, usamos el mensaje directamente
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details="Error enqueueing message"
                    )
            else:
                return QueueOperationResult(
                    success=False,
                    status=MOMQueueStatus.INTERNAL_ERROR,
                    details="Error enqueueing message"
                )
        except Exception as e:
            error_message = e.details() if hasattr(e, 'details') else str(e)
            logger.exception("Error en forward_enqueue")
            return QueueOperationResult(    
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=error_message
            )

    def forward_dequeue(self, queue_name: str, user: str, node: str) -> QueueOperationResult:
        queue_stub, _ = get_node_stubs(node)

        if not queue_stub:
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details="Cannot forward dequeue to node"
            )

        try:
            request = QueueForwardDequeueRequest(
                queue_name=queue_name,
                subscriber=user,
            )
            response = queue_stub.QueueReplicateForwardDequeue(request)
            # Aquí está el cambio clave - verificamos el mensaje de la respuesta
            if response.success:
                try:
                    # Intentamos parsear el mensaje como JSON por si viene en ese formato
                    message_data = json.loads(response.message)
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details=message_data.get("details", "")
                    )
                except json.JSONDecodeError:
                    # Si no es JSON, usamos el mensaje directamente
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details=""
                    )
            else:
                return QueueOperationResult(
                    success=False,
                    status=MOMQueueStatus.INTERNAL_ERROR,
                    details="Error dequeueing message"
                )
        except Exception as e:
            error_message = e.details() if hasattr(e, 'details') else str(e)
            logger.exception("Error en forward_dequeue")
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=error_message
            )
        
    def forward_subscribe(self, queue_name: str, user: str, node: str) -> QueueOperationResult:
        queue_stub, _ = get_node_stubs(node)

        if not queue_stub:
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details="Cannot forward subscribe to node"
            )

        try:
            request = QueueForwardSubscribeRequest(
                queue_name=queue_name,
                subscriber=user,
            )
            response = queue_stub.QueueReplicateForwardSubscribe(request)
            
            if response.success:
                try:
                    message_data = json.loads(response.message)
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details=message_data.get("details", "Successfully subscribed to queue")
                    )
                except json.JSONDecodeError:
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details="Error subscribing to queue"
                    )
            else:
                return QueueOperationResult(
                    success=False,
                    status=MOMQueueStatus.INTERNAL_ERROR,
                    details="Error subscribing to queue"
                )
        except Exception as e:
            error_message = e.details() if hasattr(e, 'details') else str(e)
            logger.exception("Error en forward_subscribe")
            return QueueOperationResult(    
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=error_message
            )
        
    def forward_unsubscribe(self, queue_name: str, user: str, node: str) -> QueueOperationResult:
        queue_stub, _ = get_node_stubs(node)

        if not queue_stub:
            return QueueOperationResult(
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details="Cannot forward unsubscribe to node"
            )

        try:
            request = QueueForwardUnsubscribeRequest(
                queue_name=queue_name,
                subscriber=user,
            )
            response = queue_stub.QueueReplicateForwardUnsubscribe(request)
            
            if response.success:
                try:
                    message_data = json.loads(response.message)
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details=message_data.get("details", "Successfully unsubscribed from queue")
                    )
                except json.JSONDecodeError:
                    return QueueOperationResult(
                        success=True,
                        status=MOMQueueStatus.SUCCES_OPERATION,
                        details="Error unsubscribing from queue"
                    )
            else:
                return QueueOperationResult(
                    success=False,
                    status=MOMQueueStatus.INTERNAL_ERROR,
                    details="Error unsubscribing from queue"
                )
        except Exception as e:
            error_message = e.details() if hasattr(e, 'details') else str(e)
            logger.exception("Error en forward_unsubscribe")
            return QueueOperationResult(    
                success=False,
                status=MOMQueueStatus.INTERNAL_ERROR,
                details=error_message
            )