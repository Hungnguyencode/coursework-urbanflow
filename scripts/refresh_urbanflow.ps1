param(
    [string]$Period = ""
)

$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [Console]::OutputEncoding

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$LogDirectory = Join-Path $ProjectRoot "logs"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $LogDirectory `
    | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$LogFile = Join-Path `
    $LogDirectory `
    "refresh_$Timestamp.log"

Write-Host ""
Write-Host "============================================================"
Write-Host "URBANFLOW SCHEDULED REFRESH"
Write-Host "============================================================"
Write-Host "Project : $ProjectRoot"
Write-Host "Log     : $LogFile"

$PipelineArguments = @(
    "run",
    "python",
    "scripts\update_pipeline.py",
    "--cleanup-raw"
)

if ($Period -ne "") {
    $PipelineArguments += @(
        "--period",
        $Period
    )

    Write-Host "Period  : $Period"
}
else {
    Write-Host "Period  : automatic"
}

Write-Host ""

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

& uv @PipelineArguments 2>&1 |
    Tee-Object -FilePath $LogFile

$ExitCode = $LASTEXITCODE

$ErrorActionPreference = $PreviousErrorActionPreference

if ($ExitCode -ne 0) {
    Write-Host ""
    Write-Host "URBANFLOW REFRESH FAILED"
    Write-Host "See log: $LogFile"

    exit $ExitCode
}

Write-Host ""
Write-Host "============================================================"
Write-Host "URBANFLOW SCHEDULED REFRESH COMPLETE"
Write-Host "============================================================"
Write-Host "Log: $LogFile"

exit 0