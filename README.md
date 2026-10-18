# AMP — Andy’s Media Player

A small, private-by-design desktop player for local images, videos and music on Linux Mint and Windows.

AMP will fit media to the viewport, offer cursor-focused zoom and drag-pan, browse neighbouring files, and save the visible media viewport as a PNG. Video playback and each window's state remain independent. No accounts, telemetry, cloud services, or media library scans.

## Run the Windows preview

Python 3.12 or newer, 64-bit Windows, and a working OpenGL 3.3 driver are required. In PowerShell from this folder:

```powershell
powershell -ExecutionPolicy Bypass -File tools/setup_windows.ps1
.\AMP.cmd
.\AMP.cmd "C:\path\to\media.mp4"
```

Setup creates `.venv`, installs the pinned Python dependencies, and downloads an official LGPL libmpv development build into ignored `artifacts/runtime`. Its archive SHA-256 is checked before extraction. It changes no system settings. The upstream rolling asset may eventually be removed; if download fails, see [runtime notes](docs/RENDERER_AND_PACKAGING.md).

With another compatible libmpv installation, set `AMP_MPV_DIR` to its DLL directory. The underlying launch command is:

```powershell
$env:AMP_MPV_DIR = (Resolve-Path artifacts/runtime/libmpv).Path
.\.venv\Scripts\python -m amp
```

Images can open without libmpv; opening video without the runtime shows installation guidance in the status bar.

## Linux development setup (not yet exercised)

On Mint 22.3, install Python 3.12 with venv support, `libmpv2`, and Qt/OpenGL runtime dependencies (`libegl1`, `libopengl0`, `libgl1`). The Ubuntu CI runner needed these libraries before Qt image tests could import. Then:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m amp /path/to/media.mp4
```

Linux/Wayland and clean-machine installation are not yet validated. Qt's xcb plugin may need distribution packages such as `libxcb-cursor0`.

## Controls

| Input | Action |
| --- | --- |
| Ctrl+O / drag local file into window | Open |
| Left / Right | Previous / next supported image, video or music file; wraps with a three-second amber notice |
| Wheel / left drag | Zoom towards pointer / pan |
| R / middle click | Reset fit |
| Space | Play / pause video or music |
| Transport bar | Seek ±5 seconds, timeline, volume, mute |
| S / Screenshot button | Save media viewport to OS Pictures/AMP |
| F / F11 / media double click | Toggle fullscreen |
| Esc | Leave fullscreen |
| Ctrl+N | Independent new window |

Screenshots read the last rendered media framebuffer without advancing video, exclude the controls/title bar, include visible bars/crop, and use physical viewport pixels. Existing files are never overwritten. If saving fails, the capture stays in memory and S retries it; closing the window discards this in-memory retry. Source media is never changed.

Music uses the same playback/seek/volume controls and a simple filename view. Screenshots and reset-fit are disabled in music mode. MP3, FLAC, WAV, Ogg/Vorbis, Opus, M4A/AAC, WMA and AIFF decoding were exercised with synthetic fixtures on the local runtime; codec support depends on the installed libmpv build. Playback stops at a track's end; use Left/Right to choose another file. Folder wrapping works in both directions, skips unreadable images, and does not restart a lone file. Tests ran at zero volume; audible output remains a manual listening check.

## Preview status and limitations

Runnable early Windows preview. Real GL probes passed with image and H.264 video capture, transforms, seek/resize/switch/shutdown at 100%, native 125%, and 150% effective Qt scaling. A second integration probe exercised playback controls, natural folder navigation, H.264 MP4/MKV, VP9 WebM, and two independent video windows. See [recorded results](docs/TEST_MATRIX.md).

Controls currently stay visible in fixed bars; hover/fade polish is pending. EXIF orientation is enabled but rotated-JPEG fixtures, large images, sound output, audio cleanup, OS file associations and multi-monitor DPI transitions still need validation. Navigation skips corrupt images, videos and music in the chosen direction and stops after trying each candidate once if none is readable. Opening a corrupt file directly reports an error and leaves manual navigation available. Settings are not persisted. Hardware decoding is deliberately disabled in this first probe. There is no installer or release package yet.

## Checks

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check amp tools tests
.\.venv\Scripts\python -m ruff format --check amp tools tests
# Requires a visible Windows desktop and AMP_MPV_DIR, plus dev dependencies:
.\.venv\Scripts\python -m tools.render_probe
.\.venv\Scripts\python -m tools.session_probe
.\.venv\Scripts\python -m tools.music_probe
.\.venv\Scripts\python -m tools.navigation_probe
```

The renderer probe generates synthetic local fixtures and PNGs in ignored `artifacts/probe`. Run it before the session probe. On this native 125% display, `QT_SCALE_FACTOR=0.8` and `1.2` exercise effective DPR 1 and 1.5; use `--output artifacts/probe-100` or `--output artifacts/probe-150` to retain separate reports. These environment overrides do not test changing OS display settings or moving between monitors. CI runs source checks and unit tests, not desktop renderer probes.

## Specification

- [Product roadmap](AMP_ROADMAP.md): behaviour and milestone acceptance criteria.
- [Implementation prompt](CODEX_PROMPT.md): engineering requirements supplied with the project.
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): build order and validation.
- [Progress](docs/PROGRESS.md): verified status and environment.
- [Technical risks](docs/TECHNICAL_RISKS.md): renderer gate and open decisions.
- [Test matrix](docs/TEST_MATRIX.md): planned platform checks.

The stack is Python, PySide6/Qt 6 Essentials, PyOpenGL for readback, and python-mpv wrapping libmpv's OpenGL Render API. All media operations are local. mpv user configuration/scripts, external-file autoloading and reference following are disabled; FFmpeg protocols are restricted to local files. No network feature, analytics, database or background scan is implemented. No diagnostics log or settings file is written by the application.

AMP is licensed under the [GNU Affero General Public License, version 3 only](LICENSE) (`AGPL-3.0-only`), matching WolfLauncher. Copyright © 2026 Andrew Hodgson trading as Wolf Forge. Dependencies retain their own licences; see [third-party notices](THIRD_PARTY_NOTICES.md) and the [licensing policy](docs/LICENSING.md). The repository remains private; the binary/runtime redistribution audit is still required before a release.
