"""
This module configures the rate limiting for the 
FastAPI application using the SlowAPI library.
It sets up a Limiter instance that uses the 
client's IP address as the key for rate limiting.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Create a Limiter instance for rate limiting
limiter = Limiter(key_func=get_remote_address)
