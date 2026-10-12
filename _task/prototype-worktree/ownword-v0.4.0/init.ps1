param([switch]$Serve, [switch]$Plan)
$ErrorActionPreference = 'Stop'
if ($Serve -and $Plan) { throw 'Serve 与 Plan 不能同时使用' }
$mode = if ($Plan) { '--plan' } elseif ($Serve) { '--serve' } else { '--check' }
& node (Join-Path $PSScriptRoot 'bootstrap.mjs') $mode
exit $LASTEXITCODE
