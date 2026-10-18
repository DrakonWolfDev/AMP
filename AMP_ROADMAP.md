# AMP — Andy’s Media Player
## Product roadmap | v1 readiness (original v0.1 milestones retained below)

### Delivery decision - 2026-10-18

The next target is a standalone v1 that does not require users to install Python. Windows packaging uses PyInstaller plus Inno Setup; a private preview is built/tested, but clean-machine installation and release compliance remain open. Linux desktop validation and standalone delivery are still required. This supersedes the original M9 wording that an installer is optional. OS file-association integration on Windows and Linux is also required for v1; registration must preserve existing defaults until the user chooses AMP. See [release readiness](docs/RELEASE_READINESS.md) for the current gates; the application version is not bumped until they pass.

Agreed additions implemented during UI review include local artwork/lyrics, video speed, remembered mute, the explicit single-folder browser, compact menus and branded dialogs. Explicit Website/GitHub links open the system browser only when activated; AMP does not fetch them or perform automatic lookups. No further feature expansion is required for this readiness review.

### Scope update — 2026-10-18

Local **music file playback** is now part of v0.1, alongside images and video. M4 covers music autoplay, play/pause, seeking, duration, volume/mute and clean switching using the existing per-window libmpv backend. Offer a simple music/filename view; hide image/video-only actions. Test MP3, FLAC, WAV, Ogg/Vorbis, Opus, M4A/AAC, WMA and AIFF against the chosen runtime. No library, streaming, playlist management, automatic next-track playback or track-repeat feature is added.

M2 now requires **circular folder navigation**: Right at the last supported file returns to the first; Left at the first returns to the last. Include supported images, videos and music in the same natural order. Display a prominent amber notice for three seconds identifying a return to the beginning or end; keep it outside screenshot content. A single-file folder stays on that file without restarting playback. Skip unreadable candidates at most once per navigation action; retain the wrap notice if unreadable files straddle the boundary. This explicitly replaces the earlier no-wrap requirement wherever stated below or in the original prompt. M7 covers the notice's visual treatment; M8 covers music independence and shutdown.

### 1. The idea

AMP is a small, fast, local **image and video viewer for Linux and Windows**. Open a file, see it fitted correctly, zoom with the mouse wheel, drag to pan, move through the files in that folder with the arrow keys, and save **exactly the media view on screen** as a PNG. Video gets normal playback and volume controls. Nothing more complicated should get in the way.

**The promise:** *The media is complicated enough. Viewing it shouldn’t be.*

**Product rules**
- Local-first, private by design. No account, telemetry, analytics, cloud service, network requests, advertising or forced updates.
- No collection, indexing, uploads, metadata database or whole-library scans. AMP views user-selected files and the current directory only.
- No edits to source media. Zoom/pan are presentation-only; screenshots create separate PNG files.
- Good defaults, minimal settings, no VLC-style maze of menus.
- Linux Mint 22.3 is the primary development/validation platform; Windows is a required release platform.
- Several independently launched copies/windows must work at once without shared playback, navigation, zoom or pan state.

### 2. v0.1 behaviour contract

| Area | Required behaviour |
| --- | --- |
| Start/open | Open a file from the command line / OS association, Ctrl+O, or drag-and-drop. A blank launch gives an unobtrusive **Open file** action. |
| File types | Common still images (at least PNG, JPEG, BMP, WebP when supported by Qt) and video formats the bundled/system libmpv build can decode (test MP4/H.264, MKV, WebM). Fail gracefully on unsupported/corrupt files; do not advertise formats that cannot be decoded. |
| Initial fit | Fit the entire image/video within the media viewport, preserve aspect ratio, centre it, letterbox where necessary, and do not crop. |
| Mouse wheel | Zoom towards/away from cursor location for both images and videos, with sensible bounds and steps. No window resizing. |
| Left-drag on media | Pan an enlarged image or playing/paused video. Do not accidentally seek or move the window. Clamp or otherwise avoid losing the media completely. |
| Reset | Middle-click restores fit and centred pan; also expose a visible/keyboard reset action. |
| Folder navigation | Left/right arrows open previous/next supported image, video or music file in the same directory in natural order. Wrap at either end with a three-second amber beginning/end notice. Skip unreadable files with a concise explanation, without recursive scanning or repeatedly retrying the same file. |
| Music | Local audio autoplay, play/pause, seek, duration, volume/mute and a calm filename view. No image/video screenshot or zoom actions in music mode. End-of-track stops; file navigation remains manual. |
| Video | Autoplay after opening; play/pause, seek slider, short backward/forward seek, volume/mute and duration/current time. Seeking is separate from left/right folder navigation. |
| Keyboard | Space = play/pause (video); Left/Right = previous/next file; F or F11 = fullscreen; Esc = leave fullscreen; Ctrl+O = open; Ctrl+N = new independent window; S = screenshot; R = reset fit. Keep keys consistent in image and video views. |
| Window | Double-click media toggles fullscreen. Multiple windows/processes work independently. Show filename discreetly. Minimise clutter. |
| Controls | A slim on-media playback/control bar appears on mouse movement/hover and fades after brief inactivity, except when interacting with it. Image mode hides video-only controls. Native OS decorations may remain where required for reliable window movement/resizing, particularly under Wayland. |
| Screenshot | Save a PNG of **only the actual media viewport** as displayed: current video frame, current zoom/pan, visible letterboxing/background and crop. Exclude player toolbar/controls and title/chrome. Output dimensions are **physical viewport pixels** (account for high DPI). Save to the OS Pictures folder in an `AMP` subfolder, with collision-safe timestamp filenames and clear success/error feedback. Never use mpv's original-frame screenshot as a substitute. |
| State | Changing file resets zoom/pan to fit by default. Each window has independent view/playback state. Local, minimal settings may remember reasonable defaults; opt-in per-file view memory is postponed. |

The mouse cursor and OS window borders are not part of the saved media screenshot. The screenshot includes blank/letterboxed areas within the *media viewport* because those are part of the visible composition.

### 3. Implementation direction

- **Language/UI:** Python 3 and PySide6 / Qt 6, with a small, conventional desktop application structure.
- **Video:** libmpv using the supported **Render API with OpenGL** in a Qt-owned rendering viewport. Do **not** use old `opengl-cb` or fragile `wid`/native child-window embedding as the final approach.
- **Images:** Qt image reader and rendering, with auto-applied image orientation, using a consistent viewport coordinate model. Prefer one media-only render surface (or equivalent isolated surface) so screenshots cannot accidentally include overlays.
- **Transforms:** One tested conceptual model for fit/zoom/pan. Adapt it correctly for Qt image rendering and mpv video zoom/pan options. Keep UI input handling independent of decoder internals.
- **Screenshot:** Capture composited media pixels from the viewport/framebuffer, not the original media frame and not a screenshot of the desktop or control bar. QOpenGLWidget's framebuffer capture is a candidate, to be validated against real video playback, resizing and display scaling.
- **Persistence:** Optional lightweight JSON/QSettings for window position/size, default volume and basic preferences, with a documented local path. No database.
- **Dependencies:** Pin/test versions; load libmpv explicitly with diagnostics if missing. On Windows test distribution of the needed runtime and codec libraries. Document actual licences for the exact binaries distributed; do not assume all libmpv/FFmpeg builds have the same licence.

### 4. Milestones, in build order

#### M0 — Feasibility / hardest problem first
**Do:** Confirm current PySide6 + libmpv Render API integration on Linux. Create a tiny, disposable or isolated probe that renders a video into Qt's OpenGL framebuffer, displays a still image, zooms/pans both, and captures the on-screen *media viewport* as a PNG. Test while video is playing and paused; compare aspect ratio, crop, letterboxing and actual PNG dimensions at normal and high-DPI scaling. Note any Qt/Wayland/window-decoration caveats. Make sure shutdown does not crash. Do a Windows probe as early as equipment allows.

**Gate:** Do not build the full UI on a renderer that cannot deliver an accurate screenshot or reliable video zoom/pan. If the precise approach fails, document the failure, propose the smallest sound alternative, and stop that dependency before proceeding.

#### M1 — Application skeleton and quality baseline
**Do:** Initialise package structure, launch entry point, environment/dependency instructions, a README, a development log, configuration model, test runner, formatting/linting, error reporting and basic CI if available. Ensure clean startup without a file.

**Gate:** `python -m amp` (or a clearly documented equivalent) starts with one working window; a path argument is accepted; tests run; missing libmpv produces a clear actionable message rather than a crash.

#### M2 — File opening and folder navigation
**Do:** Support open-dialog, file argument, drag/drop, media type detection, current-directory enumeration and stable natural ordering. Skip unsupported or deleted entries gracefully. Show file name and status unobtrusively.

**Gate:** A mixed folder containing `clip2.mp4`, `clip10.mp4`, still images and unrelated documents navigates in the expected order without recursion or surprise playlist/library behaviour.

#### M3 — Still-image viewer

The still-image scope includes PNG, JPEG/JFIF, BMP, WebP, TIFF/TIF (first page), and GIF (first frame). Test all eight EXIF rotation/mirror cases, transparency, 24-megapixel loading, bounded decoder allocation errors, and cursor anchoring while an axis remains letterboxed. Resize under zoom should preserve the media detail at the viewport centre where pan bounds allow. Animated playback and multipage document browsing remain outside this milestone.
**Do:** Fit-to-window, resize re-fit behaviour, correct orientation, smooth zoom at cursor, drag-pan, reset, fullscreen and image errors. Keep transform math in a separately unit-testable module.

**Gate:** Portrait, landscape, huge and oddly shaped images preserve proportions; zoom does not jump away from the pointed detail; resetting restores fit exactly.

#### M4 — Video and music playback

Transport must keep volume/mute, duration, pause and seeking availability synchronised with the backend. Refresh per-file state even when consecutive media have identical property values. Clamp seeks to media bounds. On natural EOF, stop and show Replay; Play/Space restarts the same file without automatic repeat/advance. Check AAC-bearing video, silent video and music; confirm output release on image/silent switches and independent shutdown. WMV and TS/MTS/M2TS join the accepted extensions, with actual codec coverage documented for the chosen runtime.
**Do:** Wire one mpv core/render context per AMP window; immediate local playback, pause, seek, timeline, audio volume/mute, end-of-file behaviour and clean media switching. Avoid libmpv operations inside forbidden render callbacks; schedule UI-thread work safely.

**Gate:** MP4/H.264, MKV, WebM and the agreed local music formats play as supported by the selected libmpv build. Time/seek/volume updates work; music/image/video mode switches restore appropriate controls and do not leave audio playing in the background.

#### M5 — Same zoom/pan experience for video
**Do:** Integrate cursor-anchored wheel zoom and drag-pan using mpv's supported video zoom and pan model; reset to centred fit; preserve letterboxing and correct proportions. Keep input mapping and clipping consistent with image mode.

**Gate:** While a video is actively playing, zoom into a corner, drag it, pause/seek and continue. Zoom stays stable, movement direction is intuitive, and a reset fully returns to fit.

#### M6 — What-you-see-is-what-you-save screenshot
**Do:** Capture the actual media-only rendered viewport in one operation for image and video, using physical pixels; make a collision-safe filename; save to `Pictures/AMP/`; give modest feedback. Handle unwritable folders and non-existent Pictures locations. Avoid altering the original media.

**Gate:** In a paused and playing video, with off-centre zoom/pan and visible letterboxing, open the PNG and compare against the media region on screen. Its width/height match viewport physical pixels, not video source dimensions; controls are absent. Repeat at 125%/150% scaling if available.

#### M7 — Quiet, useful UI

Agreed small local settings screen: repeat-current-file toggle (separate from circular folder navigation), default volume, and loop-banner duration. Keep the defaults simple and controls uncluttered. Repeat remains off until explicitly enabled; no repeat setting is introduced before this milestone. Store these preferences locally and document the location.
**Do:** Add polished but restrained hover/fade controls, compact transport bar, fullscreen, visible keyboard hints/help, useful drag/drop and failures. Ensure the controls don't disappear while hovered/focused/dragged and never interfere with panning. Don't make custom frameless chrome a prerequisite if it harms resizing/window management.

**Gate:** The controls are obvious when needed and unobtrusive otherwise; they remain keyboard-accessible, responsive and reliable under Linux and Windows.

#### M8 — Truly independent windows and resilience
**Do:** Support Ctrl+N plus launching AMP multiple times, with separately owned mpv cores, file directories, position, pan, zoom, volume, playback and screenshot operations. Confirm cleanup of GL/mpv resources on close; cope with deleted/corrupt media, rapid navigation, focus changes, screen resizing and fullscreen transitions.

**Gate:** Two windows can play different videos, zoom differently, browse different directories and save different PNGs simultaneously, with no state leakage or crash on closing either one.

#### M9 — Packaging, platform validation and beta handover
**Do:** Test an installable/runable Linux distribution first (Mint 22.3), then Windows. Establish reliable libmpv discovery and redistributable runtime strategy; build licences/third-party notices; file associations and installer are optional unless easy and proven. Provide a QA matrix and release notes. Build artifacts only when the tests have passed; do not publish/release without instruction.

**Gate:** Clean environment instructions work; functionality has been *tested*, not assumed, on both platforms. Anything not directly tested is marked as such.

### 5. Regression checklist for every milestone

- Media remains aspect-correct after opening, resizing, zooming, panning and fullscreen.
- Left/right keys change files, **not** video seek position; seek is available via control bar and separate shortcuts.
- Screenshot includes crop and bars but not controls or title bar; exact viewport dimensions at current device pixel ratio.
- Dragging on video pans instead of scrubbing; using a slider never pans the video.
- File navigation does not scan subfolders, write to media, create playlists or phone home.
- Launching or opening a second AMP window never steals playback/input/state from the first.
- No lingering audio, orphaned player process or GL resource crash on rapid close/reopen.
- Errors are shown humanely, logged locally if necessary, and do not crash the player.

### 6. Explicitly later, not v0.1

Per-file remembered crop/zoom, animated image playback, advanced subtitle/audio track controls, rotation, edit/export, media libraries, playlists, tagging, transcoding, Jellyfin/Audiobookshelf/Spotify connections, streaming, mobile versions, cloud sync, auto-update systems, accounts and analytics. These can be discussed later but must not creep into the initial build.

### 7. Definition of done

A user can double-click a local image or video, see it properly fitted, wheel-zoom, drag to inspect details, arrow through neighbouring files, play/seek/adjust volume where appropriate, press **S** to save exactly the cropped/letterboxed viewport in `Pictures/AMP/`, and open another copy of AMP to do something different without interference. It feels like a lightweight viewer, not a collection of technical features.
