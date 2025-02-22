# Rational Onion

A sophisticated argument analysis and visualization tool that helps users construct, analyze, and improve their arguments using the Toulmin model and graph-based representations.

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

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the services:
   ```bash
   docker-compose up -d  # If using containerized services
   uvicorn rational_onion.api.main:app --reload
   ```

## Project Structure

- `rational_onion/`: Main Python package
  - `api/`: FastAPI endpoints and request handling
  - `models/`: Data models and Toulmin argument structures
  - `services/`: External service integrations (Neo4j, Redis, NLP)
- `tests/`: Test suite
- `frontend/`: React-based web interface

## Development

- API documentation available at: http://localhost:8000/docs
- Frontend development server: http://localhost:3000

## License

MIT
