param(
  [Parameter(Mandatory=$true)][string]$SourceDir,
  [Parameter(Mandatory=$true)][string]$OutZip = "patch.zip",
  [string[]]$Include = @()
)
$src = Resolve-Path $SourceDir
if (!(Test-Path $src)) { Write-Error "Source not found"; exit 1 }
$tmp = Join-Path $env:TEMP ("patch_" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null

# If -Include provided, copy only those files; else copy all
if ($Include.Count -gt 0) {
  foreach ($p in $Include) {
    $full = Join-Path $src $p
    if (Test-Path $full) {
      $dest = Join-Path $tmp $p
      New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($dest)) -Force | Out-Null
      Copy-Item $full $dest -Force
    }
  }
} else {
  Copy-Item "$src\*" $tmp -Recurse -Force
}

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tmp, (Resolve-Path $OutZip))
Write-Host "Created patch zip: $OutZip"
Remove-Item $tmp -Recurse -Force
