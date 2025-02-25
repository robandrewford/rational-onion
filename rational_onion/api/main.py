# rational_onion/api/main.py

from typing import List, Optional, Dict, Any
import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Request, Response
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from neo4j.exceptions import ServiceUnavailable, DatabaseError as Neo4jDatabaseError

# Local imports
from rational_onion.services.caching_service import caching_enabled, toggle_cache
from rational_onion.api.argument_processing import router as argument_processing_router
from rational_onion.api.argument_verification import router as argument_verification_router
from rational_onion.api.argument_improvement import router as argument_improvement_router
from rational_onion.api.external_references import router as external_references_router
from rational_onion.api.dag_visualization import router as dag_visualization_router
from rational_onion.config import get_settings, Settings
from rational_onion.api.dependencies import limiter
from rational_onion.api.errors import ErrorType, BaseAPIError, DatabaseError
from rational_onion.api.rate_limiting import rate_limit_exceeded_handler

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register rate limit handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return rate_limit_exceeded_handler(request, exc)

# Register validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors and return a consistent error format."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "error_type": ErrorType.VALIDATION_ERROR.value,
                "message": "Validation error",
                "errors": exc.errors()
            }
        }
    )

# Register database error handler
@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError) -> JSONResponse:
    """Handle API errors and return a consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Register database error handler
@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors and return a consistent error format."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error_type": ErrorType.DATABASE_ERROR.value,
                "message": str(exc)
            }
        }
    )

# Register Neo4j database error handler
@app.exception_handler(Neo4jDatabaseError)
async def neo4j_database_error_handler(request: Request, exc: Neo4jDatabaseError) -> JSONResponse:
    """Handle Neo4j database errors and return a consistent error format."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error_type": ErrorType.DATABASE_ERROR.value,
                "message": str(exc)
            }
        }
    )

# Include routers
app.include_router(argument_processing_router, tags=["Argument Processing"])
app.include_router(argument_verification_router, tags=["Argument Verification"])
app.include_router(argument_improvement_router, tags=["Argument Improvement"])
app.include_router(external_references_router, tags=["External References"])
app.include_router(dag_visualization_router, tags=["DAG Visualization"])

@app.get("/health")
@limiter.limit(settings.RATE_LIMIT)
async def health_check(request: Request, response: Response) -> Dict[str, Any]:
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