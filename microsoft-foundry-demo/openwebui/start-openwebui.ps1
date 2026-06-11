param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8080,
  [string]$OpenAIBaseUrl = "http://127.0.0.1:4001/v1",
  [string]$ApiKey = "sk-win-vivo2",
  [string]$Model = "foundry-npu"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvOpenWebUi = Join-Path $repoRoot ".openwebui-venv\Scripts\open-webui.exe"

if (-not (Test-Path $venvOpenWebUi)) {
  throw "Open WebUI is not installed. Run: py -3.11 -m venv .openwebui-venv; .\.openwebui-venv\Scripts\python.exe -m pip install open-webui"
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

Write-Host "[Open WebUI] Endpoint: http://$HostName`:$Port"
Write-Host "[Open WebUI] OpenAI:   $OpenAIBaseUrl"
Write-Host "[Open WebUI] Model:    $Model"

& $venvOpenWebUi serve --host $HostName --port $Port
