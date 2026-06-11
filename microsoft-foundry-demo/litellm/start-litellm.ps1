param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 4001,
  [string]$Config = "",
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvLiteLLM = Join-Path $repoRoot ".litellm-venv\Scripts\litellm.exe"
$venvPython = Join-Path $repoRoot ".litellm-venv\Scripts\python.exe"
$configPath = if ($Config) { $Config } else { Join-Path $repoRoot "config\litellm-foundry.yaml" }

if (-not (Test-Path $venvLiteLLM)) {
  Write-Host "[LiteLLM] Creating local virtual environment..."
  & $Python -m venv (Join-Path $repoRoot ".litellm-venv")
  if ($LASTEXITCODE -ne 0) {
    throw "Could not create .litellm-venv with Python command: $Python"
  }
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install "litellm[proxy]"
  if ($LASTEXITCODE -ne 0) {
    throw "LiteLLM install failed."
  }
}

if (-not (Test-Path $configPath)) {
  throw "LiteLLM config not found: $configPath"
}

Invoke-RestMethod -Uri "http://127.0.0.1:5299/v1/models" -TimeoutSec 10 | Out-Null

$logsDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

Write-Host "[LiteLLM] Endpoint: http://$HostName`:$Port"
Write-Host "[LiteLLM] Config:   $configPath"
Write-Host "[LiteLLM] Upstream: http://127.0.0.1:5299/v1"

& $venvLiteLLM --config $configPath --host $HostName --port $Port
