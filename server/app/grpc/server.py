from concurrent import futures
import grpc
import os
import redis
from app.domain.logger_config import logger
from app.domain.topics.topics_manager import MOMTopicManager
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.utils import TopicKeyBuilder, KeyBuilder
from app.grpc.replication_service_pb2 import ReplicationResponse, StatusCode
from app.grpc import replication_service_pb2_grpc
import json

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
        
    def QueueReplicateSubscribe(self, request, context):
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

            # Obtener la clave correcta de suscriptores
            subscribers_key = KeyBuilder.subscribers_key(request.queue_name)
            queue_key = KeyBuilder.metadata_key(request.queue_name)
            
            # Verificar si la cola existe
            if not db.exists(queue_key):
                logger.critical(f"La cola {queue_key} no existe")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Queue does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Queue does not exist"
                )
            
            # Verificar si el usuario ya está suscrito
            if db.sismember(subscribers_key, request.requester):
                logger.critical(f"El usuario {request.requester} ya está suscrito a la cola {request.queue_name}")
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("User is already subscribed to this queue")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="User is already subscribed to this queue"
                )

            # Suscribir al usuario
            db.sadd(subscribers_key, request.requester)
            
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
        
    def QueueReplicateUnsubscribe(self, request, context):
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
            
            # Obtener la clave correcta de suscriptores
            subscribers_key = KeyBuilder.subscribers_key(request.queue_name)
            queue_key = KeyBuilder.metadata_key(request.queue_name)
            
            # Verificar si la cola existe
            if not db.exists(queue_key):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Queue does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Queue does not exist"
                )

            # Verificar si el usuario está suscrito
            if not db.sismember(subscribers_key, request.requester):
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User is not subscribed to this queue")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="User is not subscribed to this queue"
                )

            # Eliminar la suscripción
            db.srem(subscribers_key, request.requester)
            
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

    def QueueReplicateEnqueue(self, request, context):
        try:
            db = create_redis2_connection()
            if db is None:
                logger.error("No se pudo conectar a Redis")
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Redis connection failed")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Redis connection failed"
                )
            
            logger.info(f"Recibida solicitud de encolamiento para cola: {request.queue_name}")
            queue_manager = MOMQueueManager(db, request.requester)
            
            # Verificar si la cola existe
            metadata_key = KeyBuilder.metadata_key(request.queue_name)
            if not db.exists(metadata_key):
                logger.error(f"La cola {request.queue_name} no existe")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Queue does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Queue does not exist"
                )

            result = queue_manager.enqueue(
                message=request.message,
                queue_name=request.queue_name,
                uuid=request.uuid,
                timestamp=request.timestamp,
                im_replicating=True
            )

            logger.info(f"Resultado de la replicación en el servidor: {result}")
            if not result.success:
                logger.error(f"Error en replicación: {result.status.value}")
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
                message="Message enqueued successfully"
            )
        
        except Exception as e:
            logger.error(f"Error inesperado en QueueReplicateEnqueue: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ReplicationResponse(
                success=False,
                status_code=StatusCode.REPLICATION_FAILED,
                message=str(e)
            )

    def QueueReplicateDequeue(self, request, context):
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
            
            logger.info(f"Recibida solicitud de desencolamiento para cola: {request.queue_name}")
            queue_manager = MOMQueueManager(db, request.requester)
            
            # Verificar si la cola existe
            metadata_key = KeyBuilder.metadata_key(request.queue_name)
            if not db.exists(metadata_key):
                logger.error(f"La cola {request.queue_name} no existe")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Queue does not exist")
                return ReplicationResponse(
                    success=False,
                    status_code=StatusCode.REPLICATION_FAILED,
                    message="Queue does not exist"
                )

            # Buscar el mensaje por UUID y desencolarlo
            queue_key = KeyBuilder.queue_key(request.queue_name)
            messages = db.lrange(queue_key, 0, -1)
            for i, msg in enumerate(messages):
                message = json.loads(msg)
                if message["id"] == request.uuid:
                    db.lset(queue_key, i, "__DELETED__")
                    db.lrem(queue_key, 1, "__DELETED__")
                    db.hincrby(metadata_key, "total_messages", -1)
                    break

            return ReplicationResponse(
                success=True,
                status_code=StatusCode.REPLICATION_SUCCESS,
                message="Message dequeued successfully"
            )
        
        except Exception as e:
            logger.error(f"Error inesperado en QueueReplicateDequeue: {str(e)}")
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