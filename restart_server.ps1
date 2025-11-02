# Restart LeadOn CRM Server

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "🔄 Restarting LeadOn CRM Server..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Kill any existing Python processes on port 8000
Write-Host "Stopping existing server..." -ForegroundColor Yellow
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connections) {
    $connections | ForEach-Object {
        $processId = $_.OwningProcess
        Write-Host "  Killing process $processId" -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Start the server with auto-reload
Write-Host "`nStarting server with auto-reload..." -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

uvicorn crm_integration.chat_api:app --reload --host 0.0.0.0 --port 8000

