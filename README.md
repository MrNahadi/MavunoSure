# MavunoSure Platform

B2B2C claim verification platform for smallholder farmer micro-insurance in Kenya.

## Project Structure

```
mavunosure-platform/
├── mobile/           # Android app (Kotlin + Jetpack Compose)
├── backend/          # FastAPI backend services
├── web/              # React TypeScript dashboard
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Android Studio (for mobile development)
- Node.js 18+ (for web development)
- Python 3.11+ (for backend development)

### Local Development

1. Start backend services:
```bash
docker-compose up -d
```

2. Backend API will be available at: http://localhost:8000
3. PostgreSQL at: localhost:5432
4. Redis at: localhost:6379

### Mobile App
See `mobile/README.md` for Android setup instructions.

### Web Dashboard
See `web/README.md` for React setup instructions.

### Backend
See `backend/README.md` for FastAPI setup instructions.

## Environment Variables

Copy `.env.example` to `.env` and configure:
- Database credentials
- API keys (Africa's Talking, Google Earth Engine)
- JWT secrets
- Storage credentials (S3/GCS)

## Documentation

- [Requirements](.kiro/specs/mavunosure-platform/requirements.md)
- [Design](.kiro/specs/mavunosure-platform/design.md)
- [Implementation Tasks](.kiro/specs/mavunosure-platform/tasks.md)
