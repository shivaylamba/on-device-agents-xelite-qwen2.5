# Foundry Local NPU Bridge launcher

$Python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
$AppPy = Join-Path $PSScriptRoot 'app.py'
$LogDir = if ($env:FOUNDRY_LOG_DIR) { $env:FOUNDRY_LOG_DIR } else { Join-Path $PSScriptRoot 'logs' }
$PassArgs = $args -join ' '

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$LogFile = Join-Path $LogDir ('foundry-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')

function Log($msg) {
    $line = '[' + (Get-Date -Format 'HH:mm:ss') + '] ' + $msg
    Write-Host $line -ForegroundColor Cyan
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}

# Refresh PATH so winget-installed Foundry is visible in this shell.
$env:PATH = [System.Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH','User')

$pythonCheck = & $Python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "Python was not found. Set `$env:PYTHON to a valid python.exe path or add Python to PATH."
    exit 1
}
Log "Python OK: $pythonCheck"

$foundryCmd = Get-Command foundry -ErrorAction SilentlyContinue
if (-not $foundryCmd) {
    Log "Foundry CLI was not found. Install Microsoft Foundry Local first, then rerun this script."
    Log "Install hint: winget install Microsoft.FoundryLocal"
    exit 1
}
Log "Foundry CLI OK: $($foundryCmd.Source)"

$sdkCheck = & $Python -c "import foundry_local_sdk; print('OK')" 2>&1
if ($sdkCheck -notmatch 'OK') {
    Log 'SDK is missing - installing foundry-local-sdk-winml and openai...'
    & $Python -m pip install foundry-local-sdk-winml openai --quiet
    if ($LASTEXITCODE -ne 0) {
        Log 'SDK install failed.'
        exit 1
    }
    Log 'SDK installed.'
} else {
    Log 'SDK OK.'
}

$svcStatus = (foundry service status 2>&1) -join ' '
if ($svcStatus -match 'Started|running|Model management service is running') {
    Log 'Stopping standalone foundry service so the SDK web service can own the port...'
    foundry service stop | Out-Null
    Start-Sleep -Seconds 2
} else {
    Log 'Standalone foundry service is not running.'
}

Log "Starting app.py (args: $PassArgs)..."

if (-not $env:FOUNDRY_MODEL) {
    $env:FOUNDRY_MODEL = 'qwen2.5-7b'
}
$env:FOUNDRY_PORT = if ($env:FOUNDRY_PORT) { $env:FOUNDRY_PORT } else { '5272' }

& $Python $AppPy $args
