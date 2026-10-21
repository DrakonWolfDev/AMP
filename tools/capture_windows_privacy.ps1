# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

<# Capture local evidence; does not change firewall, diagnostics or AMP settings. #>
[CmdletBinding()]
param(
    [string]$AmpPath = "$env:LOCALAPPDATA\Programs\AMP\AMP.exe",
    [string]$OutputRoot = '',
    [ValidateRange(5, 120)][int]$BaselineSeconds = 30
)

$ErrorActionPreference = 'Stop'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $PSScriptRoot '..\artifacts\windows-privacy'
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open PowerShell as Administrator, then run this script again.'
}
if (-not (Test-Path -LiteralPath $AmpPath -PathType Leaf)) {
    throw "AMP executable not found: $AmpPath. Supply -AmpPath with the installed executable."
}
if (Get-Process AMP -ErrorAction SilentlyContinue) {
    throw 'Close AMP before starting so the capture includes startup and a clean baseline.'
}

$output = Join-Path ([IO.Path]::GetFullPath($OutputRoot)) (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
New-Item -ItemType Directory -Path $output | Out-Null
$trace = Join-Path $output 'network.etl'
$session = 'AMPPrivacyAudit'
$markers = Join-Path $output 'phases.jsonl'
$started = $false
$monitor = $null

function Mark-Phase([string]$Name) {
    @{ utc = [DateTime]::UtcNow.ToString('o'); phase = $Name } |
        ConvertTo-Json -Compress | Add-Content -LiteralPath $markers -Encoding UTF8
}

function Test-Phase([string]$Name, [string]$Instruction) {
    Mark-Phase "$Name-start"
    Write-Host "`n$Instruction" -ForegroundColor Cyan
    $note = Read-Host 'When finished, press Enter (or type SKIPPED and a reason)'
    @{ utc = [DateTime]::UtcNow.ToString('o'); phase = "$Name-end"; note = $note } |
        ConvertTo-Json -Compress | Add-Content -LiteralPath $markers -Encoding UTF8
}

@{
    utc = [DateTime]::UtcNow.ToString('o')
    executable = (Resolve-Path -LiteralPath $AmpPath).Path
    sha256 = (Get-FileHash -LiteralPath $AmpPath -Algorithm SHA256).Hash
    file_version = (Get-Item -LiteralPath $AmpPath).VersionInfo.FileVersion
    windows = [Environment]::OSVersion.VersionString
    baseline_seconds = $BaselineSeconds
    scope = 'System-wide ETW and packet capture; periodic process/TCP/UDP snapshots.'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'build.json') -Encoding UTF8
Get-CimInstance Win32_Service | Select-Object Name, State, ProcessId, PathName |
    Export-Csv -LiteralPath (Join-Path $output 'services-before.csv') -NoTypeInformation
& netsh trace show scenario InternetClient 2>&1 |
    Set-Content -LiteralPath (Join-Path $output 'trace-providers.txt') -Encoding UTF8

Write-Host "Evidence folder: $output"
Write-Host 'This system-wide trace can contain private traffic and local paths. Keep it local.'
Write-Host 'Close unrelated apps where practical. Leave Windows networking enabled.'
Write-Host 'Use non-sensitive files stored on the local disk for this first run.'
Write-Host 'Leave automatic AMP update checks OFF; record if they were enabled.'
Write-Host 'Open AMP normally from Start when prompted, not from this elevated shell.'
Write-Host 'Emergency stop, in another Administrator PowerShell: netsh trace stop sessionname=AMPPrivacyAudit'

try {
    # Use a dedicated session; never stop a trace that this script did not start.
    $startResult = & netsh trace start "sessionname=$session" scenario=InternetClient capture=yes report=no `
        persistent=no correlation=yes maxsize=512 filemode=single overwrite=no `
        "tracefile=$trace" provider=Microsoft-Windows-DNS-Client `
        provider=Microsoft-Windows-Kernel-Process keywords=0x10 2>&1
    $startCode = $LASTEXITCODE
    $startResult | Set-Content -LiteralPath (Join-Path $output 'trace-start.txt') -Encoding UTF8
    if ($startCode -ne 0) {
        throw "Capture could not start. See $output\trace-start.txt. No existing trace was stopped."
    }
    $started = $true
    $monitor = Start-Job -ArgumentList $output -ScriptBlock {
        param($Folder)
        while ($true) {
            $stamp = [DateTime]::UtcNow.ToString('o')
            try {
                $processes = @(Get-CimInstance Win32_Process |
                    Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CreationDate)
                $tcp = @(Get-NetTCPConnection -ErrorAction SilentlyContinue |
                    Select-Object OwningProcess, LocalAddress, LocalPort, RemoteAddress, RemotePort, State)
                $udp = @(Get-NetUDPEndpoint -ErrorAction SilentlyContinue |
                    Select-Object OwningProcess, LocalAddress, LocalPort)
                @{ utc = $stamp; processes = $processes; tcp = $tcp; udp = $udp } |
                    ConvertTo-Json -Depth 5 -Compress |
                    Add-Content -LiteralPath (Join-Path $Folder 'connections.jsonl') -Encoding UTF8
            } catch {
                "$stamp $_" | Add-Content -LiteralPath (Join-Path $Folder 'monitor-errors.txt')
            }
            Start-Sleep -Seconds 2
        }
    }
    Mark-Phase 'baseline-start'
    Write-Host "Recording $BaselineSeconds seconds with AMP closed..."
    Start-Sleep -Seconds $BaselineSeconds
    Mark-Phase 'baseline-end'

    Test-Phase 'startup-idle' 'Open AMP normally from Start. Leave it idle for 30 seconds.'
    Test-Phase 'music' 'Open local music. Let at least two tracks finish naturally. Try pause and seek. Note formats tested.'
    Test-Phase 'video' 'Play a local video for at least 30 seconds. Try pause, seek and switching files. Note formats tested.'
    Test-Phase 'invalid-media' 'Open a non-sensitive damaged/unsupported media file. Wait for the error. If none is available, mark SKIPPED.'
    Test-Phase 'shutdown' 'Close ALL AMP windows.'
    Mark-Phase 'after-shutdown-start'
    Write-Host "Recording another $BaselineSeconds seconds after shutdown..."
    Start-Sleep -Seconds $BaselineSeconds
    Mark-Phase 'after-shutdown-end'
    $control = Read-Host 'Optional positive control: test the manual GitHub update check? Type YES, otherwise Enter'
    if ($control -eq 'YES') {
        Test-Phase 'update-positive-control' 'Reopen AMP normally, select Check for updates, wait for the result, then close AMP. GitHub traffic is EXPECTED in this phase.'
    }
    $notes = Read-Host 'Notes: formats/files tested, update setting, skipped checks, unusual behaviour (avoid sensitive names)'
    $notes | Set-Content -LiteralPath (Join-Path $output 'operator-notes.txt') -Encoding UTF8
} finally {
    if ($started) {
        Mark-Phase 'capture-stopping'
        Write-Host 'Stopping and saving the trace; this may take a little while...'
        & netsh trace stop "sessionname=$session" 2>&1 |
            Set-Content -LiteralPath (Join-Path $output 'trace-stop.txt') -Encoding UTF8
        if ($LASTEXITCODE -ne 0) {
            Write-Warning 'Trace stop failed. Run netsh trace stop sessionname=AMPPrivacyAudit in Administrator PowerShell.'
        }
    }
    if ($null -ne $monitor) {
        Stop-Job $monitor
        Receive-Job $monitor 2>&1 |
            Out-File -LiteralPath (Join-Path $output 'monitor-job.txt') -Encoding UTF8
        Remove-Job $monitor
    }
    Get-CimInstance Win32_Service | Select-Object Name, State, ProcessId, PathName |
        Export-Csv -LiteralPath (Join-Path $output 'services-after.csv') -NoTypeInformation
}

@'
CAPTURE ONLY: no privacy pass/fail has been determined.
network.etl contains packets and Windows ETW events; phases.jsonl marks actions in UTC.
build.json fingerprints the selected installed executable. Confirm you launched that build.
connections.jsonl maps observed TCP/UDP endpoints to process snapshots; polling can miss short flows.
UDP endpoint snapshots do not identify remote peers. Use the ETW/packet evidence as well.
services-before/after.csv help identify service-host PIDs, but do not prove causation.
Compare baseline, playback, errors, shutdown and any separately marked update control.
Check capture loss/truncation before making a no-connections claim (512 MB single-file limit).
TLS payloads are encrypted; endpoint observations cannot establish the exact data transmitted.
Shared Windows-service traffic needs further attribution; timing alone is insufficient.
A short clean capture cannot rule out delayed diagnostics, other formats, or other Windows builds.
No firewall, Windows diagnostic setting or AMP preference was changed by this script.
Keep these files private. Nothing is uploaded automatically.
'@ | Set-Content -LiteralPath (Join-Path $output 'READ-ME.txt') -Encoding UTF8
Write-Host "`nCapture saved: $output" -ForegroundColor Green
Write-Host 'Tell Codex this folder path to begin the analysis. Do not publish the raw trace.'
