param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$demoRoot = Split-Path -Parent $PSScriptRoot

& $Python (Join-Path $demoRoot "runtime\qnn_ep_probe.py")
