@echo off
echo ============================================================
echo Starting LeadOn CRM Server with Job Enrichment
echo ============================================================
echo.
echo Features:
echo   - Claude AI for intent parsing
echo   - Apollo.io for contact data
echo   - Job postings enrichment (LinkedIn scraping)
echo   - AI-powered company matching
echo   - Dual database (Companies + People)
echo.
echo Server will start on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python crm_integration\chat_api.py

