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
The package declares Qt's X11 cursor, ICCCM, key-symbol and xkbcommon-X11 runtime
dependencies, including on systems that do not already have a full desktop dependency set.

## Windows installer

Windows binaries must be built on a 64-bit Windows host; PyInstaller output is
platform-specific and Inno Setup is a Windows compiler. Prepare the development environment
as described in the README, then run:

```powershell
.\.venv-windows\Scripts\python -m pip install -r requirements-build.txt
.\.venv-windows\Scripts\python tools\build_windows_preview.py `
  --output artifacts\windows-build `
  --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

The helper creates a PyInstaller one-folder bundle and, when `--iscc` is supplied, an Inno
Setup installer. The installer offers an optional, unchecked per-user task to register AMP
in Windows Open With without changing existing defaults. Its playback runtime is Qt Multimedia's
native Windows Media Foundation plugin. The build rejects libmpv, FFmpeg DLLs and Qt's FFmpeg plugin.

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

The preview artifacts include the exact Windows frozen runtime ZIP for desktop self-testing,
Linux packaged smoke results from Xvfb, and a separate hash-verified corresponding-source archive
containing the exact project commit. The smoke fixtures are generated locally by
`tools/release_fixtures.py`; their FFmpeg generator is a development dependency and is excluded
from application bundles. The test does not imply that AMP ships FFmpeg.
