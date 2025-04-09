from concurrent import futures
import grpc
import os
import redis
from app.domain.topics.topics_manager import MOMTopicManager
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.utils import TopicKeyBuilder
from app.grpc.replication_service_pb2 import ReplicationResponse, StatusCode
from app.grpc import replication_service_pb2_grpc

# Configuración de Redis (mantén tu lógica actual)
REDIS2_CONFIG = {
    'host': 'localhost',
    'port': 6380,
    'password': os.getenv('REDIS_PASSWORD'),
    'decode_responses': True
}

def create_redis2_connection():
    """Crea y retorna una conexión a redis2"""
    try:
        r = redis.Redis(**REDIS2_CONFIG)
        if r.ping():
            print("Conexión exitosa a redis2")
            return r
        raise ConnectionError("No se pudo conectar a redis2")
    except redis.AuthenticationError:
        print("Error de autenticación. Verifica la contraseña")
        return None
    except redis.ConnectionError:
        print("No se pudo conectar a redis2. Verifica si el servicio está corriendo")
        return None
    finally:
        r.close()

class TopicReplicationServicer(replication_service_pb2_grpc.TopicReplicationServicer):
    def TopicReplicateCreate(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )

            topic_manager = MOMTopicManager(db, request.owner)
            result = topic_manager.create_topic(
                topic_name=request.topic_name,
                principal=False,
                created_at=request.created_at
            )
            
            if not result.success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.status.value)
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message=result.status.value
                )
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Topic replicated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )
    
    def TopicReplicateDelete(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )
            
            topic_manager = MOMTopicManager(db, request.requester)
            
            # Verificar si el tópico existe
            metadata_key = TopicKeyBuilder.metadata_key(request.topic_name)
            if not db.exists(metadata_key):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Topic does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Topic does not exist"
                )

            # Solo el nodo principal puede eliminar un tópico
            if int(db.hget(metadata_key, "original_node")) != 0:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Permission denied"
                )
            
            result = topic_manager.delete_topic(
                topic_name=request.topic_name,
                principal=False
            )
            
            if not result.success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.status.value)
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message=result.status.value
                )
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Topic replicated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

    def TopicReplicatePublishMessage(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )
            
            topic_manager = MOMTopicManager(db, request.publisher)
            result = topic_manager.publish(
                message=request.message,
                topic_name=request.topic_name,
                timestamp=request.timestamp,
                im_replicating=True
            )
            
            if not result.success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.status.value)
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message=result.status.value
                )
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Message replicated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

    def TopicReplicateConsumeMessage(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )
            
            subscribers_key = TopicKeyBuilder.subscribers_key(request.topic_name)
            is_subscribed = db.sismember(subscribers_key, request.subscriber)
            if not is_subscribed:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details("User is not subscribed to this topic")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="User is not subscribed to this topic"
                )
            
            # Actualizar el offset del suscriptor
            offset_key = TopicKeyBuilder.subscriber_offsets_key(request.topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(request.subscriber)
        
            db.hset(offset_key, offset_field, request.offset)
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Offset updated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )
        
    def TopicReplicateSubscribe(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )

            subscribers_key = TopicKeyBuilder.subscribers_key(request.topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(request.topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(request.subscriber)
            
            metadata_key = TopicKeyBuilder.metadata_key(request.topic_name)
            if not db.exists(metadata_key):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Topic does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Topic does not exist"
                )
            
            if db.sismember(subscribers_key, request.subscriber):
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("User is already subscribed to this topic")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="User is already subscribed to this topic"
                )
            message_count = int(db.hget(metadata_key, "message_count") or 0)
            db.sadd(subscribers_key, request.subscriber)
            db.hset(offset_key, offset_field, message_count)
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="User subscribed successfully"
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

    def TopicReplicateUnsubscribe(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )
        
            subscribers_key = TopicKeyBuilder.subscribers_key(request.topic_name)
            offset_key = TopicKeyBuilder.subscriber_offsets_key(request.topic_name)
            offset_field = TopicKeyBuilder.subscriber_offset_field(request.subscriber)
            
            metadata_key = TopicKeyBuilder.metadata_key(request.topic_name)
            if not db.exists(metadata_key):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Topic does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Topic does not exist"
                )
            
            if not db.sismember(subscribers_key, request.subscriber):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User is not subscribed to this topic")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="User is not subscribed to this topic"
                )
            
            owner = db.hget(metadata_key, "owner")
            if request.subscriber == owner:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Topic owner cannot unsubscribe")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Topic owner cannot unsubscribe"
                )
            
            db.srem(subscribers_key, request.subscriber)
            db.hdel(offset_key, offset_field)
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="User unsubscribed successfully"
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

class QueueReplicationServicer(replication_service_pb2_grpc.QueueReplicationServicer):
    def QueueReplicateCreate(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )

            queue_manager = MOMQueueManager(db, request.owner)
            result = queue_manager.create_queue(
                queue_name=request.queue_name,
                principal=False,
                created_at=request.created_at
            )
            
            if not result.success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.status.value)
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message=result.status.value
                )
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Queue replicated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )
        
    def QueueReplicateDelete(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )

            queue_manager = MOMQueueManager(db, request.requester)
            result = queue_manager.delete_queue(
                queue_name=request.queue_name,
            )            
            
            if not result.success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.status.value)
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message=result.status.value
                )
            
            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Queue replicated successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replication_service_pb2_grpc.add_TopicReplicationServicer_to_server(
        TopicReplicationServicer(), server
    )
    replication_service_pb2_grpc.add_QueueReplicationServicer_to_server(
        QueueReplicationServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()