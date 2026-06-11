$ErrorActionPreference = "Stop"

Write-Host "[Foundry] Current version:"
try {
  foundry --version
} catch {
  Write-Host "Foundry CLI is not currently available on PATH."
}

Write-Host "[Foundry] Checking winget for upgrades..."
winget upgrade --id Microsoft.FoundryLocal --accept-package-agreements --accept-source-agreements

Write-Host "[Foundry] Version after upgrade check:"
try {
  foundry --version
} catch {
  Write-Host "Foundry CLI is not currently available on PATH."
}

Write-Host "If winget reports no upgrade but GitHub shows a newer Foundry Local release, install the newer release from Microsoft guidance and rerun this script."
