param(
  [Parameter(Mandatory=$true)][string]$ZipPath,
  [string]$Target = "."
)
if (!(Test-Path $ZipPath)) { Write-Error "Zip not found: $ZipPath"; exit 1 }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, (Resolve-Path $Target), $true)
Write-Host "Patched files extracted from $ZipPath to $Target (overwritten existing files)."
