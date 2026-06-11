param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 4101,
  [string]$Model = "",
  [ValidateSet("htp", "cpu")]
  [string]$Backend = "htp",
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$demoRoot = Split-Path -Parent $PSScriptRoot

$owners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($owner in $owners) {
  Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
}

$server = Join-Path $demoRoot "runtime\qairt_openai_server.py"
$argumentText = "`"$server`" --host $HostName --port $Port --backend $Backend"
if ($Model) {
  $argumentText += " --model `"$Model`""
}

Start-Process -FilePath $Python -ArgumentList $argumentText -WorkingDirectory $demoRoot -WindowStyle Hidden
Start-Sleep -Seconds 2

Invoke-RestMethod -Uri "http://$HostName`:$Port/health" -TimeoutSec 10 | ConvertTo-Json -Depth 6
