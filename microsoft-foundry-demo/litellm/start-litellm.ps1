param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 4001,
  [string]$Config = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvLiteLLM = Join-Path $repoRoot ".litellm-venv\Scripts\litellm.exe"
$configPath = if ($Config) { $Config } else { Join-Path $repoRoot "config\litellm-foundry.yaml" }

if (-not (Test-Path $venvLiteLLM)) {
  throw "LiteLLM is not installed. Run: py -3.11 -m venv .litellm-venv; .\.litellm-venv\Scripts\python.exe -m pip install 'litellm[proxy]'"
}

if (-not (Test-Path $configPath)) {
  throw "LiteLLM config not found: $configPath"
}

Invoke-RestMethod -Uri "http://127.0.0.1:5272/v1/models" -TimeoutSec 10 | Out-Null

$logsDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

Write-Host "[LiteLLM] Endpoint: http://$HostName`:$Port"
Write-Host "[LiteLLM] Config:   $configPath"
Write-Host "[LiteLLM] Upstream: http://127.0.0.1:5272/v1"

& $venvLiteLLM --config $configPath --host $HostName --port $Port
