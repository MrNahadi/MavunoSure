#!/bin/bash

# MavunoSure Development Environment Initialization Script

set -e

echo "🌱 Initializing MavunoSure Development Environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before proceeding!"
    echo "   At minimum, set a secure JWT_SECRET_KEY"
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services (PostgreSQL, Redis)..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Python virtual environment already exists"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
cd ..

# Check if web node_modules exists
if [ ! -d "web/node_modules" ]; then
    echo "📦 Installing web dashboard dependencies..."
    cd web
    npm install
    cd ..
else
    echo "✅ Web dependencies already installed"
fi

echo ""
echo "✅ Development environment initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and secrets"
echo "2. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start web dashboard: cd web && npm run dev"
echo "4. Open mobile app in Android Studio"
echo ""
echo "Or use Docker Compose to start everything:"
echo "  docker-compose up"
echo ""
