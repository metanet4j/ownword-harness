param([switch]$Serve)
$ErrorActionPreference = 'Stop'
$mode = if ($Serve) { '--serve' } else { '--check' }
& node (Join-Path $PSScriptRoot 'bootstrap.mjs') $mode
exit $LASTEXITCODE
