
$ErrorActionPreference = "Stop"

$TaskName = "UrbanFlow Weekly Refresh"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Wrapper = Join-Path $ProjectRoot "scripts\refresh_urbanflow.ps1"
$Logs = Join-Path $ProjectRoot "logs"

if (-not (Test-Path $Wrapper)) {
    throw "Missing refresh wrapper: $Wrapper"
}

New-Item -ItemType Directory -Force -Path $Logs |
    Out-Null

# Preserve the previous task configuration, if any.
$Previous = Get-ScheduledTask `
    -TaskName $TaskName `
    -ErrorAction SilentlyContinue

if ($Previous) {
    $BackupFile = Join-Path $Logs "scheduled_task_backup.xml"
    Export-ScheduledTask -TaskName $TaskName |
        Set-Content -Path $BackupFile -Encoding UTF8

    Write-Host "Previous schedule backed up."
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$Wrapper`"" `
    -WorkingDirectory $ProjectRoot

# Every Monday at 09:00, local Windows time.
$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At (Get-Date).Date.AddHours(9)

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$CurrentUser = (
    [System.Security.Principal.WindowsIdentity]::GetCurrent()
).Name

$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Refresh UrbanFlow monthly history without modifying August research." `
    -Force | Out-Null

Write-Host ""
Write-Host "SCHEDULE REGISTERED"
Write-Host "Task: $TaskName"
Write-Host "When: Every Monday, 09:00"
Write-Host "Runs: $Wrapper"
Write-Host "Account: $CurrentUser"

Get-ScheduledTaskInfo -TaskName $TaskName |
    Select-Object LastRunTime, LastTaskResult, NextRunTime
