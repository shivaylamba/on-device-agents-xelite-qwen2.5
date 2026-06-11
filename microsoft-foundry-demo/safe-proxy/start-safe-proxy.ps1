param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 5299,
  [string]$Upstream = "http://127.0.0.1:5272/v1",
  [string]$Python = "python",
  [int]$MaxTokens = 128,
  [int]$MaxMessages = 8,
  [int]$MaxMessageChars = 12000,
  [switch]$KeepOpenAITools
)

$ErrorActionPreference = "Stop"

$env:SAFE_PROXY_MAX_TOKENS = "$MaxTokens"
$env:SAFE_PROXY_MAX_MESSAGES = "$MaxMessages"
$env:SAFE_PROXY_MAX_MESSAGE_CHARS = "$MaxMessageChars"
$env:SAFE_PROXY_STRIP_OPENAI_TOOLS = if ($KeepOpenAITools) { "false" } else { "true" }

$scriptPath = Join-Path $PSScriptRoot "safe_npu_proxy.py"

Write-Host "[Safe NPU Proxy] Endpoint: http://$HostName`:$Port/v1"
Write-Host "[Safe NPU Proxy] Upstream:  $Upstream"
Write-Host "[Safe NPU Proxy] Max tokens: $MaxTokens"

& $Python $scriptPath --host $HostName --port $Port --upstream $Upstream
