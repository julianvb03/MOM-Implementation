import grpc
from app.domain.models import NODES_CONFIG, WHOAMI, ReplicationStatus
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    CreateTopicRequest,
    DeleteTopicRequest,
    TopicPublishMessageRequest,
    TopicConsumeMessageRequest,
    TopicSubscribeRequest,
    TopicUnsubscribeRequest,
)
from app.grpc.replication_service_pb2_grpc import TopicReplicationStub

class TopicReplicationClient:
    """Client for topic replication via gRPC"""
    
    def __init__(self, stub: TopicReplicationStub, target_node_desc: str):
        """
        Initialize the client with a pre-created gRPC stub.
        Args:
            stub (TopicReplicationStub): The gRPC stub to use for calls.
            target_node_desc (str): Description of the destination node (for logging).
        """
        self.stub = stub
        self.target_node_desc = target_node_desc
            
    def replicate_create_topic(self, topic_name: str, owner: str, created_at) -> bool:
        """
        Replicate topic creation to the replica node
        
        Returns:
            bool: True if the topic was created successfully, False otherwise.
        """
        if not self.stub:
            logger.error(f"Replicación fallida (create_topic): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = CreateTopicRequest(
                topic_name=topic_name,
                owner=owner,
                created_at=created_at,
            )
            
            response = self.stub.TopicReplicateCreate(request)
            
            if response.success:
                logger.debug(f"Tópico '{topic_name}' replicado exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación del tópico '{topic_name}' a {self.target_node_desc}")
                return False
                
        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (create_topic): gRPC error replicating to")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (create_topic): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
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
        if not self.stub:
            logger.error(f"Replicación fallida (delete_topic): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = DeleteTopicRequest(
                topic_name=topic_name,
                requester=owner,
            )

            response = self.stub.TopicReplicateDelete(request)

            if response.success:
                logger.info(f"Eliminación del tópico '{topic_name}' replicada exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación de eliminación del tópico '{topic_name}' a {self.target_node_desc}")
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (delete_topic): gRPC error replicating to {self.target_node_desc}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (delete_topic): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
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
        if not self.stub:
            logger.error(f"Replicación fallida (publish_message): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = TopicPublishMessageRequest(
                topic_name=topic_name,
                publisher=publisher,
                message=message,
                timestamp=timestamp
            )

            response = self.stub.TopicReplicatePublishMessage(request)

            if response.success:
                logger.info(f"Mensaje publicado en tópico '{topic_name}' replicado exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación de publicación en tópico '{topic_name}' a {self.target_node_desc}")
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (publish_message): gRPC error replicating to {self.target_node_desc}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (publish_message): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
            return False

    def replicate_consume_message(self, topic_name: str, subscriber: str, offset: int) -> bool:
        """
        Replicate message consumption to the replica node
        
        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user consuming the message.
            offset (int): The new offset after consuming the message.

        Returns:
            bool: True if the offset was replicated successfully, False otherwise.
        """
        if not self.stub:
            logger.error(f"Replicación fallida (consume_message): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = TopicConsumeMessageRequest(
                topic_name=topic_name,
                subscriber=subscriber,
                offset=offset
            )

            response = self.stub.TopicReplicateConsumeMessage(request)

            if response.success:
                logger.info(f"Consumo de mensaje en tópico '{topic_name}' replicado exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación de consumo en tópico '{topic_name}' a {self.target_node_desc}")
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (consume_message): gRPC error replicating to {self.target_node_desc}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (consume_message): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
            return False
        
    def replicate_subscribe(self, topic_name: str, subscriber: str) -> bool:
        """
        Replicate subscription to the replica node
        
        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user subscribing to the topic.

        Returns:
            bool: True if the subscription was replicated successfully, False otherwise.
        """
        if not self.stub:
            logger.error(f"Replicación fallida (subscribe): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = TopicSubscribeRequest(
                topic_name=topic_name,
                subscriber=subscriber
            )

            response = self.stub.TopicReplicateSubscribe(request)

            if response.success:
                logger.info(f"Suscripción a tópico '{topic_name}' replicada exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación de suscripción a tópico '{topic_name}' a {self.target_node_desc}")
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (subscribe): gRPC error replicating to {self.target_node_desc}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (subscribe): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
            return False

    def replicate_unsubscribe(self, topic_name: str, subscriber: str) -> bool:
        """
        Replicate unsubscription to the replica node
        
        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user unsubscribing from the topic.

        Returns:
            bool: True if the unsubscription was replicated successfully, False otherwise.
        """
        if not self.stub:
            logger.error(f"Replicación fallida (unsubscribe): Stub no disponible para {self.target_node_desc}.")
            return False

        try:
            request = TopicUnsubscribeRequest(
                topic_name=topic_name,
                subscriber=subscriber
            )

            response = self.stub.TopicReplicateUnsubscribe(request)

            if response.success:
                logger.info(f"Desuscripción de tópico '{topic_name}' replicada exitosamente a {self.target_node_desc}")
                return True
            else:
                logger.error(f"Fallo en la replicación de desuscripción de tópico '{topic_name}' a {self.target_node_desc}")
                return False

        except grpc.RpcError as e:
            logger.error(f"REPLICATION ERROR (unsubscribe): gRPC error replicating to {self.target_node_desc}")
            return False
        except Exception as e:
            logger.error(f"REPLICATION ERROR (unsubscribe): Error inesperado replicating to {self.target_node_desc}: {str(e)}")
            return False