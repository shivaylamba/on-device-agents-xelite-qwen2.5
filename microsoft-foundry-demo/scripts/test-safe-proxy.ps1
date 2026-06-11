param(
  [int]$SafeProxyPort = 5299
)

$ErrorActionPreference = "Stop"

$payload = @{
  model = "qwen2.5-7b-instruct-qnn-npu"
  max_tokens = 32
  temperature = 0
  messages = @(
    @{
      role = "user"
      content = "Reply exactly: safe proxy works"
    }
  )
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Uri "http://127.0.0.1:$SafeProxyPort/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json" `
  -Body $payload `
  -TimeoutSec 90 |
  ConvertTo-Json -Depth 6
