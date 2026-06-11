param(
  [ValidateSet("htp", "cpu")]
  [string]$Backend = "htp",
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$demoRoot = Split-Path -Parent $PSScriptRoot

$modelPath = & $Python (Join-Path $demoRoot "runtime\make_toy_add_model.py")
Write-Host "Generated toy model: $modelPath"

& $Python (Join-Path $demoRoot "runtime\qnn_ort_runner.py") `
  --model $modelPath `
  --backend $Backend
