@echo off
echo ========================================
echo Starting LeadOn Chat CRM
echo ========================================
echo.
echo This will start the chat-based CRM interface
echo.
echo Services:
echo - Chat Interface: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python crm_integration/chat_api.py

pause

