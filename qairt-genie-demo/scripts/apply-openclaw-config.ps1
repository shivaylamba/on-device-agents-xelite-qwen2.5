$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $demoRoot "openclaw\qwen3-genie-openclaw-provider.jsonc"

if (-not (Test-Path $configPath)) {
  throw "OpenClaw Qwen3 Genie provider config not found: $configPath"
}

Get-Content $configPath -Raw | openclaw config patch --stdin
openclaw config validate

