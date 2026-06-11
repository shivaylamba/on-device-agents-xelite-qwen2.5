$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $demoRoot "config\openclaw-provider.jsonc"
$workspacePath = Join-Path $demoRoot "workspace-minimal"
$mcpPath = Join-Path $demoRoot "mcp"
$mcpServerPath = Join-Path $mcpPath "snapdragon-npu-tools.mjs"

if (-not (Test-Path $configPath)) {
  throw "OpenClaw provider config not found: $configPath"
}

Get-Content $configPath -Raw | openclaw config patch --stdin

if (Test-Path $mcpServerPath) {
  Push-Location $mcpPath
  try {
    if (-not (Test-Path (Join-Path $mcpPath "node_modules"))) {
      npm install
    }
  }
  finally {
    Pop-Location
  }

  openclaw mcp add snapdragon-npu `
    --command node `
    --arg "snapdragon-npu-tools.mjs" `
    --cwd $mcpPath `
    --include "get_current_time,get_npu_status,draft_stage_note" `
    --timeout 30 `
    --no-probe 2>$null | Out-Null

  if ($LASTEXITCODE -ne 0) {
    openclaw mcp configure snapdragon-npu `
      --include "get_current_time,get_npu_status,draft_stage_note" `
      --timeout 30 `
      --enable | Out-Null
  }
}

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
    allow: null,
    alsoAllow: ["bundle-mcp", "group:plugins", "snapdragon-npu__*"],
    codeMode: {
      enabled: false
    }
  }
}
"@ | openclaw config patch --stdin
}

openclaw config validate
