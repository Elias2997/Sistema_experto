$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"
$pythonExe = Join-Path $projectRoot ".venv\\Scripts\\python.exe"
$backendUrl = "http://localhost:3000/diagnostico"

if (-not (Test-Path -LiteralPath $backendPath)) {
    throw "No se encontro la carpeta backend en: $backendPath"
}

if (-not (Test-Path -LiteralPath $frontendPath)) {
    throw "No se encontro la carpeta frontend en: $frontendPath"
}

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "No se encontro el interprete de Python en: $pythonExe"
}

$backendCommand = @"
Set-Location -LiteralPath '$backendPath'
node server.js
"@

$frontendCommand = @"
Set-Location -LiteralPath '$projectRoot'
`$env:BACKEND_URL = '$backendUrl'
& '$pythonExe' 'frontend/app.py'
"@

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
Start-Sleep -Seconds 2
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host "Backend y frontend iniciados." -ForegroundColor Green
Write-Host "Backend: $backendUrl" -ForegroundColor Cyan
