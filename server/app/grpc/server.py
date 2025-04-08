from concurrent import futures
import grpc
import os
import redis
from app.domain.topics.topics_manager import MOMTopicManager
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
    
    def TopicReplicateDelete(self, request, context):
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

    def TopicReplicatePublishMessage(self, request, context):
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
            principal=False,
            timestamp=request.timestamp
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

    def TopicReplicateConsumeMessage(self, request, context):
        db = create_redis2_connection()
        if db is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Redis connection failed")
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message="Redis connection failed"
            )
        
        topic_manager = MOMTopicManager(db, request.subscriber)
        
        # Actualizar el offset del suscriptor
        offset_key = TopicKeyBuilder.subscriber_offsets_key(request.topic_name)
        offset_field = TopicKeyBuilder.subscriber_offset_field(request.subscriber)
        
        try:
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

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replication_service_pb2_grpc.add_TopicReplicationServicer_to_server(
        TopicReplicationServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()