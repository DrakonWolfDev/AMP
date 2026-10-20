# Packaging AMP

Build outputs are written below the ignored `artifacts/` directory. The helpers run tests,
lint and formatting checks before packaging and never publish or install anything.

## Debian package (Linux Mint / Ubuntu, amd64)

Install the normal development environment and the pinned packaging tools, then build:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip install -r requirements-linux-build.txt
.venv/bin/python tools/build_linux_deb.py --output artifacts/linux-deb
```

The result is `amp-media-player_<version>_amd64.deb`. Install it with:

```sh
sudo apt install ./artifacts/linux-deb/amp-media-player_0.8b_amd64.deb
```

The package installs a self-contained Python/Qt application under `/opt/amp`, an `amp`
launcher under `/usr/bin`, an application icon, and a desktop entry. The desktop entry
registers the supported image, video and audio MIME types so AMP appears in file-manager
Open With menus. It deliberately does not replace existing default applications.

libmpv and graphics libraries remain distribution packages. This avoids bundling the
host's FFmpeg/libmpv stack and lets the package manager apply system security updates.

## Windows installer

Windows binaries must be built on a 64-bit Windows host; PyInstaller output is
platform-specific and Inno Setup is a Windows compiler. Prepare the development environment
as described in the README, set `AMP_MPV_DIR` to a validated directory containing
`libmpv-2.dll`, and run:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-build.txt
.\.venv\Scripts\python tools\build_windows_preview.py `
  --output artifacts\windows-build `
  --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

The helper creates a PyInstaller one-folder bundle and, when `--iscc` is supplied, an Inno
Setup installer. The installer offers an optional, unchecked per-user task to register AMP
in Windows Open With without changing existing defaults.

## Release checks

- Test install, Open With, playback and uninstall on a clean target system.
- Preserve the bundled third-party notices and complete the native dependency/source audit.
- Build Windows artifacts on Windows and Debian artifacts on the oldest supported Linux base.
- Record the SHA-256 digest for every published installer.

## GitHub preview builds

Run **Package previews** from the repository's Actions tab to build Linux amd64 and Windows x64
test artifacts from the selected commit. The workflow does not publish a release. Download both
artifacts and perform the clean-machine checks above. GitHub's Windows runner is non-interactive,
so its build explicitly skips the standalone GL/media smoke test and records that fact in
`report.json`; this is not a substitute for testing the installer on a desktop.
