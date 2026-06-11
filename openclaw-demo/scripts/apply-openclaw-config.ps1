$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $demoRoot "config\openclaw-provider.jsonc"
$workspacePath = Join-Path $demoRoot "workspace-minimal"

if (-not (Test-Path $configPath)) {
  throw "OpenClaw provider config not found: $configPath"
}

Get-Content $configPath -Raw | openclaw config patch --stdin

if (Test-Path $workspacePath) {
  $workspaceJsonPath = ($workspacePath -replace '\\', '\\')
  @"
{
  agents: {
    defaults: {
      workspace: "$workspaceJsonPath",
      maxConcurrent: 1,
      subagents: {
        maxConcurrent: 1
      }
    }
  },
  tools: {
    profile: "minimal",
    codeMode: {
      enabled: false
    }
  }
}
"@ | openclaw config patch --stdin
}

openclaw config validate
