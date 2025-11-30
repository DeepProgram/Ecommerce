# E-commerce Backend

A FastAPI-based e-commerce backend with product management, media handling (Cloudinary), and Elasticsearch-powered search.

## Features

- Product and variant management
- Image and video uploads with Cloudinary
- Full-text search with Elasticsearch
- Alembic database migrations
- Docker-based development environment

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Search**: Elasticsearch
- **Media Storage**: Cloudinary
- **ORM**: SQLAlchemy
- **Migrations**: Alembic

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

2. Start services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

4. Access the API:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Kibana: http://localhost:5601

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── core/                # Core configuration and database
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── api/                 # API routes
├── services/            # Business logic
└── utils/              # Utility functions
```

