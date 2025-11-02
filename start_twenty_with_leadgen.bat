@echo off
echo ========================================
echo   Twenty CRM with Lead Gen Integration
echo ========================================
echo.

echo Step 1: Starting Python FastAPI Service...
echo.
start cmd /k "cd /d %~dp0 && python crm_integration/chat_api.py"
timeout /t 3 /nobreak >nul

echo Step 2: Starting Twenty CRM...
echo.
echo Please run these commands in a separate terminal:
echo.
echo   cd CRM/twenty
echo   yarn install
echo   yarn start
echo.

echo ========================================
echo   Services Starting...
echo ========================================
echo.
echo Python API: http://localhost:8000
echo Twenty CRM: http://localhost:3001
echo.
echo Once Twenty CRM is running:
echo 1. Open http://localhost:3001
echo 2. Navigate to People page
echo 3. Click the blue robot button (bottom-right)
echo 4. Start chatting!
echo.
echo Press any key to exit...
pause >nul

