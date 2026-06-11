param(
  [string]$Prompt = "Reply in one short sentence: what runtime stack are you using?",
  [string]$SessionKey = "agent:main:npu-smoke",
  [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:5272/v1/models" -TimeoutSec 10 | Out-Null
Invoke-RestMethod -Uri "http://127.0.0.1:5299/health" -TimeoutSec 10 | Out-Null
Invoke-RestMethod -Uri "http://127.0.0.1:4001/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSec 10 | Out-Null

openclaw agent --local `
  --agent main `
  --session-key $SessionKey `
  --model foundry-npu/foundry-npu `
  --message $Prompt `
  --thinking off `
  --timeout $TimeoutSeconds `
  --json
