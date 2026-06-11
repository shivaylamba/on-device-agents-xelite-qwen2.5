param(
  [int]$FoundryPort = 5272,
  [int]$SafeProxyPort = 5299,
  [int]$LiteLLMPort = 4001
)

$ErrorActionPreference = "Stop"

Write-Host "[Health] Foundry"
Invoke-RestMethod -Uri "http://127.0.0.1:$FoundryPort/v1/models" -TimeoutSec 10 | ConvertTo-Json -Depth 4

Write-Host "[Health] Safe NPU proxy"
Invoke-RestMethod -Uri "http://127.0.0.1:$SafeProxyPort/health" -TimeoutSec 10 | ConvertTo-Json -Depth 4

Write-Host "[Health] LiteLLM"
Invoke-RestMethod -Uri "http://127.0.0.1:$LiteLLMPort/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSec 10 | ConvertTo-Json -Depth 4
