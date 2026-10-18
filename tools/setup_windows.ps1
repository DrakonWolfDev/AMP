$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
    }
    & ./.venv/Scripts/python.exe -m pip install -e '.[dev]'
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    $runtimeDirectory = Join-Path $projectRoot 'artifacts/runtime'
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    $archivePath = Join-Path $runtimeDirectory 'libmpv-v0.41.0-dev-gfffe7a23a-39086651352-x86_64-w64-mingw32-lgpl.zip'
    $runtimeUrl = 'https://github.com/mpv-player/mpv/releases/download/git-release/libmpv-v0.41.0-dev-gfffe7a23a-39086651352-x86_64-w64-mingw32-lgpl.zip'
    if (-not (Test-Path -LiteralPath $archivePath)) {
        Invoke-WebRequest -Uri $runtimeUrl -OutFile $archivePath
    }
    $expectedHash = '9EDA5C48918422BF28E211240B9010687F05E239C086D568AA86CC851A80FA6A'
    if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $expectedHash) {
        throw 'libmpv archive checksum mismatch. Do not use this runtime.'
    }
    Expand-Archive -LiteralPath $archivePath -DestinationPath (Join-Path $runtimeDirectory 'libmpv') -Force
    Write-Output 'Setup complete. Launch with .\AMP.cmd or .\AMP.cmd "C:\path\to\media.mp4"'
} finally {
    Pop-Location
}
