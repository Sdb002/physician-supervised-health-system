<#
.SYNOPSIS
    Starts the FastAPI backend and the Next.js dashboard together.

.DESCRIPTION
    The dashboard is useless without the API - every page shows
    "Cannot reach the API" until uvicorn is up. This script starts the
    backend (in its own window, so you can watch its logs and Ctrl+C it),
    waits until it actually answers /health, then runs the dashboard dev
    server in the foreground.

    If something is already listening on the API port, the existing backend
    is reused instead of starting a second one.

    Keep this file ASCII-only: Windows PowerShell 5.1 reads a BOM-less
    script as CP1252, and characters such as an em dash decode into bytes
    that it treats as string delimiters.

.EXAMPLE
    .\scripts\dev.ps1
    .\scripts\dev.ps1 -ApiPort 8001
    .\scripts\dev.ps1 -ApiOnly
#>
[CmdletBinding()]
param(
    [int]$ApiPort = 8000,
    [string]$ApiHost = "127.0.0.1",
    # Skip uvicorn's auto-reload (slightly faster, but code edits need a restart).
    [switch]$NoReload,
    # Start only the backend and leave it in the foreground.
    [switch]$ApiOnly
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$apiUrl = "http://${ApiHost}:${ApiPort}"

if (-not (Test-Path $python)) {
    throw "No virtualenv at $python - see the Quickstart in README.md."
}

function Test-ApiUp {
    try {
        Invoke-WebRequest -Uri "$apiUrl/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

$uvicornArgs = @("-m", "uvicorn", "src.api.main:app", "--host", $ApiHost, "--port", "$ApiPort")
if (-not $NoReload) { $uvicornArgs += "--reload" }

if ($ApiOnly) {
    Write-Host "Starting API on $apiUrl (Ctrl+C to stop)..." -ForegroundColor Cyan
    & $python @uvicornArgs
    return
}

if (Test-ApiUp) {
    Write-Host "API already running on $apiUrl - reusing it." -ForegroundColor Yellow
} else {
    Write-Host "Starting API on $apiUrl ..." -ForegroundColor Cyan
    # A separate window keeps uvicorn's logs visible and keeps it alive
    # independently of this shell.
    Start-Process -FilePath $python -ArgumentList $uvicornArgs -WorkingDirectory $root | Out-Null

    $deadline = (Get-Date).AddSeconds(45)
    while (-not (Test-ApiUp)) {
        if ((Get-Date) -gt $deadline) {
            throw "API did not come up on $apiUrl within 45s - check the uvicorn window for errors."
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "API is up on $apiUrl" -ForegroundColor Green
}

Write-Host "Starting dashboard on http://localhost:3000 (Ctrl+C to stop)..." -ForegroundColor Cyan
Push-Location (Join-Path $root "dashboard")
try {
    npm run dev
} finally {
    Pop-Location
}
