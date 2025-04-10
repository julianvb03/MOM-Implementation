# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import app.grpc.replication_service_pb2 as replication__service__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in replication_service_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class TopicReplicationStub(object):
    """Replication service for topics
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.TopicReplicateCreate = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicateCreate',
                request_serializer=replication__service__pb2.CreateTopicRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.TopicReplicateDelete = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicateDelete',
                request_serializer=replication__service__pb2.DeleteTopicRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.TopicReplicatePublishMessage = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicatePublishMessage',
                request_serializer=replication__service__pb2.TopicPublishMessageRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.TopicReplicateConsumeMessage = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicateConsumeMessage',
                request_serializer=replication__service__pb2.TopicConsumeMessageRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.TopicReplicateSubscribe = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicateSubscribe',
                request_serializer=replication__service__pb2.TopicSubscribeRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.TopicReplicateUnsubscribe = channel.unary_unary(
                '/app.grpc.TopicReplication/TopicReplicateUnsubscribe',
                request_serializer=replication__service__pb2.TopicUnsubscribeRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)


class TopicReplicationServicer(object):
    """Replication service for topics
    """

    def TopicReplicateCreate(self, request, context):
        """Create topic replication Done
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicReplicateDelete(self, request, context):
        """Delete topic replication Done
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicReplicatePublishMessage(self, request, context):
        """Publish message replication Done
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicReplicateConsumeMessage(self, request, context):
        """Consume message replication Done
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicReplicateSubscribe(self, request, context):
        """Subscribe user replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TopicReplicateUnsubscribe(self, request, context):
        """Unsubscribe user replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TopicReplicationServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'TopicReplicateCreate': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicateCreate,
                    request_deserializer=replication__service__pb2.CreateTopicRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'TopicReplicateDelete': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicateDelete,
                    request_deserializer=replication__service__pb2.DeleteTopicRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'TopicReplicatePublishMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicatePublishMessage,
                    request_deserializer=replication__service__pb2.TopicPublishMessageRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'TopicReplicateConsumeMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicateConsumeMessage,
                    request_deserializer=replication__service__pb2.TopicConsumeMessageRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'TopicReplicateSubscribe': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicateSubscribe,
                    request_deserializer=replication__service__pb2.TopicSubscribeRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'TopicReplicateUnsubscribe': grpc.unary_unary_rpc_method_handler(
                    servicer.TopicReplicateUnsubscribe,
                    request_deserializer=replication__service__pb2.TopicUnsubscribeRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'app.grpc.TopicReplication', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('app.grpc.TopicReplication', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class TopicReplication(object):
    """Replication service for topics
    """

    @staticmethod
    def TopicReplicateCreate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicateCreate',
            replication__service__pb2.CreateTopicRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TopicReplicateDelete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicateDelete',
            replication__service__pb2.DeleteTopicRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TopicReplicatePublishMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicatePublishMessage',
            replication__service__pb2.TopicPublishMessageRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TopicReplicateConsumeMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicateConsumeMessage',
            replication__service__pb2.TopicConsumeMessageRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TopicReplicateSubscribe(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicateSubscribe',
            replication__service__pb2.TopicSubscribeRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TopicReplicateUnsubscribe(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.TopicReplication/TopicReplicateUnsubscribe',
            replication__service__pb2.TopicUnsubscribeRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class QueueReplicationStub(object):
    """Replication service for queues
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.QueueReplicateCreate = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateCreate',
                request_serializer=replication__service__pb2.CreateQueueRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.QueueReplicateDelete = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateDelete',
                request_serializer=replication__service__pb2.DeleteQueueRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.QueueReplicateEnqueue = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateEnqueue',
                request_serializer=replication__service__pb2.EnqueueRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.QueueReplicateSubscribe = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateSubscribe',
                request_serializer=replication__service__pb2.QueueSubscribeRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.QueueReplicateUnsubscribe = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateUnsubscribe',
                request_serializer=replication__service__pb2.QueueUnsubscribeRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)
        self.QueueReplicateDequeue = channel.unary_unary(
                '/app.grpc.QueueReplication/QueueReplicateDequeue',
                request_serializer=replication__service__pb2.DequeueRequest.SerializeToString,
                response_deserializer=replication__service__pb2.ReplicationResponse.FromString,
                _registered_method=True)


class QueueReplicationServicer(object):
    """Replication service for queues
    """

    def QueueReplicateCreate(self, request, context):
        """Create queue replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueReplicateDelete(self, request, context):
        """Delete queue replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueReplicateEnqueue(self, request, context):
        """Publish message replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueReplicateSubscribe(self, request, context):
        """Subscribe user replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueReplicateUnsubscribe(self, request, context):
        """Unsubscribe user replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueueReplicateDequeue(self, request, context):
        """Dequeue message replication
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_QueueReplicationServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'QueueReplicateCreate': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateCreate,
                    request_deserializer=replication__service__pb2.CreateQueueRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'QueueReplicateDelete': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateDelete,
                    request_deserializer=replication__service__pb2.DeleteQueueRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'QueueReplicateEnqueue': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateEnqueue,
                    request_deserializer=replication__service__pb2.EnqueueRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'QueueReplicateSubscribe': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateSubscribe,
                    request_deserializer=replication__service__pb2.QueueSubscribeRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'QueueReplicateUnsubscribe': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateUnsubscribe,
                    request_deserializer=replication__service__pb2.QueueUnsubscribeRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
            'QueueReplicateDequeue': grpc.unary_unary_rpc_method_handler(
                    servicer.QueueReplicateDequeue,
                    request_deserializer=replication__service__pb2.DequeueRequest.FromString,
                    response_serializer=replication__service__pb2.ReplicationResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'app.grpc.QueueReplication', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('app.grpc.QueueReplication', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class QueueReplication(object):
    """Replication service for queues
    """

    @staticmethod
    def QueueReplicateCreate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateCreate',
            replication__service__pb2.CreateQueueRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueReplicateDelete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateDelete',
            replication__service__pb2.DeleteQueueRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueReplicateEnqueue(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateEnqueue',
            replication__service__pb2.EnqueueRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueReplicateSubscribe(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateSubscribe',
            replication__service__pb2.QueueSubscribeRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueReplicateUnsubscribe(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateUnsubscribe',
            replication__service__pb2.QueueUnsubscribeRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueueReplicateDequeue(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/app.grpc.QueueReplication/QueueReplicateDequeue',
            replication__service__pb2.DequeueRequest.SerializeToString,
            replication__service__pb2.ReplicationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
