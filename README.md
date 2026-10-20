# AMP — Andy’s Media Player

A small, private-by-design desktop player for local images, videos and music on Linux Mint and Windows.

AMP will fit media to the viewport, offer cursor-focused zoom and drag-pan, browse neighbouring files, and save the visible media viewport as a PNG. Video playback and each window's state remain independent. No accounts, telemetry, cloud services, or media library scans.

## Run from source on Windows

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

## Install on Linux Mint

Build the Debian package (or use a supplied build), then install it with APT:

```sh
.venv/bin/python -m pip install -r requirements-linux-build.txt
.venv/bin/python tools/build_linux_deb.py --output artifacts/linux-deb
sudo apt install ./artifacts/linux-deb/amp-media-player_0.8b_amd64.deb
```

The package registers AMP with the desktop's **Open With** list for its supported image,
video and audio types without changing existing defaults. It also installs the `amp`
command, so `amp /path/to/media.mkv` works from a terminal.

## Linux development setup

On Mint 22.3, install Python 3.12 with venv support, `libmpv2`, and Qt/OpenGL runtime dependencies (`libegl1`, `libopengl0`, `libgl1`). The Ubuntu CI runner needed these libraries before Qt image tests could import. Then:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m amp /path/to/media.mp4
```

Qt's xcb plugin may need distribution packages such as `libxcb-cursor0`.

## Controls

Images: PNG, JPEG/JPG/JFIF, BMP, WebP, animated GIF, and TIFF/TIF (first page). EXIF rotations/mirroring are applied automatically. Very large images exceeding Qt's decoded-image allocation limit produce a size/limit message; the original file is never reduced or modified. HEIC/AVIF support remains future work.

Video extensions accepted: MP4, MKV, WebM, MOV, AVI, M4V, MPG/MPEG, WMV, TS, MTS and M2TS. Tested samples include H.264/AAC MP4 and transport streams, H.264 MKV, silent MKV, VP9 WebM and WMV2/WMA WMV. Extensions identify containers, not a guarantee that every codec/profile inside them will decode on every runtime.

For local subtitles, place a matching SRT file beside the video. `Film.srt`, `Film.en.srt`
and similar `Film.<label>.srt` names are attached when `Film.mkv` (or another supported video)
opens. The exact-name subtitle is selected first. AMP checks only that folder and matching basename;
recursive and general external-file autoloading remain disabled. Subtitles start hidden for each
video; use the CC button in the playback controls to show or hide them.

| Input | Action |
| --- | --- |
| Ctrl+O / drag local file into window | Open |
| Delete | Confirm, then move the currently open file to the OS Trash / Recycle Bin |
| Left / Right | Previous / next supported image, video or music file; wraps with a three-second amber notice |
| Wheel / left drag | Zoom towards pointer / pan |
| R | Reset fit |
| Optional wheel-navigation mode | Wheel up/down selects previous/next; middle click toggles wheel zoom/navigation |
| Space | Play / pause video or music; Replay from the end |
| Transport bar | Seek ±5 seconds, timeline, CC subtitles, volume, mute |
| S / camera icon / Screenshot in the menu | Save media viewport to OS Pictures/AMP |
| F / F11 / media double click | Toggle fullscreen |
| Esc | Leave fullscreen |
| Ctrl+N | Independent new window |
| Three-dot menu / right click | New window, lyrics (music), Settings, update check, keyboard help and licences |
| Ctrl+, | Settings |

Screenshots read the last rendered media framebuffer without advancing video, exclude the controls/title bar, include visible bars/crop, and use physical viewport pixels. Existing files are never overwritten. If saving fails, the capture stays in memory and S retries it; closing the window discards this in-memory retry. Source media is never changed.

During a media/viewport update, capture waits for a valid rendered frame by reporting that the view is updating; press S again in a moment. A capture that failed before readback does not claim to retain a frame. Partial disk writes are reported as failures, with partial files removed where possible. If a PNG save failed after capture, retry preserves that exact earlier frame even after you open another file.

Music uses the same playback/seek/volume controls, with local artwork, lyrics and a decorated title view. Screenshots and reset-fit are disabled in music mode. MP3, FLAC, WAV, Ogg/Vorbis, Opus, M4A/AAC, WMA and AIFF decoding were exercised with synthetic fixtures on the local runtime; codec support depends on the installed libmpv build. By default AMP opens the next music track in the folder at a track's end. Folder wrapping works in both directions, skips unreadable files, and does not restart a lone file. Tests ran at zero volume; audible output remains a manual listening check.

The timeline supports direct click-to-seek and dragging across its full height, including near either end. Video stops at natural EOF and shows **Replay**; music advances to the next track unless music repeat is enabled. Video repeat and music repeat are separate and off by default.

At the end of a video the transport shows **Replay**; clicking it or pressing Space starts the video from the beginning. Music advances to the next music track unless music repeat is enabled. Video repeat and music repeat are separate and off by default. Short seeks and timeline seeks are clamped to the file's duration. Mute shows the volume slider at zero and restores the retained level when unmuted. Moving the volume slider above zero unmutes playback. Mute is remembered for future windows; their restore level uses the configured default volume. Video has a speed slider to the left of the transport buttons (0.25×–2×); click its multiplier to reset to 1×. Each newly opened file starts at normal speed, and music hides this control. Volume/mute widgets follow decoder changes, and seek controls are disabled when seeking is unavailable. Per-file state is refreshed even for consecutive files with identical durations.

## Status and limitations

Real GL probes on Windows passed image and H.264 video capture, transforms, seek/resize/switch/shutdown at 100%, native 125%, and 150% effective Qt scaling. Linux Mint testing covers images, animated GIFs, video, music, subtitles, local/NAS media, PipeWire audio, Trash navigation and Debian install/uninstall. Human testing on Linux and Windows confirmed audible playback, fullscreen and moving AMP between monitors with different scaling. Automatic graphics-context recovery and native assistive-technology testing remain open.

### Offline music artwork and lyrics

Embedded artwork and title/artist/album tags display locally. Artwork and text scale with the player, with aspect-correct covers centered in the available space. Covers and embedded text lyrics were verified in MP3 (ID3), FLAC, M4A and Ogg/Vorbis files. If artwork is absent, a quiet record motif decorates the title; untagged files use their filename without the extension. Linked artwork URLs are ignored.

Put a UTF-8 or BOM-marked UTF-16 lyric file beside the music with the same basename: `Song.flac` and `Song.lrc`. LRC timestamps highlight the current line and follow playback, seeking and replay. Repeated timestamps, multiple lines at one timestamp and millisecond offsets are supported. The order is companion `.lrc`, companion `.txt`, then embedded text lyrics. Plain lyrics scroll with the wheel or Page Up/Page Down; Home returns to the top. Press **L**, or use **Show lyrics** in the music menu, to show/hide lyrics. This choice is independent in each window. Artwork and lyrics share wide windows; small windows use a cover thumbnail. No downloads, online lookups, background folder scans or media writes are performed.

The labelled **Open media** button is on the right. Click it or press **Ctrl+B** to expand/collapse a folder browser. Click a file to open it in this window, click a subfolder to browse it, use **Up** for its parent, or **Choose folder** to jump elsewhere. The current media is highlighted; browsing a folder leaves playback running. The list reads only that folder when requested, with no recursive index or filesystem watcher. **Ctrl+O** and the browser's **Choose a file** button retain the native file picker. At idle the browser, its button and the other controls all fade; pointer movement or Tab restores them. Hovering or keyboard interaction keeps them available. Choosing a file collapses the browser; Left/Right navigation keeps it closed until you reopen it with Open media or Ctrl+B. Browsing subfolders keeps it open.

Button hover hints are drawn inside AMP rather than opening separate native tooltip windows. Fully visible controls bypass opacity effects; idle fading still applies.

Menus and AMP dialogs use a shared dark palette with restrained amber accents. About includes Wolf Forge copyright and project attribution with paw prints, plus Website and GitHub links that open your browser only when clicked; dialog content scrolls in smaller windows while footer actions remain available.

The media fills the canvas. Small floating icon controls and the filename fade after 2.2 seconds of inactivity; fullscreen video also hides the idle pointer. There are no permanent menu or status bars. The three-dot menu or right click exposes secondary actions, Settings and help. Previous/next buttons remain fixed at the left and right sides for every media format. Image mode has a small reset/capture dock; playback uses a compact floating timeline and transport. Pointer movement or Tab reveals them; hover, keyboard focus, slider dragging and open menus keep them visible. Image mode hides playback controls. The menu lists keyboard help; native window decorations remain available. Navigation skips corrupt images, videos and music in the chosen direction and stops after trying each candidate once if none is readable. Opening a corrupt file directly reports an error and leaves manual navigation available. Settings stores separate video and music repeat choices (off by default), default volume for new windows, the folder-wrap notice duration, and optional wheel navigation. Hardware decoding is disabled. See [release readiness](docs/RELEASE_READINESS.md) and [packaging notes](docs/PACKAGING.md).

## Checks

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check amp tools tests
.\.venv\Scripts\python -m ruff format --check amp tools tests
# Requires a visible Windows desktop and AMP_MPV_DIR, plus dev dependencies:
.\.venv\Scripts\python -m tools.render_probe
.\.venv\Scripts\python -m tools.session_probe
.\.venv\Scripts\python -m tools.music_probe
.\.venv\Scripts\python -m tools.music_presentation_probe
.\.venv\Scripts\python -m tools.navigation_probe
.\.venv\Scripts\python -m tools.image_probe
.\.venv\Scripts\python -m tools.playback_probe
.\.venv\Scripts\python -m tools.capture_probe
.\.venv\Scripts\python -m tools.ui_probe
.\.venv\Scripts\python -m tools.style_probe
.\.venv\Scripts\python -m tools.browser_probe
.\.venv\Scripts\python -m tools.dialog_probe
.\.venv\Scripts\python -m tools.interaction_probe
.\.venv\Scripts\python -m tools.hover_probe
.\.venv\Scripts\python -m tools.resilience_probe
.\.venv\Scripts\python -m tools.process_probe
# Optional: saves two verification PNGs into the real OS Pictures/AMP folder:
.\.venv\Scripts\python -m tools.capture_probe --native-pictures
```

The renderer probe generates synthetic local fixtures and PNGs in ignored `artifacts/probe`. Run it before the session probe. The UI and resilience probes also use playback_probe fixtures; run playback_probe first. The process probe uses resilience_probe fixtures. On this native 125% display, `QT_SCALE_FACTOR=0.8` and `1.2` exercise effective DPR 1 and 1.5; use `--output artifacts/probe-100` or `--output artifacts/probe-150` to retain separate reports. These environment overrides do not test changing OS display settings or moving between monitors. CI runs source checks and unit tests, not desktop renderer probes.

The manually triggered **Package previews** GitHub Actions workflow builds an amd64 Debian package and a Windows x64 installer from the same commit. These are unsigned test artifacts, not published releases. The Windows CI runner deliberately skips the interactive GL/media smoke test; test the downloaded installer on a normal desktop before treating it as validated.

## Specification

- [Product roadmap](AMP_ROADMAP.md): behaviour and milestone acceptance criteria.
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): build order and validation.
- [Local packaging](docs/PACKAGING.md): offline builds, exact dependency inventory and fresh-install checks.
- [Technical risks](docs/TECHNICAL_RISKS.md): renderer gate and open decisions.
- [Test matrix](docs/TEST_MATRIX.md): planned platform checks.

The stack is Python, PySide6/Qt 6 Essentials, PyOpenGL for readback, Mutagen for local music tags, and python-mpv wrapping libmpv's OpenGL Render API. All media operations are local. mpv user configuration/scripts, external-file autoloading and reference following are disabled; FFmpeg protocols are restricted to local files. There is no analytics, database or background media scan. A manual update check contacts GitHub only when selected. Optional automatic checks are disabled by default and require confirmation; when enabled they read public AMP release metadata from GitHub at most once every 24 hours. AMP never sends media paths or usage data and never downloads or installs an update. No diagnostics log is written. Preferences are stored in Qt's local AppConfigLocation: `%LOCALAPPDATA%/AMP/AMP/preferences.ini` on Windows and `${XDG_CONFIG_HOME:-~/.config}/AMP/AMP/preferences.ini` on Linux. No media paths or playback history are stored. Delete this file while AMP is closed to restore defaults.

AMP is licensed under the [GNU Affero General Public License, version 3 only](LICENSE) (`AGPL-3.0-only`). Copyright © 2026 Andrew Hodgson trading as Wolf Forge. Dependencies retain their own licences; see [third-party notices](THIRD_PARTY_NOTICES.md), the [codec and bundle audit](docs/CODEC_AUDIT.md), and the [licensing policy](docs/LICENSING.md). Public binary release remains blocked until exact corresponding-source archives and complete Qt/libmpv/FFmpeg transitive notices are prepared; the audit is not legal advice or patent clearance.


### OS file associations

The Windows installer offers an optional, unchecked **Register AMP in Open with (keep existing defaults)** task. It registers supported images, video and music for the current user and advertises AMP to Windows Default apps. It does not replace existing defaults or write Windows UserChoice settings; choose AMP as a default through Windows Settings or Open with. Uninstall removes AMP registration values while preserving other applications' handlers. Native install/Open with/default selection/uninstall still need clean-machine verification.

The Debian package installs `packaging/linux/amp.desktop`, including supported media MIME types. Desktop environments then offer AMP in **Open With** while leaving current defaults unchanged.
