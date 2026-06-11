param(
  [string]$Prompt = "Reply exactly: OpenClaw is using Foundry Local on Snapdragon NPU."
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:5272/v1/models" -TimeoutSec 10 | Out-Null
Invoke-RestMethod -Uri "http://127.0.0.1:5299/health" -TimeoutSec 10 | Out-Null
Invoke-RestMethod -Uri "http://127.0.0.1:4001/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSec 10 | Out-Null

openclaw infer model run --local --model foundry-npu/foundry-npu --prompt $Prompt --json
