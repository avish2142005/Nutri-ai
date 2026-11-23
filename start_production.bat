@echo off
echo ==============================================================================
echo           Starting KrishiNetra Production Server
echo ==============================================================================
echo.

set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

echo [1/3] Checking Python virtual environment...
if not exist "farmai\backend\.venv\Scripts\python.exe" (
    echo Python virtual environment not found. Creating one...
    python -m venv farmai\backend\.venv
    call farmai\backend\.venv\Scripts\activate.bat
    pip install -r farmai\backend\requirements.txt
)

echo [2/3] Checking Frontend production build...
if not exist "farmai\frontend\dist\index.html" (
    echo Compiling React/Vite frontend bundle...
    cd farmai\frontend
    call npm install
    call npm run build
    cd /d "%ROOT_DIR%"
)

echo [3/3] Launching Production Server on http://127.0.0.1:8000 ...
echo KrishiNetra is live! Press Ctrl+C to stop.
echo.

cd farmai\backend
".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
