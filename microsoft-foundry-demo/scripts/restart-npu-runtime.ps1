param(
  [int]$FoundryPort = 5272,
  [int]$SafeProxyPort = 5299,
  [int]$LiteLLMPort = 4001,
  [string]$Python = "C:\Program Files\Python312-arm64\python.exe",
  [string]$FoundryModel = "qwen2.5-7b",
  [switch]$KeepOpenAITools
)

$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot

foreach ($port in @($LiteLLMPort, $SafeProxyPort, $FoundryPort)) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
  }
}

Start-Sleep -Seconds 3

& (Join-Path $PSScriptRoot "start-demo-stack.ps1") `
  -FoundryPort $FoundryPort `
  -SafeProxyPort $SafeProxyPort `
  -LiteLLMPort $LiteLLMPort `
  -Python $Python `
  -FoundryModel $FoundryModel `
  -KeepOpenAITools:$KeepOpenAITools
