"""
Zookeeper and node configuration loader.
"""

import os

NODE_ID = os.getenv("NODE_ID", "mom-unknown")
NODE_HOST = os.getenv("NODE_HOST", "http://localhost:8000")

ZOOKEEPER_HOST = os.getenv("ZOOKEEPER_HOST", "localhost")
ZOOKEEPER_PORT = os.getenv("ZOOKEEPER_PORT", "2181")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
