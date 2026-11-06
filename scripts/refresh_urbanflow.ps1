
param(
    [string]$Period = ""
)

$ErrorActionPreference = "Stop"

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\refresh_monthly_history.py"

if (-not (Test-Path $Python)) {
    throw "Python environment not found: $Python"
}

if (-not (Test-Path $Script)) {
    throw "Refresh script not found: $Script"
}

$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir |
    Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "refresh_$Timestamp.log"

$Arguments = @(
    "-u",
    $Script,
    "--cleanup-raw"
)

if ($Period -ne "") {
    $Arguments += @("--period", $Period)
}

Write-Host "URBANFLOW SCHEDULED HISTORY REFRESH"
Write-Host "Project: $ProjectRoot"
Write-Host "Log: $LogFile"

$OldPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

& $Python @Arguments 2>&1 |
    Tee-Object -FilePath $LogFile

$ExitCode = $LASTEXITCODE
$ErrorActionPreference = $OldPreference

if ($ExitCode -ne 0) {
    Write-Host "REFRESH FAILED. Check: $LogFile"
    exit $ExitCode
}

Write-Host "REFRESH COMPLETED. Log: $LogFile"
exit 0
