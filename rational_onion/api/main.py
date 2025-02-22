# rational_onion/api/main.py

from typing import List, Optional, Dict, Any
import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Local imports
from rational_onion.services.caching_service import caching_enabled, toggle_cache
from rational_onion.api.argument_processing import router as argument_processing_router
from rational_onion.api.argument_verification import router as argument_verification_router
from rational_onion.api.argument_improvement import router as argument_improvement_router
from rational_onion.api.external_references import router as external_references_router
from rational_onion.api.dag_visualization import router as dag_visualization_router
from rational_onion.config import get_settings, Settings
from rational_onion.api.dependencies import limiter

# FastAPI app initialization
settings = get_settings()

app = FastAPI(
    title="Rational Onion API",
    description="Structured argument analysis with LLM integration",
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# Add rate limiter to app state and middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Rational-Onion API!"}

@app.get("/health")
@limiter.limit(settings.RATE_LIMIT)
async def health_check(request: Request) -> Dict[str, Any]:
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

if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)