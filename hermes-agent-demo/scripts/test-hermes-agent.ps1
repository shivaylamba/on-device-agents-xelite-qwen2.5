param(
  [string]$Prompt = "Reply in one short sentence: Hermes is routed through LiteLLM to Foundry Local on Snapdragon NPU."
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:5272/v1/models" -TimeoutSec 10 | Out-Null
Invoke-RestMethod -Uri "http://127.0.0.1:4001/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSec 10 | Out-Null

hermes -z $Prompt --ignore-rules
