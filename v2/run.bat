@echo off
REM Script to build and run Acestream Scraper v2

echo === Building and running Acestream Scraper v2 ===

REM Navigate to project root
cd %~dp0

REM Check if we're in v2 directory
if not exist "frontend" (
  echo Error: This script must be run from the v2 directory.
  exit /b 1
)

REM Build frontend
echo === Building frontend ===
cd frontend
call npm install
call npm run build:backend
if %ERRORLEVEL% neq 0 (
  echo Error: Frontend build failed.
  exit /b 1
)

REM Navigate to backend
cd ..\backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
  echo === Creating Python virtual environment ===
  python -m venv venv
)

REM Activate virtual environment
echo === Activating virtual environment ===
call venv\Scripts\activate

REM Install backend dependencies
echo === Installing backend dependencies ===
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
  echo Error: Failed to install backend dependencies.
  exit /b 1
)

REM Run the application
echo === Starting the application ===
echo The application will be available at http://localhost:8000
echo Press Ctrl+C to stop the server.
python main.py

REM Deactivate virtual environment on exit
deactivate
