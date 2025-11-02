@echo off
echo ============================================================
echo LeadOn CRM - Claude Setup Script
echo ============================================================
echo.

echo Step 1: Installing dependencies...
pip install anthropic==0.39.0
if %errorlevel% neq 0 (
    echo ERROR: Failed to install anthropic package
    pause
    exit /b 1
)

echo.
echo Step 2: Installing all requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Your configuration:
echo   Claude API:  Configured
echo   Apollo API:  Configured
echo   Twenty CRM:  Optional (see TWENTY_CRM_SETUP.md)
echo.
echo Next steps:
echo   1. Start the server: python crm_integration/chat_api.py
echo   2. Open http://localhost:8000/
echo   3. Try: "Find CTOs at AI companies in San Francisco"
echo.
echo ============================================================
pause

