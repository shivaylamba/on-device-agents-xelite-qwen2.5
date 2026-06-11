param(
  [string]$BundlePath = "C:\Users\Admin\Documents\executorch-voice-agent\models\qwen3_4b\genie_bundle\qwen3_4b-genie-w4a16-qualcomm_snapdragon_x_elite",
  [string]$QairtRoot = "C:\Qualcomm\AIStack\QAIRT\2.45.0.260326",
  [ValidateSet("aarch64-windows-msvc", "arm64x-windows-msvc", "x86_64-windows-msvc")]
  [string]$Arch = "aarch64-windows-msvc",
  [string]$Prompt = "What is 2+2? Reply with the number only.",
  [ValidateSet("error", "warn", "info", "verbose", "none")]
  [string]$LogLevel = "none"
)

$ErrorActionPreference = "Stop"

$exe = Join-Path $QairtRoot "bin\$Arch\genie-t2t-run.exe"
$lib = Join-Path $QairtRoot "lib\$Arch"
$bin = Join-Path $QairtRoot "bin\$Arch"
$skel = Join-Path $QairtRoot "lib\hexagon-v73\unsigned"
$config = Join-Path $BundlePath "genie_config.json"

if (-not (Test-Path $exe)) { throw "genie-t2t-run.exe not found: $exe" }
if (-not (Test-Path $lib)) { throw "QAIRT lib path not found: $lib" }
if (-not (Test-Path $skel)) { throw "HTP Skel path not found: $skel" }
if (-not (Test-Path $config)) { throw "Genie config not found: $config" }

$env:QAIRT_SDK_ROOT = $QairtRoot
$env:QAIRT_HOME = $QairtRoot
$env:QNN_SDK_ROOT = $QairtRoot
$env:ADSP_LIBRARY_PATH = "$skel;"
$env:PATH = "$bin;$lib;$env:PATH"

$chatPrompt = @"
<|im_start|>system
You are a helpful AI assistant.<|im_end|>
<|im_start|>user
$Prompt<|im_end|>
<|im_start|>assistant
"@

Push-Location $BundlePath
try {
  if ($LogLevel -eq "none") {
    & $exe -c genie_config.json -p $chatPrompt
  } else {
    & $exe -c genie_config.json -p $chatPrompt --log $LogLevel
  }
  if ($LASTEXITCODE -ne 0) {
    throw "genie-t2t-run exited with $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

