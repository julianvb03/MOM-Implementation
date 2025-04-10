"""Environment configuration settings for the FastAPI application."""

import os

# Basic configuration
API_NAME = os.getenv('API_NAME')
API_VERSION = os.getenv('API_VERSION')
JWT_SECRET = os.getenv('JWT_SECRET')  # The JWT secret string
PRODUCTION_SERVER_URL = os.getenv('PRODUCTION_SERVER_URL')
DEVELOPMENT_SERVER_URL = os.getenv('DEVELOPMENT_SERVER_URL')
LOCALHOST_SERVER_URL = os.getenv('LOCALHOST_SERVER_URL')

# Database configuration
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

# Users Database configuration
REDIS_USERS_PASSWORD = os.getenv('REDIS_USERS_PASSWORD')
REDIS_USERS_HOST = os.getenv('REDIS_USERS_HOST')
REDIS_USERS_PORT = os.getenv('REDIS_USERS_PORT')

# Default user configuration
DEFAULT_USER_PASSWORD = os.getenv('DEFAULT_USER_PASSWORD')
DEFAULT_USER_NAME = os.getenv('DEFAULT_USER_NAME')

# Cluster communication
NODE_A_IP = os.getenv('NODE_A_IP', 'localhost')
NODE_B_IP = os.getenv('NODE_B_IP', 'localhost')
NODE_C_IP = os.getenv('NODE_C_IP', 'localhost')
GRPC_PORT = os.getenv('GRPC_PORT', '50051')
WHOAMI = os.getenv('WHOAMI', 'A')

