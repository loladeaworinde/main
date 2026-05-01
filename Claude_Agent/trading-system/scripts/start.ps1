# Quick start script for Windows PowerShell
# Run from the trading-system\ directory

$root = $PSScriptRoot | Split-Path

Write-Host "=== Trading System ===" -ForegroundColor Cyan

# Copy .env if it doesn't exist
if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
    Write-Host "Created .env from .env.example — fill in your API keys!" -ForegroundColor Yellow
}

Write-Host "Starting services..." -ForegroundColor Green
docker compose -f "$root\docker-compose.yml" up --build
