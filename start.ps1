# ContadorMX — Script de inicio completo
# Uso: .\start.ps1
# Requiere: Docker Desktop, Python 3.11+, Node 18+

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot

function Write-Step($msg) { Write-Host "  >> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  OK $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !! $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  ERR $msg" -ForegroundColor Red; exit 1 }

# ─────────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ┌─────────────────────────────────────┐" -ForegroundColor Green
Write-Host "  │        ContadorMX  Dev Stack         │" -ForegroundColor Green
Write-Host "  └─────────────────────────────────────┘" -ForegroundColor Green
Write-Host ""

# ── 1. Prerrequisitos ─────────────────────────────────────────────────────────
Write-Step "Verificando prerrequisitos..."

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Fail "Docker no encontrado. Instálalo desde https://docker.com/products/docker-desktop"
}

$pythonCmd = "python"
if (-not (Get-Command $pythonCmd -ErrorAction SilentlyContinue)) {
    $pythonCmd = "python3"
    if (-not (Get-Command $pythonCmd -ErrorAction SilentlyContinue)) {
        Write-Fail "Python no encontrado. Instálalo desde https://python.org"
    }
}

if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Fail "Node.js no encontrado. Instálalo desde https://nodejs.org"
}

Write-OK "Docker, Python y Node encontrados"

# ── 2. backend/.env ───────────────────────────────────────────────────────────
$backendEnv = "$ROOT\backend\.env"
if (-not (Test-Path $backendEnv)) {
    Copy-Item "$ROOT\backend\.env.example" $backendEnv
    Write-Warn "backend/.env creado desde .env.example"
    Write-Warn "Edita backend/.env y agrega tu ANTHROPIC_API_KEY antes de chatear"
} else {
    Write-OK "backend/.env existe"
}

# Advertencia si falta la API key
$envContent = Get-Content $backendEnv -Raw
if ($envContent -match "sk-ant-api03-\.\.\.") {
    Write-Warn "ANTHROPIC_API_KEY no configurada — el chat no funcionará hasta que la agregues"
}

# ── 3. frontend/.env.local ────────────────────────────────────────────────────
$frontendEnv = "$ROOT\frontend\.env.local"
if (-not (Test-Path $frontendEnv)) {
    "NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -FilePath $frontendEnv -Encoding utf8
    Write-OK "frontend/.env.local creado"
} else {
    Write-OK "frontend/.env.local existe"
}

# ── 4. Python venv ────────────────────────────────────────────────────────────
$venvPath = "$ROOT\backend\venv"
if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
    Write-Step "Creando entorno virtual Python..."
    & $pythonCmd -m venv $venvPath
    Write-OK "venv creado en backend/venv"
}

$pipExe     = "$venvPath\Scripts\pip.exe"
$pythonExe  = "$venvPath\Scripts\python.exe"

# ── 5. Dependencias Python ────────────────────────────────────────────────────
$fastapiInstalled = & $pipExe show fastapi 2>$null
if (-not $fastapiInstalled) {
    Write-Step "Instalando dependencias Python (puede tardar 1-2 min)..."
    & $pipExe install -r "$ROOT\backend\requirements.txt" --quiet
    Write-OK "Dependencias Python instaladas"
} else {
    Write-OK "Dependencias Python OK"
}

# ── 6. Dependencias Node ──────────────────────────────────────────────────────
if (-not (Test-Path "$ROOT\frontend\node_modules\next")) {
    Write-Step "Instalando dependencias Node (puede tardar 1-2 min)..."
    Push-Location "$ROOT\frontend"
    npm install --silent
    Pop-Location
    Write-OK "Dependencias Node instaladas"
} else {
    Write-OK "Dependencias Node OK"
}

# ── 7. Docker: postgres + redis + qdrant ─────────────────────────────────────
Write-Step "Levantando servicios Docker..."
Push-Location $ROOT

# Detecta docker compose v2 vs docker-compose v1
docker compose version 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    docker compose up -d 2>&1 | Out-Null
} else {
    docker-compose up -d 2>&1 | Out-Null
}
Pop-Location
Write-OK "Postgres + Redis + Qdrant en Docker"

# ── 8. Esperar PostgreSQL ─────────────────────────────────────────────────────
Write-Step "Esperando PostgreSQL..."
$maxTries = 20
$try = 0
do {
    $try++
    Start-Sleep -Seconds 2
    docker exec contadormx_postgres pg_isready -U contadormx 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { break }
    Write-Host "    ... intento $try/$maxTries" -ForegroundColor DarkGray
} while ($try -lt $maxTries)

if ($try -ge $maxTries) {
    Write-Warn "Postgres tardó más de lo esperado. Verifica que Docker Desktop esté corriendo."
} else {
    Write-OK "PostgreSQL listo"
}

# ── 9. Backend (nueva ventana) ────────────────────────────────────────────────
Write-Step "Iniciando backend FastAPI..."
$backendCmd = @"
title ContadorMX-Backend
cd /d "$ROOT\backend"
call venv\Scripts\activate
echo.
echo   Backend corriendo en http://localhost:8000
echo   API Docs en http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@
$backendScript = "$env:TEMP\cmx_backend.bat"
$backendCmd | Out-File -FilePath $backendScript -Encoding ascii
Start-Process "cmd.exe" -ArgumentList "/k", $backendScript

# ── 10. Frontend (nueva ventana) ──────────────────────────────────────────────
Write-Step "Iniciando frontend Next.js..."
$frontendCmd = @"
title ContadorMX-Frontend
cd /d "$ROOT\frontend"
echo.
echo   Frontend corriendo en http://localhost:3000
echo.
npm run dev
"@
$frontendScript = "$env:TEMP\cmx_frontend.bat"
$frontendCmd | Out-File -FilePath $frontendScript -Encoding ascii
Start-Process "cmd.exe" -ArgumentList "/k", $frontendScript

# ── Listo ─────────────────────────────────────────────────────────────────────
Start-Sleep -Seconds 4
Write-Host ""
Write-Host "  ┌─────────────────────────────────────┐" -ForegroundColor Green
Write-Host "  │  ContadorMX iniciado correctamente   │" -ForegroundColor Green
Write-Host "  ├─────────────────────────────────────┤" -ForegroundColor Green
Write-Host "  │  Frontend  →  http://localhost:3000  │" -ForegroundColor Cyan
Write-Host "  │  Backend   →  http://localhost:8000  │" -ForegroundColor Cyan
Write-Host "  │  API Docs  →  /docs                  │" -ForegroundColor Cyan
Write-Host "  │  Qdrant    →  http://localhost:6333  │" -ForegroundColor Cyan
Write-Host "  └─────────────────────────────────────┘" -ForegroundColor Green
Write-Host ""
Write-Host "  Para detener todo: .\stop.ps1" -ForegroundColor DarkGray
Write-Host ""
