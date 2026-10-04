# setup_task.ps1 - Registers Windows Scheduled Task for 6-hour scraper runs
$TaskName = "FragranceFinder_Scraper_6Hour"
$PythonPath = (Get-Command python.exe).Source
$ScriptPath = "$PSScriptRoot\backend\scripts\run_scheduled_scrapers.py"
$WorkingDir = "$PSScriptRoot"

Write-Host "Registering Windows Scheduled Task: $TaskName"
Write-Host "Python Executable: $PythonPath"
Write-Host "Target Script: $ScriptPath"

# Trigger: Every 6 hours indefinitely
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)

# Action: Run Python with run_scheduled_scrapers.py
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ScriptPath" -WorkingDirectory $WorkingDir

# Settings: Allow on battery, start when available, wake computer, retry on failure
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 15)

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Description "Runs Fragrance Finder multi-domain scraper every 6 hours with Neon PostgreSQL telemetry streaming." `
        -User "$env:USERDOMAIN\$env:USERNAME" `
        -Force

    Write-Host "Task '$TaskName' successfully registered for 6-hour interval execution!" -ForegroundColor Green
} catch {
    Write-Warning "Could not register scheduled task: $_"
}
