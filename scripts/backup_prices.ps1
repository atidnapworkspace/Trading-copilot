# Weekly local backup of old prices (run by a Windows scheduled task). Log: historico\backup-log.txt
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = Join-Path $root 'pipeline\src'
& (Join-Path $root '.venv\Scripts\python.exe') -m tcp.jobs.backup_prices
exit $LASTEXITCODE
