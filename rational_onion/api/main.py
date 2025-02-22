# rational_onion/api/main.py

from typing import List, Optional

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

# Local imports
from rational_onion.services.neo4j_service import driver
from rational_onion.services.caching_service import caching_enabled, toggle_cache
from rational_onion.api.argument_processing import router as argument_processing_router
from rational_onion.api.argument_verification import router as argument_verification_router
from rational_onion.api.argument_improvement import router as argument_improvement_router
from rational_onion.api.external_references import router as external_references_router
from rational_onion.api.dag_visualization import router as dag_visualization_router
from rational_onion.config import get_settings, Settings

# FastAPI app initialization
settings = get_settings()

app = FastAPI(
    title="Rational Onion API",
    description="Structured argument analysis with LLM integration",
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# CORS Middleware for the front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to your domain or keep '*' for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers from other modules
app.include_router(argument_processing_router, tags=["Argument Processing"])
app.include_router(argument_verification_router, tags=["Argument Verification"])
app.include_router(argument_improvement_router, tags=["Argument Improvement"])
app.include_router(external_references_router, tags=["External References"])
app.include_router(dag_visualization_router, tags=["Visualization"])

# Optional: endpoint to toggle caching
app.post("/toggle-cache")(toggle_cache)

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the Rational-Onion API!"}

@app.get("/health")
async def health_check():
    """
    Check system health and component status.
    
    Verifies:
        - API availability
        - Database connectivity
        - Cache service status
        - NLP service readiness
        
    Returns:
        Dict containing:
            - status: Overall system health
            - version: API version
            - debug: Debug mode status
            - components: Individual service statuses
            
    Raises:
        ServiceError: If any critical component is unavailable
    """
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "debug": settings.DEBUG
    }

async def get_db():
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        database=settings.NEO4J_DATABASE,
        max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
        connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT,
        encrypted=settings.NEO4J_ENCRYPTION_ENABLED
    )
    try:
        yield driver
    finally:
        await driver.close()

if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)