@echo off
echo Starting LeadOn CRM API Server...
echo.
echo API will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:8000/frontend
echo API Docs: http://localhost:8000/docs
echo.
python crm_integration/api.py
pause

