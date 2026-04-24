# ContadorMX — Parar todos los servicios
# Uso: .\stop.ps1

$ROOT = $PSScriptRoot

Write-Host ""
Write-Host "  Deteniendo ContadorMX..." -ForegroundColor Yellow

# Cerrar ventanas de cmd con título ContadorMX
Get-Process "cmd" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "ContadorMX*"
} | ForEach-Object {
    Write-Host "  Cerrando: $($_.MainWindowTitle)" -ForegroundColor DarkGray
    $_.CloseMainWindow() | Out-Null
    Start-Sleep -Milliseconds 500
    if (-not $_.HasExited) { $_.Kill() }
}

# Matar procesos uvicorn y node que puedan quedar huérfanos
Get-Process "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*next*" -or $_.CommandLine -like "*contadormx*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Bajar Docker
Write-Host "  Deteniendo Docker..." -ForegroundColor DarkGray
Push-Location $ROOT
docker compose down 2>$null
if ($LASTEXITCODE -ne 0) { docker-compose down 2>$null }
Pop-Location

Write-Host ""
Write-Host "  ContadorMX detenido." -ForegroundColor Green
Write-Host ""
