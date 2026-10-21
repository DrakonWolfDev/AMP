[CmdletBinding()]
param([string]$Python = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    # Virtual environments are platform-specific. A shared checkout can retain
    # Linux's .venv while Windows uses its own interpreter and wheels.
    $environmentPython = Join-Path $projectRoot '.venv-windows\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $environmentPython)) {
        $candidates = @()
        if ($Python) {
            $candidates += ,@($Python)
        } else {
            # Respect an activated environment or actions/setup-python on PATH
            # before falling back to the launcher's newest installed Python.
            foreach ($name in @('python', 'python3', 'py')) {
                $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
                if ($command -and $command.Source -notlike '*\Microsoft\WindowsApps\*') {
                    if ($name -eq 'py') { $candidates += ,@($command.Source, '-3') }
                    else { $candidates += ,@($command.Source) }
                }
            }
            # uv-managed Python may be installed without a python command on PATH.
            $uvRoot = Join-Path $env:APPDATA 'uv\python'
            if (Test-Path -LiteralPath $uvRoot) {
                Get-ChildItem -LiteralPath $uvRoot -Directory -Filter 'cpython-*-windows-x86_64-none' |
                    Sort-Object Name -Descending | ForEach-Object {
                        $candidate = Join-Path $_.FullName 'python.exe'
                        if (Test-Path -LiteralPath $candidate) { $candidates += ,@($candidate) }
                    }
            }
        }
        $selected = $null
        foreach ($candidate in $candidates) {
            $arguments = @($candidate | Select-Object -Skip 1)
            try {
                & $candidate[0] @arguments -c "import sys; sys.exit(0 if sys.platform == 'win32' and sys.version_info >= (3, 12) and sys.maxsize > 2**32 else 1)" 2>$null
                if ($LASTEXITCODE -eq 0) { $selected = $candidate; break }
            } catch {
                # A stale launcher must not prevent trying the next installation.
                continue
            }
        }
        if (-not $selected) {
            throw '64-bit Windows Python 3.12+ was not found. Install it, or pass -Python "C:\path\to\python.exe".'
        }
        $arguments = @($selected | Select-Object -Skip 1)
        & $selected[0] @arguments -m venv .venv-windows
        if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
    }
    & $environmentPython -c "import sys; sys.exit(0 if sys.platform == 'win32' and sys.version_info >= (3, 12) and sys.maxsize > 2**32 else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw 'The .venv-windows environment is unusable. Rename that folder and run setup again.'
    }
    & $environmentPython -m pip install -e '.[dev]'
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    Write-Output 'Setup complete. Launch with .\AMP.cmd or .\AMP.cmd "C:\path\to\media.mp4"'
} finally {
    Pop-Location
}
