@echo off
REM MavunoSure Development Environment Initialization Script for Windows

echo 🌱 Initializing MavunoSure Development Environment...

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration before proceeding!
    echo    At minimum, set a secure JWT_SECRET_KEY
    exit /b 1
)

REM Start Docker services
echo 🐳 Starting Docker services (PostgreSQL, Redis)...
docker-compose up -d postgres redis

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak > nul

REM Check if backend venv exists
if not exist backend\venv (
    echo 🐍 Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    echo 📦 Installing Python dependencies...
    pip install -r requirements.txt
    cd ..
) else (
    echo ✅ Python virtual environment already exists
)

REM Run database migrations
echo 🗄️  Running database migrations...
cd backend
call venv\Scripts\activate
alembic upgrade head
cd ..

REM Check if web node_modules exists
if not exist web\node_modules (
    echo 📦 Installing web dashboard dependencies...
    cd web
    npm install
    cd ..
) else (
    echo ✅ Web dependencies already installed
)

echo.
echo ✅ Development environment initialized successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys and secrets
echo 2. Start backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo 3. Start web dashboard: cd web ^&^& npm run dev
echo 4. Open mobile app in Android Studio
echo.
echo Or use Docker Compose to start everything:
echo   docker-compose up
echo.
