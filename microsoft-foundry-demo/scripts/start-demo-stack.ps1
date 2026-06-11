param(
  [string]$HostName = "127.0.0.1",
  [int]$FoundryPort = 5272,
  [int]$SafeProxyPort = 5299,
  [int]$LiteLLMPort = 4001,
  [int]$OpenWebUIPort = 8080,
  [string]$Python = "C:\Program Files\Python312-arm64\python.exe",
  [string]$FoundryModel = "qwen2.5-7b",
  [int]$MaxTokens = 128
)

$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot

function Wait-HttpOk {
  param(
    [string]$Url,
    [hashtable]$Headers = @{},
    [int]$TimeoutSeconds = 180
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      Invoke-RestMethod -Uri $Url -Headers $Headers -TimeoutSec 8 | Out-Null
      return
    } catch {
      Start-Sleep -Seconds 3
    }
  } while ((Get-Date) -lt $deadline)

  throw "Timed out waiting for $Url"
}

$foundryCommand = @"
`$env:PYTHON = '$Python'
`$env:FOUNDRY_MODEL = '$FoundryModel'
`$env:FOUNDRY_PORT = '$FoundryPort'
Set-Location '$demoRoot'
.\foundry\start-foundry.ps1
"@

Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $demoRoot -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-Command",
  $foundryCommand
)

Wait-HttpOk -Url "http://$HostName`:$FoundryPort/v1/models" -TimeoutSeconds 240

$safeProxyCommand = @"
Set-Location '$demoRoot'
.\safe-proxy\start-safe-proxy.ps1 -HostName '$HostName' -Port $SafeProxyPort -Upstream 'http://$HostName`:$FoundryPort/v1' -Python '$Python' -MaxTokens $MaxTokens
"@

Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $demoRoot -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-Command",
  $safeProxyCommand
)

Wait-HttpOk -Url "http://$HostName`:$SafeProxyPort/health" -TimeoutSeconds 60

$litellmCommand = @"
Set-Location '$demoRoot'
.\litellm\start-litellm.ps1 -HostName '$HostName' -Port $LiteLLMPort -Python '$Python'
"@

Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $demoRoot -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-Command",
  $litellmCommand
)

Wait-HttpOk -Url "http://$HostName`:$LiteLLMPort/v1/models" -Headers @{ Authorization = "Bearer sk-win-vivo2" } -TimeoutSeconds 120

$openWebUICommand = @"
Set-Location '$demoRoot'
.\openwebui\start-openwebui.ps1 -HostName '$HostName' -Port $OpenWebUIPort -Python '$Python'
"@

Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $demoRoot -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-Command",
  $openWebUICommand
)

Write-Host "Foundry Local: http://$HostName`:$FoundryPort/v1"
Write-Host "Safe Proxy:    http://$HostName`:$SafeProxyPort/v1"
Write-Host "LiteLLM:       http://$HostName`:$LiteLLMPort/v1"
Write-Host "Open WebUI:    http://$HostName`:$OpenWebUIPort"
