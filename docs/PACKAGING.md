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

## Fedora 44 RPM preview (x86_64)

Build on Fedora 44 x86_64, using its system Python (currently 3.14), not on Mint
or Ubuntu. The builder rejects other target releases and architectures.

```sh
sudo dnf install python3 python3-devel binutils rpm-build desktop-file-utils mpv-libs libglvnd-egl libglvnd-opengl libglvnd-glx xcb-util-cursor xcb-util-wm xcb-util-keysyms xcb-util-image xcb-util-renderutil libxkbcommon-x11
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip install -r requirements-linux-build.txt
.venv/bin/python tools/build_linux_rpm.py --output artifacts/fedora-rpm
sudo dnf install ./artifacts/fedora-rpm/*.rpm
```

The builder shares the frozen runtime, inventory gate, notices and desktop layout
with the Debian builder. It produces an unsigned upstream RPM such as
`amp-media-player-0.8~b0-1.fc44.x86_64.rpm`. The `~b0` suffix sorts this Python beta
before the final `0.8` RPM version. Private Qt/Python libraries do not become
system library providers; their requirements are filtered only where the matching
library is present in the bundle. Automatic system ABI requirements are retained
and checked, alongside explicit libmpv/OpenGL/X11 plugin dependencies.

KDE SMB drops use the optional system `kio-fuse` service (`sudo dnf install
kio-fuse` if absent); AMP does not bundle KDE KIO or Samba. The system libmpv
build determines codec availability. Stock Fedora HEVC support is not guaranteed;
AMP does not enable extra repositories or install codec packs. A VP9/AAC fixture
is available with `tools/release_fixtures.py --video-codec libvpx-vp9` for stock
Fedora tests. H.264/HEVC acceptance must identify the actual system decoder set.

To remove the preview, use `sudo dnf remove amp-media-player`. Like the Debian
package, it leaves existing file defaults alone and uses desktop/icon file
triggers supplied by Fedora. Preferences and user-created screenshots are not
removed. Do not install both AMP's DEB and RPM on one system.

This frozen upstream RPM is not a Fedora package collection submission. Such a
submission would need a separate packaging review, including the distribution's
bundling and licence-expression requirements. See
[Fedora release review](FEDORA_RELEASE_REVIEW.md) for tested scope and remaining gates.

## RPM (Fedora, x86_64) and AppImage

Use the native Fedora builder above for RPM. The Debian builder also accepts `--format appimage`. All formats
use the same tested PyInstaller payload, licence inventory and bundle exclusion policy.
On Ubuntu 24.04 install `rpm` and `squashfs-tools` alongside the Debian runtime libraries;
on Fedora install `rpm-build`, `python3-devel`, `mpv-libs`, `libglvnd-egl`,
`libglvnd-glx`, `libglvnd-opengl`, `xcb-util-cursor`, `xcb-util-wm`,
`xcb-util-keysyms`, `libxkbcommon-x11` and `squashfs-tools`. Prepare the same Python
virtual environment and pinned build requirements as above, then run:

```sh
.venv/bin/python tools/build_linux_rpm.py --output artifacts/linux-rpm
.venv/bin/python tools/build_linux_deb.py --format appimage --output artifacts/linux-appimage
sudo dnf install ./artifacts/linux-rpm/amp-media-player-0.8b-1.x86_64.rpm
chmod +x artifacts/linux-appimage/AMP-0.8b-x86_64.AppImage
./artifacts/linux-appimage/AMP-0.8b-x86_64.AppImage
```

Use a new output directory on each run. RPM installs the same `/opt/amp` application,
`amp` command, icon and Open With integration as DEB. AppImage runs in place and
requires distribution-provided libmpv and graphics libraries; it does not install
Open With entries. Its tool and runtime downloads are pinned and SHA-256 verified.
The RPM builder preserves the audited frozen binaries without stripping them again.
CI freezes on Ubuntu 24.04; validate install, playback and removal on Fedora before
publishing. These are unsigned packages, with published SHA-256 checksums.

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
- Build Windows artifacts on Windows and Linux artifacts on the oldest supported Linux base.
- Record the SHA-256 digest for every published installer.

## GitHub preview builds

Run **Package previews** from the repository's Actions tab to build Linux amd64 DEB, RPM and
AppImage packages and Windows x64 test artifacts from the selected commit. The workflow does not publish a release. Download the
artifacts and perform the clean-machine checks above. GitHub's Windows runner is non-interactive,
so its build explicitly skips the standalone GL/media smoke test and records that fact in
`report.json`; this is not a substitute for testing the installer on a desktop.

The preview artifacts include the exact Windows frozen runtime ZIP for desktop self-testing,
Linux packaged smoke results from Xvfb, and a separate hash-verified corresponding-source archive
containing the exact project commit. The smoke fixtures are generated locally by
`tools/release_fixtures.py`; their FFmpeg generator is a development dependency and is excluded
from application bundles. The test does not imply that AMP ships FFmpeg.

## GitHub releases

A version-matched `v*` tag builds Windows plus all three Linux formats from the
same commit. Publication waits for every build, verifies all required files,
and includes every format in `SHA256SUMS.txt`. The website dispatch names
`windows`, `linux_rpm`, `linux_deb` and `linux_appimage` separately. Existing
release approval and corresponding-source gates remain required.
