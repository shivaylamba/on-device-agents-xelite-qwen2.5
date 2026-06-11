param(
  [string]$BundlePath = "C:\Users\Admin\Documents\executorch-voice-agent\models\qwen3_4b\genie_bundle\qwen3_4b-genie-w4a16-qualcomm_snapdragon_x_elite",
  [string]$QairtRoot = "C:\Qualcomm\AIStack\QAIRT\2.45.0.260326",
  [ValidateSet("aarch64-windows-msvc", "arm64x-windows-msvc", "x86_64-windows-msvc")]
  [string]$Arch = "aarch64-windows-msvc",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 4102
)

$ErrorActionPreference = "Stop"

$demoRoot = Split-Path -Parent $PSScriptRoot
$server = Join-Path $demoRoot "runtime\qwen3_genie_openai_server.py"

if (-not (Test-Path $server)) { throw "Server file not found: $server" }

python $server `
  --host $HostName `
  --port $Port `
  --bundle $BundlePath `
  --qairt-root $QairtRoot `
  --arch $Arch

