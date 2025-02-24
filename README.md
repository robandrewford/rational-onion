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

- API documentation: <http://localhost:8000/docs>
- Frontend development: <http://localhost:3000>
- Neo4j browser: <http://localhost:7474>
- Redis Commander: <http://localhost:8081>

## Testing

```bash
pytest tests/
```

## License

MIT
