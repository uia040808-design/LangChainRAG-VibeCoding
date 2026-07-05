@echo off
chcp 936 >nul
title LangChain RAG Knowledge Base Q&A System

echo ========================================
echo   LangChain RAG Knowledge Base Q&A System
echo ========================================
echo.

:: Save project root directory
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

:: ===== Check Python =====
echo [Check] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python is ready
echo.

:: ===== Check Node.js =====
echo [Check] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    echo         Download: https://nodejs.org/zh-cn/
    pause
    exit /b 1
)
node --version
echo [OK] Node.js is ready
echo.

:: ===== Check .env file =====
if not exist "%BACKEND_DIR%\.env" (
    echo [Setup] First run: copying .env.example to .env
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo [Setup] Please configure your Alibaba Cloud Bailian API Key in:
    echo         %BACKEND_DIR%\.env
    echo         Get your key at: https://bailian.console.aliyun.com/
    echo.
    start notepad "%BACKEND_DIR%\.env"
    echo [Setup] After configuring the API Key, save the file and close Notepad
    echo          Then press any key to continue...
    pause >nul
)

:: ===== Install backend dependencies =====
echo [1/4] Installing backend Python dependencies...
cd /d "%BACKEND_DIR%"

if not exist "venv\" (
    echo        Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo        Virtual environment created
)

call venv\Scripts\activate.bat

echo        Installing packages (this may take a few minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend dependency installation failed!
    echo        Possible causes:
    echo        1. Network issues - check your internet connection
    echo        2. Try running this script again
    echo        3. If it keeps failing, try using a VPN or mirror site
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed
echo.

:: ===== Start backend =====
echo [2/4] Starting backend server (http://localhost:8000)...
start "LangChainRAG-Backend" /D "%BACKEND_DIR%" cmd /k "venv\Scripts\activate.bat && echo Backend starting... && uvicorn app.main:app --reload --port 8000"

:: Wait for backend to start
echo        Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul
echo [OK] Backend server should be running
echo.

:: ===== Install frontend dependencies =====
echo [3/4] Installing frontend Node.js dependencies...
cd /d "%FRONTEND_DIR%"

if not exist "node_modules\" (
    echo        First run: installing frontend dependencies (this may take several minutes)...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Frontend dependency installation failed!
        echo        Possible causes:
        echo        1. Network issues - check your internet connection
        echo        2. Try running: npm config set registry https://registry.npmmirror.com
        echo           (This uses a Chinese mirror for faster downloads)
        pause
        exit /b 1
    )
) else (
    echo        Frontend dependencies already installed, skipping...
)
echo [OK] Frontend dependencies ready
echo.

:: ===== Start frontend =====
echo [4/4] Starting frontend server (http://localhost:5173)...
start "LangChainRAG-Frontend" /D "%FRONTEND_DIR%" cmd /k "echo Frontend starting... && npm run dev"

:: Wait for frontend to start
echo        Waiting for frontend to start (5 seconds)...
timeout /t 5 /nobreak >nul

:: ===== Open browser =====
echo        Opening browser...
start http://localhost:5173

cd /d "%PROJECT_DIR%"

echo.
echo ========================================
echo   System startup complete!
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Admin:     admin / 123456
echo ========================================
echo.
echo NOTE: Two new windows will open for the backend and frontend.
echo       Close those windows to stop the servers.
echo.
echo Press any key to close this window (servers will keep running)...
pause >nul
