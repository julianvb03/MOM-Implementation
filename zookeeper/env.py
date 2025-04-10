"""Environment configuration for Zookeeper service."""

import os

# App metadata
API_NAME = os.getenv("API_NAME", "MomServer")
API_VERSION = os.getenv("API_VERSION", "v1.0.0")

# Node identity
NODE_ID = os.getenv("NODE_ID", "mom-unknown")
NODE_HOST = os.getenv("NODE_HOST", "http://localhost:8000")

# Zookeeper connection
ZOOKEEPER_HOST = os.getenv("ZOOKEEPER_HOST", "localhost")
ZOOKEEPER_PORT = os.getenv("ZOOKEEPER_PORT", "2181")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
