$root       = Resolve-Path (Join-Path $PSScriptRoot "..")
$venv       = Join-Path $root ".venv"
$act        = Join-Path $venv "Scripts\Activate.ps1"
$script     = Join-Path $root "rtsp-stream\rtsp_cam.py"
$mediamtxExe = Join-Path $root "rtsp-stream\mediamtx.exe"

function Install-Tool {
  param(
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$WingetId
  )
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    Write-Host "Installing $Name ..."
    winget install -e --id $WingetId --silent | Out-Null
  }
}

function Get-FFmpegPath {
  $cmd = (Get-Command ffmpeg -ErrorAction SilentlyContinue)
  if ($cmd) { return $cmd.Source }

  $candidates = @(
    "$env:ProgramFiles\ffmpeg\bin\ffmpeg.exe",
    "$env:ProgramFiles\FFmpeg\bin\ffmpeg.exe"
  )

  $pkgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  if (Test-Path $pkgRoot) {
    $found = Get-ChildItem -Path $pkgRoot -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $candidates += $found.FullName }
  }

  foreach ($p in $candidates) {
    if (Test-Path $p) { return $p }
  }
  return $null
}

# 1) Tools
Install-Tool -Name python -WingetId 'Python.Python.3.11'
Install-Tool -Name ffmpeg -WingetId 'Gyan.FFmpeg'

# 2) venv + deps
if (-not (Test-Path $act)) {
  Write-Host "Creating virtual env..."
  python -m venv $venv
}
. $act
python -m pip install --upgrade pip
pip install opencv-python numpy | Out-Null

# 3) Optional firewall (skip if not admin)
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
            ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($IsAdmin) {
  if (-not (Get-NetFirewallRule -DisplayName 'ENSC424-RTSP-8554' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName 'ENSC424-RTSP-8554' -Direction Inbound -Protocol TCP -LocalPort 8554 -Action Allow | Out-Null
  }
} else {
  Write-Host "Note: not admin, skipping firewall rule. If others can't connect, allow TCP 8554 in Windows Firewall."
}

# 4) RTSP env defaults (mostly for future use)
if ([string]::IsNullOrWhiteSpace($env:RTSP_PORT))   { $env:RTSP_PORT   = '8554' }
if ([string]::IsNullOrWhiteSpace($env:RTSP_STREAM)) { $env:RTSP_STREAM = 'cam' }
if ([string]::IsNullOrWhiteSpace($env:RTSP_URL)) {
  $env:RTSP_URL = "rtsp://127.0.0.1:$($env:RTSP_PORT)/$($env:RTSP_STREAM)"
}

# 5) Resolve ffmpeg and expose to Python
$ff = Get-FFmpegPath
if ($ff) {
  $env:FFMPEG_EXE = $ff
} else {
  Write-Host "FFmpeg installed but not on PATH yet. Close and reopen the terminal, or restart Windows, then run again."
  exit 1
}

# 6) Start MediaMTX RTSP server (separate window)
$mediamtxProc = $null
if (Test-Path $mediamtxExe) {
  Write-Host "Starting MediaMTX RTSP server..."
  $mediamtxProc = Start-Process -FilePath $mediamtxExe `
                                -WorkingDirectory (Split-Path $mediamtxExe) `
                                -WindowStyle Normal `
                                -PassThru
  Start-Sleep -Seconds 1
} else {
  Write-Host "WARNING: mediamtx.exe not found at $mediamtxExe. RTSP server will NOT be started automatically."
}


# 8) Run Python streamer; when it exits, stop MediaMTX
try {
  python $script
}
finally {
  if ($mediamtxProc -and -not $mediamtxProc.HasExited) {
    Write-Host "Stopping MediaMTX RTSP server..."
    $mediamtxProc.Kill()
  }
}