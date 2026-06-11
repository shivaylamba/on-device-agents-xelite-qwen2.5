param(
  [string]$BaseUrl = "http://127.0.0.1:4102/v1",
  [string]$Prompt = "In one sentence, what runtime is serving this model?"
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "$BaseUrl/models"

$body = @{
  model = "qwen3-4b-genie"
  messages = @(
    @{ role = "system"; content = "You are a concise local AI assistant." },
    @{ role = "user"; content = $Prompt }
  )
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "$BaseUrl/chat/completions" `
  -ContentType "application/json" `
  -Body $body

