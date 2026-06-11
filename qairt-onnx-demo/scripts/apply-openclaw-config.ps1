$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $demoRoot "openclaw\qairt-openclaw-provider.jsonc"

if (-not (Test-Path $configPath)) {
  throw "OpenClaw QAIRT provider config not found: $configPath"
}

Get-Content $configPath -Raw | openclaw config patch --stdin
openclaw config validate
