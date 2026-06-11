param(
  [Parameter(Mandatory = $true)]
  [string]$Model,
  [ValidateSet("htp", "cpu")]
  [string]$Backend = "htp",
  [string]$Inputs = "",
  [switch]$NoCpuFallback,
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$demoRoot = Split-Path -Parent $PSScriptRoot

$argsList = @(
  (Join-Path $demoRoot "runtime\qnn_ort_runner.py"),
  "--model", $Model,
  "--backend", $Backend
)

if ($Inputs) {
  $argsList += @("--inputs", $Inputs)
}

if ($NoCpuFallback) {
  $argsList += "--no-cpu-fallback"
}

& $Python @argsList
