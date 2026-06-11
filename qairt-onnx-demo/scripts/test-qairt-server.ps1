param(
  [int]$Port = 4101
)

$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 10 | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/models" -TimeoutSec 10 | ConvertTo-Json -Depth 6
