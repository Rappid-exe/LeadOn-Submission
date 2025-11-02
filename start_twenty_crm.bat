@echo off
echo ========================================
echo Starting Twenty CRM
echo ========================================
echo.
echo This will start Twenty CRM using Docker Compose
echo.
echo Services:
echo - Frontend: http://localhost:3001
echo - Backend API: http://localhost:3000
echo - GraphQL: http://localhost:3000/graphql
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd CRM\twenty\packages\twenty-docker
docker-compose up

pause

