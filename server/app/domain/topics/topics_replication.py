"""
This module contains the TopicReplicationClient class, which is 
responsible for replicating topic operations to the replica node.
"""

import json
import grpc
from app.domain.logger_config import logger

from app.grpc.replication_service_pb2 import (
    CreateTopicRequest,
    DeleteTopicRequest,
    TopicPublishMessageRequest,
    TopicConsumeMessageRequest,
    TopicSubscribeRequest,
    TopicUnsubscribeRequest,
    TopicForwardSubscribeRequest,
    TopicForwardUnsubscribeRequest
)
from app.grpc.replication_service_pb2_grpc import TopicReplicationStub
from app.domain.models import TopicOperationResult, MOMTopicStatus
from app.domain.utils import get_node_stubs

class TopicReplicationClient:
    """Client for topic replication via gRPC"""

    def __init__(self, stub: TopicReplicationStub, target_node_desc: str):
        """
        Initialize the client with a pre-created gRPC stub.
        Args:
            stub (TopicReplicationStub): The gRPC stub to use for calls.
            target_node_desc (str): Description of the destination
            node (for logging).
        """
        self.stub = stub
        self.target_node_desc = target_node_desc

    def replicate_create_topic(
            self, topic_name: str, owner: str, created_at
            ) -> bool:
        """
        Replicate topic creation to the replica node

        Returns:
            bool: True if the topic was created successfully, False otherwise.
        """
        if not self.stub:
            logger.error("Replication error on create_topic to %s", self.target_node_desc) # pylint: disable=C0301
            return False

        try:
            request = CreateTopicRequest(
                topic_name=topic_name,
                owner=owner,
                created_at=created_at,
            )

            response = self.stub.TopicReplicateCreate(request)

            if response.success:
                return True
            else:
                logger.error("Replication error on create_topic to %s", self.target_node_desc) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.error("REPLICATION ERROR (create_topic): gRPC error replicating to") # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Error creating topic '%s'", topic_name)
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
            logger.error("Replication error on delete_topic to %s", self.target_node_desc) # pylint: disable=C0301
            return False

        try:
            request = DeleteTopicRequest(
                topic_name=topic_name,
                requester=owner,
            )

            response = self.stub.TopicReplicateDelete(request)

            if response.success:
                return True
            else:
                logger.error("Replication error on delete_topic to %s", self.target_node_desc) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.error("Replication error on delete_topic to %s", self.target_node_desc) # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Replication error on delete_topic to %s", self.target_node_desc) # pylint: disable=C0301
            return False

    def replicate_publish_message(
        self, topic_name: str, publisher: str, message: str, timestamp: float
    ) -> bool:
        """
        Replicate message publishing to the replica node

        Args:
            topic_name (str): The name of the topic.
            publisher (str): The user publishing the message.
            message (str): The message content.
            timestamp (float): The timestamp of the message.

        Returns:
            bool: True if the message was replicated successfully,
            False otherwise.
        """
        if not self.stub:
            logger.error("Replication error on publish_message to %s", self.target_node_desc) # pylint: disable=C0301
            return False

        try:
            request = TopicPublishMessageRequest(
                topic_name=topic_name,
                publisher=publisher,
                message=message,
                timestamp=timestamp,
            )

            response = self.stub.TopicReplicatePublishMessage(request)

            if response.success:
                return True
            else:
                logger.error("Replication error on publish_message to %s", self.target_node_desc) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.exception("Replication error on publish_message to %s", self.target_node_desc) # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Replication error on publish_message to %s", self.target_node_desc) # pylint: disable=C0301
            return False

    def replicate_consume_message(
        self, topic_name: str, subscriber: str, offset: int
    ) -> bool:
        """
        Replicate message consumption to the replica node

        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user consuming the message.
            offset (int): The new offset after consuming the message.

        Returns:
            bool: True if the offset was replicated successfully, 
            False otherwise.
        """
        if not self.stub:
            logger.error("Error consuming message replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False

        try:
            request = TopicConsumeMessageRequest(
                topic_name=topic_name, subscriber=subscriber, offset=offset
            )

            response = self.stub.TopicReplicateConsumeMessage(request)

            if response.success:
                return True
            else:
                logger.error("Error consuming message replication to topic '%s'", topic_name) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.exception("Error consuming message replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Error consuming message replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False

    def replicate_subscribe(self, topic_name: str, subscriber: str) -> bool:
        """
        Replicate subscription to the replica node

        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user subscribing to the topic.

        Returns:
            bool: True if the subscription was replicated 
            successfully, False otherwise.
        """
        if not self.stub:
            logger.error("Error subscribing replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False

        try:
            request = TopicSubscribeRequest(
                topic_name=topic_name, subscriber=subscriber
            )

            response = self.stub.TopicReplicateSubscribe(request)

            if response.success:
                return True
            else:
                logger.error("Error subscribing replication to topic '%s'", topic_name) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.exception("Error subscribing replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Error subscribing replication to topic '%s'", topic_name) # pylint: disable=C0301
            return False

    def replicate_unsubscribe(self, topic_name: str, subscriber: str) -> bool:
        """
        Replicate unsubscription to the replica node

        Args:
            topic_name (str): The name of the topic.
            subscriber (str): The user unsubscribing from the topic.

        Returns:
            bool: True if the unsubscription was replicated
            successfully, False otherwise.
        """
        if not self.stub:
            logger.error("Error unsubscribing replication from topic '%s'", topic_name) # pylint: disable=C0301
            return False

        try:
            request = TopicUnsubscribeRequest(
                topic_name=topic_name, subscriber=subscriber
            )

            response = self.stub.TopicReplicateUnsubscribe(request)

            if response.success:
                return True
            else:
                logger.error("Error unsubscribing replication from topic '%s'", topic_name) # pylint: disable=C0301
                return False

        except grpc.RpcError:
            logger.exception("Error unsubscribing replication from topic '%s'", topic_name) # pylint: disable=C0301
            return False
        except Exception: # pylint: disable=W0703
            logger.exception("Error unsubscribing replication from topic '%s'", topic_name) # pylint: disable=C0301
            return False

    def forward_subscribe(self, topic_name: str, user: str, node: str) -> TopicOperationResult:
        _ , topic_stub = get_node_stubs(node)

        if not topic_stub:
            return TopicOperationResult(
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details="No se pudo obtener el stub del nodo"
            )

        try:
            request = TopicForwardSubscribeRequest(
                topic_name=topic_name,
                subscriber=user,
            )
            response = topic_stub.TopicReplicateForwardSubscribe(request)
            
            if response.success:
                try:
                    message_data = json.loads(response.message)
                    return TopicOperationResult(
                        success=True,
                        status=MOMTopicStatus.SUBSCRIPTION_CREATED,
                        details=message_data.get("details", "Suscripción realizada correctamente")
                    )
                except json.JSONDecodeError:
                    return TopicOperationResult(
                        success=True,
                        status=MOMTopicStatus.SUBSCRIPTION_CREATED,
                        details=response.message
                    )
            else:
                return TopicOperationResult(
                    success=False,
                    status=MOMTopicStatus.INTERNAL_ERROR,
                    details=response.message
                )
        except Exception as e:
            logger.exception("Error en forward_subscribe")
            return TopicOperationResult(    
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details=str(e)
            )
        
    def forward_unsubscribe(self, topic_name: str, user: str, node: str) -> TopicOperationResult:
        _ , topic_stub = get_node_stubs(node)

        if not topic_stub:
            return TopicOperationResult(
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details="No se pudo obtener el stub del nodo"
            )

        try:
            request = TopicForwardUnsubscribeRequest(
                topic_name=topic_name,
                subscriber=user,
            )
            response = topic_stub.TopicReplicateForwardUnsubscribe(request)
            
            if response.success:
                try:
                    message_data = json.loads(response.message)
                    return TopicOperationResult(
                        success=True,
                        status=MOMTopicStatus.SUBSCRIPTION_DELETED,
                        details=message_data.get("details", "Desuscripción realizada correctamente")
                    )
                except json.JSONDecodeError:
                    return TopicOperationResult(
                        success=True,
                        status=MOMTopicStatus.SUBSCRIPTION_DELETED,
                        details=response.message
                    )
            else:
                return TopicOperationResult(
                    success=False,
                    status=MOMTopicStatus.INTERNAL_ERROR,
                    details=response.message
                )
        except Exception as e:
            logger.exception("Error en forward_unsubscribe")
            return TopicOperationResult(    
                success=False,
                status=MOMTopicStatus.INTERNAL_ERROR,
                details=str(e)
            )