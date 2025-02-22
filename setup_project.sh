#!/bin/bash

echo "Setting up Rational Onion project structure..."

# 1. Create base directories
echo "Creating directory structure..."
mkdir -p .venv
mkdir -p uv
mkdir -p rational_onion/{api,models,services}
mkdir -p tests
mkdir -p frontend/{src,public}

# 2. Create API files (FastAPI Application Structure)
echo "Setting up API layer..."
# Main FastAPI entry point and routers
touch rational_onion/api/main.py
touch rational_onion/api/__init__.py

# Argument processing and analysis endpoints
touch rational_onion/api/argument_processing.py    # Insert and retrieve Toulmin model arguments
touch rational_onion/api/argument_verification.py  # Structural checks and contradiction detection
touch rational_onion/api/argument_improvement.py   # NLP-based suggestions and quality scoring

# External services and visualization
touch rational_onion/api/external_references.py    # Scholarly source queries and ranking
touch rational_onion/api/dag_visualization.py      # Graph visualization endpoints

# 3. Create model files (Data Models)
echo "Setting up data models..."
touch rational_onion/models/__init__.py
touch rational_onion/models/toulmin_model.py      # Toulmin argument structure models
touch rational_onion/models/dag_models.py         # Graph representation models

# 4. Create service files (External Services Integration)
echo "Setting up service integrations..."
touch rational_onion/services/__init__.py
touch rational_onion/services/neo4j_service.py    # Neo4j database integration
touch rational_onion/services/caching_service.py  # Redis caching service
touch rational_onion/services/nlp_service.py      # NLP processing with spacy and sentence-transformers

# 5. Create test files
echo "Setting up test suite..."
touch tests/__init__.py
touch tests/test_api.py          # API endpoint tests
touch tests/test_verification.py # Argument verification tests
touch tests/test_dag.py         # Graph visualization tests

# 6. Create frontend files
echo "Setting up frontend..."
touch frontend/src/ArgumentDAG.jsx  # Graph visualization component
touch frontend/src/index.js
touch frontend/package.json

# 7. Create configuration files
echo "Creating configuration files..."
touch requirements.uv
touch .env.example
touch docker-compose.yml
touch README.md

# Make the setup script executable
chmod +x setup.sh

# Initialize main FastAPI application with proper imports
cat > rational_onion/api/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import route handlers
from .argument_processing import router as argument_router
from .argument_verification import router as verification_router
from .argument_improvement import router as improvement_router
from .external_references import router as references_router
from .dag_visualization import router as visualization_router

app = FastAPI(
    title="Rational Onion API",
    description="API for argument analysis and visualization using Toulmin model",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(argument_router, prefix="/api/arguments", tags=["arguments"])
app.include_router(verification_router, prefix="/api/verify", tags=["verification"])
app.include_router(improvement_router, prefix="/api/improve", tags=["improvement"])
app.include_router(references_router, prefix="/api/references", tags=["references"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Rational Onion API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
EOF

# Initialize .env.example with comprehensive configuration
cat > .env.example << 'EOF'
# API Configuration
API_HOST=localhost
API_PORT=8000
DEBUG=true

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CACHE_ENABLED=true
CACHE_TTL=3600

# NLP Services
SPACY_MODEL=en_core_web_md
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2

# External Services
OPENAI_API_KEY=your_api_key_here
SCHOLARLY_API_KEY=your_api_key_here

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
EOF

# Initialize docker-compose.yml with service configurations
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  neo4j:
    image: neo4j:5.7
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_dbms_memory_pagecache_size: 1G
      NEO4J_dbms_memory_heap_initial__size: 1G
      NEO4J_dbms_memory_heap_max__size: 1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_plugins:/plugins

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_plugins:
  redis_data:
EOF

# Initialize package.json for frontend with visualization dependencies
cat > frontend/package.json << 'EOF'
{
  "name": "rational-onion-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@emotion/react": "^11.10.6",
    "@emotion/styled": "^11.10.6",
    "@mui/material": "^5.12.1",
    "@mui/icons-material": "^5.12.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-flow-renderer": "^10.3.17",
    "cytoscape": "^3.23.0",
    "axios": "^1.3.6",
    "lodash": "^4.17.21"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  }
}
EOF

# Initialize README.md with comprehensive documentation
cat > README.md << 'EOF'
# Rational Onion

A sophisticated argument analysis and visualization tool that helps users construct, analyze, and improve their arguments using the Toulmin model and graph-based representations.

## Features

- Argument Processing & Analysis
  - Toulmin model implementation
  - Structural verification
  - Contradiction detection
  - Quality scoring
- NLP-Enhanced Suggestions
  - Argument improvement recommendations
  - Query expansion
- External Reference Integration
  - Scholarly source queries
  - Reference ranking
- Interactive Visualization
  - DAG-based argument visualization
  - Real-time updates

## Project Structure

- `rational_onion/`
  - `api/`: FastAPI endpoints
    - `main.py`: Application entry point
    - `argument_processing.py`: Toulmin model operations
    - `argument_verification.py`: Structural checks
    - `argument_improvement.py`: NLP-based improvements
    - `external_references.py`: Source integration
    - `dag_visualization.py`: Graph visualization
  - `models/`: Data structures
    - `toulmin_model.py`: Argument models
    - `dag_models.py`: Graph models
  - `services/`: External integrations
    - `neo4j_service.py`: Graph database
    - `caching_service.py`: Redis caching
    - `nlp_service.py`: NLP processing
- `tests/`: Test suite
- `frontend/`: React-based interface

## Setup

1. Create and activate virtual environment:
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   ./setup.sh
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start services:
   ```bash
   docker-compose up -d
   uvicorn rational_onion.api.main:app --reload
   ```

## Development

- API documentation: http://localhost:8000/docs
- Frontend development: http://localhost:3000
- Neo4j browser: http://localhost:7474
- Redis Commander: http://localhost:8081

## Testing

```bash
pytest tests/
```

## License

MIT
EOF

echo "Project structure created successfully!"
echo "Next steps:"
echo "1. Run './setup.sh' to install dependencies"
echo "2. Configure your .env file"
echo "3. Start the services with docker-compose" 