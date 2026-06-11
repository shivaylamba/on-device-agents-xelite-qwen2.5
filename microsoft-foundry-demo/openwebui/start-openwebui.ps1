param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8080,
  [string]$OpenAIBaseUrl = "http://127.0.0.1:4001/v1",
  [string]$ApiKey = "sk-win-vivo2",
  [string]$Model = "foundry-npu",
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvOpenWebUi = Join-Path $repoRoot ".openwebui-venv\Scripts\open-webui.exe"
$venvPython = Join-Path $repoRoot ".openwebui-venv\Scripts\python.exe"

if (-not (Test-Path $venvOpenWebUi)) {
  Write-Host "[Open WebUI] Creating local virtual environment..."
  & $Python -m venv (Join-Path $repoRoot ".openwebui-venv")
  if ($LASTEXITCODE -ne 0) {
    throw "Could not create .openwebui-venv with Python command: $Python"
  }
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install open-webui
  if ($LASTEXITCODE -ne 0) {
    throw "Open WebUI install failed."
  }
}

try {
  Invoke-RestMethod -Uri "$OpenAIBaseUrl/models" -Headers @{ Authorization = "Bearer $ApiKey" } -TimeoutSec 8 | Out-Null
} catch {
  throw "OpenAI-compatible endpoint is not reachable at $OpenAIBaseUrl. Start Foundry Local and LiteLLM first."
}

$dataDir = Join-Path $PSScriptRoot "data"
$logsDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $dataDir, $logsDir | Out-Null

$env:DATA_DIR = $dataDir
$env:WEBUI_AUTH = "False"
$env:WEBUI_NAME = "Snapdragon NPU Agent"
$env:ENABLE_OPENAI_API = "True"
$env:ENABLE_OLLAMA_API = "False"
$env:OPENAI_API_BASE_URLS = $OpenAIBaseUrl
$env:OPENAI_API_KEYS = $ApiKey
$env:DEFAULT_MODELS = $Model
$env:SAFE_NPU_BASE_URL = "http://127.0.0.1:5299/v1"

Write-Host "[Open WebUI] Endpoint: http://$HostName`:$Port"
Write-Host "[Open WebUI] OpenAI:   $OpenAIBaseUrl"
Write-Host "[Open WebUI] Model:    $Model"

& $venvOpenWebUi serve --host $HostName --port $Port
