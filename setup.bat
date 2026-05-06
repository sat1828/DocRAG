@echo off
echo ========================================
echo Indian SME RAG - Automated Setup
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] Setting up Python Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
echo Installing Python dependencies (this takes 3-5 minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Python dependencies failed to install
    pause
    exit /b 1
)
cd ..

echo.
echo [2/6] Setting up Frontend...
cd frontend
echo Installing Node.js dependencies (this takes 2-3 minutes)...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed. Make sure Node.js is installed.
    pause
    exit /b 1
)
cd ..

echo.
echo [3/6] Creating environment files...
if not exist backend\.env (
    copy backend\.env.example backend\.env
    echo Created backend\.env
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo NEXT STEPS:
echo.
echo Option 1: Run with Docker (Recommended)
echo   1. Start Docker Desktop
echo   2. Run: docker-compose up --build
echo   3. Access: http://localhost:3000
echo.
echo Option 2: Run Locally (Requires PostgreSQL + Ollama)
echo   1. Install PostgreSQL 16
echo   2. Install Ollama: https://ollama.com
echo   3. Run: ollama pull llama3.3:8b
echo   4. Run Backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo   5. Run Frontend: cd frontend ^&^& npm run dev
echo   6. Access: http://localhost:3000
echo.
echo For detailed instructions, see SETUP.md
echo.
pause
