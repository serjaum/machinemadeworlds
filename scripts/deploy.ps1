# Machine Made Worlds - Hostinger deploy via WinSCP / FTP (PowerShell)
# Syncs dist/ -> public_html. Board approval required before first live push.
# Env vars (same as deploy.sh):
#   HOSTINGER_FTP_HOST, HOSTINGER_FTP_USER, HOSTINGER_FTP_PASS
#   HOSTINGER_FTP_PORT (default 21), HOSTINGER_FTP_PROTOCOL (ftp|sftp|ftps), HOSTINGER_FTP_REMOTE_DIR (default public_html)
#   BOARD_APPROVED=1 to bypass approval gate (or pass -Yes)
# Usage:
#   $env:HOSTINGER_FTP_HOST="ftp.example.com"; $env:HOSTINGER_FTP_USER="u123"; $env:HOSTINGER_FTP_PASS="secret"; .\scripts\deploy.ps1 -DryRun
#   .\scripts\deploy.ps1 -Yes   # after Board approval
param(
  [switch]$DryRun,
  [switch]$Yes,
  [switch]$Help
)

if ($Help) {
  Write-Host "Usage: .\scripts\deploy.ps1 [-DryRun] [-Yes]"
  Write-Host "Env: HOSTINGER_FTP_HOST, HOSTINGER_FTP_USER, HOSTINGER_FTP_PASS [+ PORT/PROTOCOL/REMOTE_DIR]"
  exit 0
}

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$DistDir = Join-Path $RootDir "dist"
$RemoteDefault = "public_html"

if ($env:BOARD_APPROVED -eq "1") { $Yes = $true }

function Get-EnvWithFallback($primary, $fallback) {
  $v = [Environment]::GetEnvironmentVariable($primary)
  if ($v) { return $v }
  if ($fallback) {
    $v2 = [Environment]::GetEnvironmentVariable($fallback)
    if ($v2) { return $v2 }
  }
  return $null
}

$HostVal = Get-EnvWithFallback "HOSTINGER_FTP_HOST" "HOSTINGER_HOST"
$UserVal = Get-EnvWithFallback "HOSTINGER_FTP_USER" "HOSTINGER_USER"
$PassVal = Get-EnvWithFallback "HOSTINGER_FTP_PASS" "HOSTINGER_PASS"
$PortVal = Get-EnvWithFallback "HOSTINGER_FTP_PORT" "HOSTINGER_PORT"
$ProtoVal = [Environment]::GetEnvironmentVariable("HOSTINGER_FTP_PROTOCOL")
if (-not $ProtoVal) { $ProtoVal = "ftp" }
$RemoteVal = [Environment]::GetEnvironmentVariable("HOSTINGER_FTP_REMOTE_DIR")
if (-not $RemoteVal) { $RemoteVal = [Environment]::GetEnvironmentVariable("HOSTINGER_REMOTE_DIR") }
if (-not $RemoteVal) { $RemoteVal = $RemoteDefault }

if (-not $PortVal) {
  if ($ProtoVal -eq "sftp") { $PortVal = "22" } else { $PortVal = "21" }
}

# Validations
if (-not (Test-Path $DistDir)) {
  Write-Error "dist/ not found at $DistDir - build the site first"
  exit 1
}
foreach ($f in @("index.html","404.html","robots.txt","sitemap.xml","styles.css")) {
  if (-not (Test-Path (Join-Path $DistDir $f))) { Write-Warning "dist/$f missing - dist may be incomplete" }
}
if (-not (Test-Path (Join-Path $DistDir "about\index.html"))) { Write-Warning "dist/about/index.html missing" }
if (-not (Test-Path (Join-Path $DistDir "blog\index.html"))) { Write-Warning "dist/blog/index.html missing" }

if (-not $HostVal) { Write-Error "Set HOSTINGER_FTP_HOST (or legacy HOSTINGER_HOST)"; exit 1 }
if (-not $UserVal) { Write-Error "Set HOSTINGER_FTP_USER"; exit 1 }
if (-not $PassVal) { Write-Error "Set HOSTINGER_FTP_PASS"; exit 1 }

if (-not $Yes -and -not $DryRun) {
  Write-Host "Board approval required before first live push." -ForegroundColor Yellow
  Write-Host "After the Board approves in Paperclip, re-run with -Yes or set BOARD_APPROVED=1"
  Write-Host ""
  Write-Host "Example: `$env:BOARD_APPROVED='1'; .\scripts\deploy.ps1 -Yes"
  Write-Host "Dry-run (no approval needed): .\scripts\deploy.ps1 -DryRun"
  exit 3
}

$FileCount = (Get-ChildItem -Recurse -File $DistDir | Measure-Object).Count
Write-Host "=== Machine Made Worlds deploy ==="
Write-Host "Source : $DistDir\"
Write-Host "Target : $UserVal@$HostVal`:$RemoteVal (proto=$ProtoVal port=$PortVal)"
Write-Host "Files  : $FileCount files"

if ($DryRun) {
  Write-Host "[dry-run] Would mirror dist/ -> $RemoteVal via $ProtoVal" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "--- dist contents (top 50) ---"
  Get-ChildItem -Recurse -File $DistDir | Sort-Object FullName | Select-Object -First 50 | ForEach-Object {
    $_.FullName.Replace($RootDir + "\", "")
  }
  Write-Host ""
  $winscp = Get-Command "WinSCP.com" -ErrorAction SilentlyContinue
  if ($winscp) {
    Write-Host "[dry-run] WinSCP found - ready for real deploy"
  } else {
    Write-Host "WinSCP not found. Install WinSCP (https://winscp.net/eng/download.php) for one-command deploys." -ForegroundColor Yellow
    Write-Host "The PowerShell fallback uses System.Net.FtpWebRequest (slower, no delete sync)."
  }
  Write-Host ""
  Write-Host "[dry-run] Done - no files pushed." -ForegroundColor Green
  exit 0
}

# Real push
$WinScpPath = Get-Command "WinSCP.com" -ErrorAction SilentlyContinue
if ($WinScpPath) {
  Write-Host "Pushing with WinSCP synchronize remote -mirror -delete ..."
  $sessionUrl = "$ProtoVal`://$UserVal`:$PassVal@$HostVal`:$PortVal/"
  $openCmd = 'open ' + $sessionUrl + ' -hostkey="*"'
  $syncCmd = 'synchronize remote -mirror -delete -filemask="| _template/; _template/*" "' + $DistDir + '" "/' + $RemoteVal + '/"'
  & "WinSCP.com" /command "option batch abort" "option confirm off" $openCmd $syncCmd "exit"
  if ($LASTEXITCODE -ne 0) { Write-Error "WinSCP exited with code $LASTEXITCODE"; exit $LASTEXITCODE }
} else {
  Write-Host "WinSCP not found - using PowerShell FTP fallback (uploads only, no server-side delete)" -ForegroundColor Yellow
  Write-Host "For full mirror --delete, install WinSCP: https://winscp.net/eng/download.php"
  Add-Type -AssemblyName System.Net.Http
  $files = Get-ChildItem -Recurse -File $DistDir
  foreach ($file in $files) {
    $rel = $file.FullName.Substring($DistDir.Length).Replace("\","/").TrimStart("/")
    $uri = "$ProtoVal`://$HostVal`:$PortVal/$RemoteVal/$rel"
    if ($ProtoVal -eq "sftp") {
      Write-Warning "SFTP without WinSCP not supported in fallback. Install WinSCP or use WSL lftp."
      exit 2
    }
    Write-Host "  FTP PUT $rel"
    $req = [System.Net.FtpWebRequest]::Create($uri)
    $req.Credentials = New-Object System.Net.NetworkCredential($UserVal, $PassVal)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $req.UseBinary = $true
    $req.UsePassive = $true
    $dir = Split-Path $rel -Parent
    if ($dir) {
      $dirParts = $dir -split "/"
      $acc = ""
      foreach ($part in $dirParts) {
        if ($acc) { $acc = "$acc/$part" } else { $acc = $part }
        $mkUri = "$ProtoVal`://$HostVal`:$PortVal/$RemoteVal/$acc"
        try {
          $mk = [System.Net.FtpWebRequest]::Create($mkUri)
          $mk.Credentials = $req.Credentials
          $mk.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
          $mk.GetResponse().Close() | Out-Null
        } catch {}
      }
    }
    $content = [System.IO.File]::ReadAllBytes($file.FullName)
    $req.ContentLength = $content.Length
    $stream = $req.GetRequestStream()
    $stream.Write($content, 0, $content.Length)
    $stream.Close()
    $resp = $req.GetResponse()
    $resp.Close()
  }
}

Write-Host ""
Write-Host "Deploy finished. Verifying https://machinemadeworlds.com ..."
try {
  $res = Invoke-WebRequest -Uri "https://machinemadeworlds.com/" -UseBasicParsing -TimeoutSec 15
  Write-Host "HTTP $($res.StatusCode)" -ForegroundColor Green
} catch {
  Write-Warning "Verification failed: $_ - site may still be propagating"
}
try {
  $sm = Invoke-WebRequest -Uri "https://machinemadeworlds.com/sitemap.xml" -UseBasicParsing -TimeoutSec 15
  Write-Host "sitemap HTTP $($sm.StatusCode)" -ForegroundColor Green
} catch {
  Write-Warning "sitemap check failed: $_"
}
