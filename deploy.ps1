# Wrapper for convenience — delegates to scripts/deploy.ps1
param(
  [switch]$DryRun,
  [switch]$Yes,
  [switch]$Help
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $ScriptDir "scripts\deploy.ps1") -DryRun:$DryRun -Yes:$Yes -Help:$Help
exit $LASTEXITCODE
