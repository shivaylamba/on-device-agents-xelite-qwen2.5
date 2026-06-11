param(
  [string]$SessionKey = "agent:main:npu-tool-demo",
  [int]$TimeoutSeconds = 240
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:5272/v1/models" -TimeoutSec 10 | Out-Null
$safeProxy = Invoke-RestMethod -Uri "http://127.0.0.1:5299/health" -TimeoutSec 10
Invoke-RestMethod -Uri "http://127.0.0.1:4001/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSec 10 | Out-Null

if ($safeProxy.strip_openai_tools) {
  throw "Safe NPU proxy is stripping tool schemas. Restart it with: .\safe-proxy\start-safe-proxy.ps1 -KeepOpenAITools"
}

openclaw agent --local `
  --agent main `
  --session-key $SessionKey `
  --model foundry-npu/foundry-npu `
  --message "First call the session_status tool. Then answer exactly: session_status tool was used." `
  --thinking off `
  --timeout $TimeoutSeconds `
  --json
