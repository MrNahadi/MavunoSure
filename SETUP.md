# MavunoSure Platform Setup Guide

This guide will help you set up the complete MavunoSure development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker & Docker Compose** (for backend services)
- **Python 3.11+** (for backend development)
- **Node.js 18+** (for web dashboard)
- **Android Studio Hedgehog (2023.1.1)+** (for mobile app)
- **JDK 17** (for Android development)
- **Git**

## Quick Start (Docker)

The fastest way to get started is using Docker Compose:

1. Clone the repository
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your configuration (at minimum, set JWT_SECRET_KEY)
4. Start all services:
   ```bash
   docker-compose up -d
   ```

This will start:
- PostgreSQL database on port 5432
- Redis on port 6379
- Backend API on port 8000
- Celery worker for async tasks

## Component Setup

### 1. Backend (FastAPI)

#### Using Docker (Recommended for Development)
```bash
docker-compose up backend
```

#### Manual Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Web Dashboard (React + TypeScript)

```bash
cd web

# Install dependencies
npm install
# or: yarn install
# or: pnpm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

Dashboard will be available at: http://localhost:5173

### 3. Mobile App (Android)

1. Open Android Studio
2. Select "Open an Existing Project"
3. Navigate to the `mobile` folder
4. Wait for Gradle sync to complete
5. Create `local.properties` if it doesn't exist:
   ```
   sdk.dir=/path/to/your/Android/sdk
   ```
6. Build and run on emulator or device

**Note:** The app is configured to connect to `http://10.0.2.2:8000` (Android emulator localhost) by default.

## Environment Configuration

### Required Environment Variables

Edit `.env` file with the following minimum configuration:

```bash
# Database (auto-configured for Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mavunosure
POSTGRES_USER=mavunosure_user
POSTGRES_PASSWORD=your_secure_password_here

# JWT (REQUIRED - generate a secure random key)
JWT_SECRET_KEY=your_very_secure_random_secret_key_here

# Redis (auto-configured for Docker)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Optional Services (for full functionality)

```bash
# Africa's Talking SMS API
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key

# Google Earth Engine (for satellite data)
GEE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_PATH=/path/to/service-account-key.json

# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=mavunosure-claims
AWS_REGION=us-east-1
```

## Database Setup

### Using Docker
Database is automatically created and initialized when you run `docker-compose up`.

### Manual Setup
```bash
# Create PostgreSQL database
createdb mavunosure

# Run migrations
cd backend
alembic upgrade head
```

## Verification

### Check Backend
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Check Database
```bash
docker-compose exec postgres psql -U mavunosure_user -d mavunosure -c "\dt"
# Should list database tables after migrations
```

### Check Redis
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

## Development Workflow

### Backend Development
1. Make code changes in `backend/app/`
2. Server auto-reloads with `--reload` flag
3. Run tests: `pytest`
4. Create migrations: `alembic revision --autogenerate -m "description"`

### Web Development
1. Make code changes in `web/src/`
2. Vite hot-reloads automatically
3. Build for production: `npm run build`

### Mobile Development
1. Make code changes in `mobile/app/src/`
2. Android Studio auto-builds
3. Run on emulator or device
4. Run tests: `./gradlew test`

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `docker-compose ps`
- Check environment variables in `.env`
- Check logs: `docker-compose logs backend`

### Database connection errors
- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Check credentials in `.env` match docker-compose.yml
- Try: `docker-compose down -v && docker-compose up -d`

### Mobile app can't connect to API
- Ensure backend is running on port 8000
- For emulator, use `http://10.0.2.2:8000`
- For physical device, use your computer's IP address
- Check `mobile/app/build.gradle.kts` API_BASE_URL configuration

### Web dashboard can't connect to API
- Check VITE_API_BASE_URL in `web/.env.local`
- Ensure CORS is configured in backend (check `app/config.py`)
- Check browser console for errors

## Next Steps

After setup is complete:

1. Review the [Requirements](.kiro/specs/mavunosure-platform/requirements.md)
2. Review the [Design](.kiro/specs/mavunosure-platform/design.md)
3. Check [Implementation Tasks](.kiro/specs/mavunosure-platform/tasks.md)
4. Start implementing features following the task list

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- React Documentation: https://react.dev/
- Jetpack Compose: https://developer.android.com/jetpack/compose
- Docker Compose: https://docs.docker.com/compose/
