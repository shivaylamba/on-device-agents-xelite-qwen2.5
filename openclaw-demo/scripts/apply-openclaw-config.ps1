$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $demoRoot "config\openclaw-provider.jsonc"

if (-not (Test-Path $configPath)) {
  throw "OpenClaw provider config not found: $configPath"
}

Get-Content $configPath -Raw | openclaw config patch --stdin
openclaw config validate
