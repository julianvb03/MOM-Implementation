"""
Test cases for the MOMQueueManager class
"""

from app.adapters.db import Database
from app.adapters.factory import ObjectFactory
import redis
import os
import json
import pytest
import time
from datetime import datetime, timedelta
from app.domain.models import MOMQueueStatus 
from app.domain.queues.queues_manager import MOMQueueManager
from app.domain.utils import KeyBuilder

# Configuración de Redis para el nodo principal y réplica
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': os.getenv('REDIS_PASSWORD'),
    'decode_responses': True
}

REDIS2_CONFIG = {
    'host': 'localhost',
    'port': 6380,
    'password': os.getenv('REDIS_PASSWORD'),
    'decode_responses': True
}

def create_redis_connection(config):
    """Crea y retorna una conexión a Redis"""
    try:
        r = redis.Redis(**config)
        if r.ping():
            print(f"Conexion exitosa a Redis en puerto {config['port']}")
            return r
        raise ConnectionError(f"No se pudo conectar a Redis en puerto {config['port']}")
    except redis.AuthenticationError:
        print("Error de autenticación. Verifica la contraseña")
        return None
    except redis.ConnectionError:
        print(f"No se pudo conectar a Redis en puerto {config['port']}")
        return None

@pytest.fixture(name="redis_connection")
def redis_connection_fixture():
    """Fixture para la conexión a Redis principal"""
    return create_redis_connection(REDIS_CONFIG)

@pytest.fixture(name="redis2_connection")
def redis2_connection_fixture():
    """Fixture para la conexión a Redis réplica"""
    return create_redis_connection(REDIS2_CONFIG)

@pytest.fixture(name="queue_manager")
def queue_manager_fixture(redis_connection):
    """Fixture para el MOMQueueManager del nodo principal"""
    return MOMQueueManager(redis_connection, "test_user")

@pytest.fixture(name="queue_manager_replica")
def queue_manager_replica_fixture(redis2_connection):
    """Fixture para el MOMQueueManager del nodo réplica"""
    return MOMQueueManager(redis2_connection, "test_user")

def test_create_queue(queue_manager, redis_connection, redis2_connection):
    """Test crear una cola y verificar su replicación"""
    queue_name = "test_queue"
    result = queue_manager.create_queue(queue_name)
    
    assert result.success is True
    assert result.status == MOMQueueStatus.QUEUE_CREATED
    
    # Verificar en Redis principal
    metadata_key = KeyBuilder.metadata_key(queue_name)
    assert redis_connection.exists(metadata_key) == 1
    
    # Verificar en Redis réplica
    assert redis2_connection.exists(metadata_key) == 1
    
    # Verificar metadatos
    metadata = redis_connection.hgetall(metadata_key)
    assert metadata["name"] == queue_name
    assert metadata["owner"] == "test_user"
    assert metadata["original_node"] == "1"  # Es el nodo principal

def test_enqueue_message(queue_manager, redis_connection, redis2_connection):
    """Test encolar un mensaje y verificar su replicación"""
    queue_name = "test_queue"
    message = "Test message"
    
    # Crear la cola primero
    queue_manager.create_queue(queue_name)
    
    # Encolar mensaje
    result = queue_manager.enqueue(message, queue_name)
    assert result.success is True
    
    # Verificar en Redis principal
    queue_key = KeyBuilder.queue_key(queue_name)
    messages = redis_connection.lrange(queue_key, 0, -1)
    assert len(messages) == 1
    
    # Verificar en Redis réplica
    messages_replica = redis2_connection.lrange(queue_key, 0, -1)
    assert len(messages_replica) == 1
    
    # Verificar contenido del mensaje
    message_data = json.loads(messages[0])
    assert json.loads(message_data["payload"]) == message
    assert message_data["id"] is not None
    assert message_data["timestamp"] is not None

def test_dequeue_message(queue_manager, queue_manager_replica, redis_connection, redis2_connection):
    """Test desencolar un mensaje y verificar su replicación"""
    queue_name = "test_queue"
    message = "Test message"
    
    # Crear la cola y encolar un mensaje
    queue_manager.create_queue(queue_name)
    queue_manager.enqueue(message, queue_name)
    
    # Desencolar desde el nodo principal
    result = queue_manager.dequeue(queue_name)
    assert result.success is True
    assert result.details == message
    
    # Verificar en Redis principal
    queue_key = KeyBuilder.queue_key(queue_name)
    assert redis_connection.llen(queue_key) == 0
    
    # Verificar en Redis réplica
    assert redis2_connection.llen(queue_key) == 0

def test_subscribe_to_queue(queue_manager, queue_manager_replica, redis_connection, redis2_connection):
    """Test suscribirse a una cola y verificar la replicación"""
    queue_name = "test_queue"
    
    # Crear la cola
    queue_manager.create_queue(queue_name)
    
    # Suscribirse desde el nodo réplica
    result = queue_manager_replica.subscriptions.subscribe(queue_name)
    assert result.success is True
    
    # Verificar en Redis principal
    subscribers_key = KeyBuilder.subscribers_key(queue_name)
    assert redis_connection.sismember(subscribers_key, "test_user") == 1
    
    # Verificar en Redis réplica
    assert redis2_connection.sismember(subscribers_key, "test_user") == 1

def test_unsubscribe_from_queue(queue_manager, queue_manager_replica, redis_connection, redis2_connection):
    """Test desuscribirse de una cola y verificar la replicación"""
    queue_name = "test_queue"
    
    # Crear la cola con el usuario principal
    queue_manager.create_queue(queue_name)
    
    # Crear un nuevo manager para un usuario diferente
    other_user_manager = MOMQueueManager(redis_connection, "other_user")
    other_user_manager_replica = MOMQueueManager(redis2_connection, "other_user")
    
    # Suscribir al otro usuario desde el nodo réplica
    result = other_user_manager_replica.subscriptions.subscribe(queue_name)
    assert result.success is True
    
    # Verificar que está suscrito en ambos nodos
    subscribers_key = KeyBuilder.subscribers_key(queue_name)
    assert redis_connection.sismember(subscribers_key, "other_user") == 1
    assert redis2_connection.sismember(subscribers_key, "other_user") == 1
    
    # Desuscribir al otro usuario desde el nodo réplica
    result = other_user_manager_replica.subscriptions.unsubscribe(queue_name)
    assert result.success is True
    
    # Verificar que ya no está suscrito en ambos nodos
    assert redis_connection.sismember(subscribers_key, "other_user") == 0
    assert redis2_connection.sismember(subscribers_key, "other_user") == 0

def test_delete_queue(queue_manager, redis_connection, redis2_connection):
    """Test eliminar una cola y verificar su replicación"""
    queue_name = "test_queue"
    
    # Crear la cola
    queue_manager.create_queue(queue_name)
    
    # Eliminar la cola
    result = queue_manager.delete_queue(queue_name)
    assert result.success is True
    
    # Verificar en Redis principal
    metadata_key = KeyBuilder.metadata_key(queue_name)
    queue_key = KeyBuilder.queue_key(queue_name)
    subscribers_key = KeyBuilder.subscribers_key(queue_name)
    
    assert redis_connection.exists(metadata_key) == 0
    assert redis_connection.exists(queue_key) == 0
    assert redis_connection.exists(subscribers_key) == 0
    
    # Verificar en Redis réplica
    assert redis2_connection.exists(metadata_key) == 0
    assert redis2_connection.exists(queue_key) == 0
    assert redis2_connection.exists(subscribers_key) == 0
