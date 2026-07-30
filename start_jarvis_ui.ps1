param(
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$existing = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Error "JARVIS UI is already listening at http://127.0.0.1:$Port"
    exit 1
}

$python = $env:JARVIS_PYTHON
if (-not $python) {
    $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    $python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
}

$arguments = @("main.py", "--ui", "--port", "$Port")
if ($NoBrowser) { $arguments += "--no-browser" }

Write-Host "Starting JARVIS at http://127.0.0.1:$Port"
& $python @arguments
exit $LASTEXITCODE
