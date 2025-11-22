# MavunoSure Backend

FastAPI backend services for claim verification platform.

## Setup

### Local Development (without Docker)

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp ../.env.example ../.env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

### With Docker

```bash
docker-compose up backend
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── celery_app.py        # Celery configuration
│   ├── api/                 # API routes
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── farms.py
│   │   │   ├── claims.py
│   │   │   └── reports.py
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── satellite_service.py
│   │   ├── weighted_algorithm.py
│   │   └── payment_service.py
│   └── core/                # Core utilities
│       ├── security.py
│       └── dependencies.py
├── alembic/                 # Database migrations
├── tests/
├── Dockerfile
└── requirements.txt
```

## Testing

```bash
pytest
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```
