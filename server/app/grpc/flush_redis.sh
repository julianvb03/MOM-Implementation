#!/bin/bash

# Verificar si REDIS_PASSWORD está definida
if [ -z "$REDIS_PASSWORD" ]; then
    echo "Error: REDIS_PASSWORD no está definida"
    exit 1
fi

echo "Limpiando base de datos Redis en puerto 6379..."
redis-cli -p 6379 -a $REDIS_PASSWORD FLUSHDB

echo "Limpiando base de datos Redis en puerto 6380..."
redis-cli -p 6380 -a $REDIS_PASSWORD FLUSHDB

echo "Limpiando archivo de logs..."
echo "" > ../domain/logs/Domain.log

echo "¡Bases de datos y logs limpiados exitosamente!" 