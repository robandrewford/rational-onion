# rational_onion/api/main.py

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Local imports
from rational_onion.services.neo4j_service import driver
from rational_onion.services.caching_service import caching_enabled, toggle_cache
from rational_onion.api.argument_processing import router as argument_processing_router
from rational_onion.api.argument_verification import router as argument_verification_router
from rational_onion.api.argument_improvement import router as argument_improvement_router
from rational_onion.api.external_references import router as external_references_router
from rational_onion.api.dag_visualization import router as dag_visualization_router

load_dotenv()

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

VALID_API_KEYS = os.getenv("VALID_API_KEYS", "").split(",")

def authenticate_api_key(api_key: str = Security(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# FastAPI app initialization
app = FastAPI(
    title="Argumentation Pipeline API",
    version="2.0",
    description="API for managing Toulmin argument structures with visualization support and front-end integration."
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

# You can define a root endpoint for health checks
@app.get("/")
def root():
    return {"message": "Welcome to the Rational-Onion API!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)