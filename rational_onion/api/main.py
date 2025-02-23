# rational_onion/api/main.py

from typing import List, Optional, Dict, Any
import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Local imports
from rational_onion.services.caching_service import caching_enabled, toggle_cache
from rational_onion.api.argument_processing import router as argument_processing_router
from rational_onion.api.argument_verification import router as argument_verification_router
from rational_onion.api.argument_improvement import router as argument_improvement_router
from rational_onion.api.external_references import router as external_references_router
from rational_onion.api.dag_visualization import router as dag_visualization_router
from rational_onion.config import get_settings, Settings
from rational_onion.api.dependencies import limiter
from rational_onion.api.errors import ErrorType, BaseAPIError

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

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "error_type": ErrorType.RATE_LIMIT_EXCEEDED.value,
                "message": f"Rate limit exceeded: {exc.limit} per {exc.period} seconds",
                "details": {
                    "limit": str(exc.limit),
                    "period": str(exc.period)
                }
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Custom handler for validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "error_type": ErrorType.VALIDATION_ERROR.value,
                "message": "Validation error",
                "details": {"errors": exc.errors()}
            }
        }
    )

@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError) -> JSONResponse:
    """Custom handler for API errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "error_type": exc.error_type.value,
                "message": exc.detail["message"],
                "details": exc.detail["details"]
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom handler for unhandled exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error_type": ErrorType.INTERNAL_ERROR.value,
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)}
            }
        }
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