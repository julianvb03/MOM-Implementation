"""
This file contains the main FastAPI application for the API.
The FastAPI application is configured with CORS middleware, 
rate limiting, and custom OpenAPI documentation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config.env import (
    API_NAME,
    PRODUCTION_SERVER_URL,
    DEVELOPMENT_SERVER_URL,
    LOCALHOST_SERVER_URL,
    API_VERSION
)
from app.config.limiter import limiter
from app.dtos.admin.mom_management_dto import QueueTopic
from app.routes.admin.mom_management.routes import router as admin_mom_management_router
from app.routes.admin.routes import router as admin_router
from app.routes.mom.routes import router as mom_router
from app.routes.routes import router
from app.utils.db import initialize_database, backup_database

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Executes setup and teardown logic for the app, like DB and Zookeeper.
    """
    print("🚀 API started")

    # Initialize DB
    initialize_database()
    
    # Backup DB
    # TODO: Replace element for endpoint call to zookeeper
    elements = [
        QueueTopic(
            name="queue-example",
            type="queue",
        ),
        QueueTopic(
            name="topic-example",
            type="topic",
        )
    ]
    backup_database(elements)

    yield  # Let the app run

    # On shutdown
    print("🛑 API shutting down...")

# FastAPI Metadata
title = f"{API_NAME} API"
description = (
    f"{API_NAME} is an API REST which receives requests from clients "
    "wanting to connect to a message queue/topic in a MOM system."
)
version = f"{API_VERSION}"
servers = [
    {"url": LOCALHOST_SERVER_URL, "description": "Localhost server"},
    {"url": DEVELOPMENT_SERVER_URL, "description": "Development server"},
    {"url": PRODUCTION_SERVER_URL, "description": "Production server"},
]
contact = {
    "name": "Juan Felipe Restrepo Buitrago",
    "email": "jfrestrepb@eafit.edu.co",
}
license_info = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

# FastAPI instance
app = FastAPI(
    openapi_url=f"/api/{API_VERSION}/{API_NAME}/openapi.json",
    docs_url=f"/api/{API_VERSION}/{API_NAME}/docs",
    redoc_url=f"/api/{API_VERSION}/{API_NAME}/redoc",
    servers=servers,
    title=title,
    description=description,
    version=version,
    contact=contact,
    license_info=license_info,
    lifespan=lifespan
)

# Custom OpenAPI logo (optional)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
        servers=servers,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "..."  # Add your logo URL here
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Rate Limiting Middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix=f"/api/{API_VERSION}/{API_NAME}")
app.include_router(admin_router, prefix=f"/api/{API_VERSION}/{API_NAME}/admin")
app.include_router(
    admin_mom_management_router,
    prefix=f"/api/{API_VERSION}/{API_NAME}/admin"
)
app.include_router(
    mom_router,
    prefix=f"/api/{API_VERSION}/{API_NAME}/queue_topic"
)
