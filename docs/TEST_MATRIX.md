# Test matrix — 2026-10-21

## Final packaged candidate and Windows acceptance — 2026-10-21

[Package preview run 39581705214](https://github.com/DrakonWolfDev/AMP/actions/runs/39581705214)
passed Windows, Linux and corresponding-source jobs at commit
`f0bed107bdd836b62751f6e6369e205ecf63e2a8`. Windows passed 136 unit tests; Linux passed
131 with one Windows-specific module skipped. Both packaged runtimes passed 17 smoke checks,
including subtitle framebuffer composition and natural advancement to a second music track.
Linux used Xvfb/software GL and a null audio sink; Windows used the exact downloaded frozen
runtime on the local desktop through Media Foundation. Both subtitle captures were visually
inspected. All 307 Windows and 306 Linux runtime file hashes matched their inventories;
installer/package hashes, the nine pinned upstream source archives and the exact project-source
archive were verified. The agreed privacy and codec-scope wording accompanies both packages.

The user subsequently reported that Windows passes testing. Record this as user-reported
Windows acceptance of the final candidate; individual clean-machine, association and uninstall
checks were not separately enumerated. Manual Linux/Mint acceptance of this exact package is
next and remains pending. This documentation update does not change either binary.

## Final source checks — 2026-10-21

The Windows source environment passes all 135 unit tests, Ruff lint/format and dependency
checks. The real-window source smoke test passes 17 checks through Windows Media Foundation,
including local SRT framebuffer composition, natural EOF advancement to a second WAV track,
two independent video windows, screenshots and decoder shutdown. The user also confirmed
music advancement in the source application. Windows source setup now uses `.venv-windows`,
leaving Linux's `.venv` intact. These results precede the final packaged candidate; final
artifact results must be recorded separately and do not inherit a blanket acceptance claim.

> Windows playback has changed from bundled libmpv to Qt's native Media Foundation backend.
> Windows results below describe the former renderer unless explicitly rerun and marked as Media
> Foundation evidence. The final candidate's current results and Windows acceptance are recorded above.

## Linux package, animated GIF and Trash validation — 2026-10-20

The current source passes 108 unit tests plus Ruff lint/format. The amd64 Debian builder passes its tests, freeze and `dpkg-deb` gates. Manual Mint testing confirmed package install, uninstall and reinstall; animated GIF playback; confirmation and restoration-safe Trash handling; and automatic display of the next naturally sorted image after deletion. A native Linux OpenGL probe also exercised the real `QFile.moveToTrash()` call and verified that the framebuffer changed to the next image. This exposed and fixed a PySide Linux binding difference where the static method returns a boolean despite its stub advertising a tuple.

Human testing confirmed audible playback on Linux and Windows and confirmed fullscreen plus movement between monitors with different scaling on both platforms. These results supersede older historical entries below that list Linux audio, monitor transitions or fullscreen scaling as pending. Native assistive-technology testing, deliberate graphics-context loss, prolonged soak testing and clean-machine testing of the new GitHub-produced installers remain open.

The manually triggered GitHub **Package previews** workflow builds Linux and Windows artifacts from one commit. Its Windows hosted runner is a non-interactive build environment, so the packaged GL/media smoke test is explicitly skipped there and remains part of target-desktop acceptance testing. No public release or legal-clearance claim is made.

[Package preview run 39409743922](https://github.com/DrakonWolfDev/AMP/actions/runs/39409743922) passed on 2026-10-20 at commit `26d4d68`: Linux amd64 Debian-package and Windows x64 installer jobs both completed their tests, packaging and artifact upload. Installation and interactive desktop acceptance of those exact downloads remain pending.

## Hover pause/flicker near fullscreen button - 2026-10-18

The user clarified that the pause and flicker begin while moving to the fullscreen button, without clicking. A baseline tooltip event created a separate native QTipLabel window while all six overlay opacity effects remained enabled. This is distinct from a fullscreen state transition; no fullscreen workaround or geometry delay was added for hovering.

Hints now render as a plain child label within the existing canvas and never create a native tooltip window for main-window controls. They hide on leave, input, fullscreen changes and idle fade. Fully visible overlays disable their QGraphicsOpacityEffect, and repeated reveal calls only restart the idle timer. Effects are enabled for actual fades and removed from the visible hover/paint path. Diagnostics preserve effect state when grabbing widgets.

Validation: 90 unit tests and lint/format pass. A new 21-check hover probe passes at DPR 1.25 and 1.5, moving from the bottom transport toward fullscreen and dwelling for a hint on windowed/fullscreen image and video. No native tooltip, fullscreen/size transition or changed media pixels occur; playing video advances. Maximum sampled event-loop gaps were 13.23 ms at 1.25 and 18.07 ms at 1.5 on this machine. Existing 34-check pointer/fullscreen, 19-check browser and nine-check style probes also pass. These are Qt/framebuffer/event-loop checks; the user's visible compositor flicker still needs confirmation with the rebuilt app. Evidence uses windows-hover-* and windows-*-hover names.

## v1 readiness and standalone Windows build - 2026-10-18

The Windows build uses PyInstaller and Inno Setup. The helper requires an explicit compiler path, runs quality checks, freezes the app, preserves Python/freezer notices, excludes unused Qt PDF/Multimedia and development FFmpeg, smoke-tests the executable, then compiles and hashes the installer. CI installs the pinned Inno Setup version through Chocolatey. Nothing is installed or published automatically.

The bundle passed all 13 media/GL/independence/shutdown smoke checks during development. Actual install/upgrade/uninstall and clean Windows validation remain pending.

Refreshed Windows validation: 86 unit tests, lint/format, 35 UI checks, 21 window resilience checks, six process-isolation checks and 62 quantitative capture checks at each of DPR 1.25 and effective 1.5. Updated old UI probe panel assumptions and made the process probe's output/fixtures independent of the resilience harness. These test harness corrections do not change playback behavior. All refreshed report JSONs use release-review/current-review/release-125/release-150 names in evidence.

RELEASE_READINESS.md is the current v1 gate list; HANDOVER.md and the roadmap now reflect standalone delivery. Linux desktop and standalone packaging, clean Windows install/upgrade/uninstall, human listening/native desktop checks and exact native corresponding-source/notices/patent assessment remain required. No clean-OS, Linux, long-soak or completed legal-release claim is made.

## Menu and dialog styling - 2026-10-18

The secondary menu now uses an amber top edge and warm selection treatment. About, keyboard help and Settings share an AMP header, restrained amber accents, a separate action footer and centered A WOLF FORGE PROJECT attribution. About presents the preview version, licence/warranty, copyright and dependency notice locations. Keyboard help uses an aligned shortcut table. Settings keeps existing preference behavior with compact numeric controls. Dialog content scrolls at small sizes while actions and attribution remain available; standard native title bars and Escape behavior are retained. No external assets, online links or update checks were introduced.

Validation: 86 unit tests and lint/format pass. A ten-check actual-Qt dialog probe passes at Windows DPR 1.25 and 1.5, exercising footer bounds, Escape, small-dialog scrolling and actual modal Settings Save/Cancel with isolated preferences. Menu, About, Settings and help renders were visually inspected. Evidence: windows-dialogs-125.json and windows-dialogs-150.json. Linux/native assistive-technology checks remain pending.

## Collapsible folder browser and clear idle canvas - 2026-10-18

Open media now sits at the right and toggles an overlay folder browser (also Ctrl+B). The browser lists immediate subfolders and supported media in natural order, with folders first and the current media highlighted. Single-click file opening reuses this window; browsing folders does not interrupt playback. Up, Choose folder, refresh and the existing native file picker cover navigation. No recursive scan, watcher, saved folder history or network access was added.

Both the button and drawer now join the normal idle fade, including fullscreen image/video. The invisible drawer passes pointer events through to the media; movement or Tab restores the expanded browser. Interaction/hover prevents premature fading. The overlay does not resize the media or enter its captured framebuffer. Small drawers omit the footer controls (Ctrl+O remains available) to retain list space.

Validation: 86 unit tests and lint/format pass. A 16-check live browser probe passes at Windows DPR 1.25 and 1.5: folder/file navigation, current-item marking, right-side placement, idle transparency, pointer restoration, fullscreen images, paused video capture stability, collapse and 540x400/500x260 bounds. Normal and compact Qt compositions were inspected. The nine-check style and 33-check music presentation probes also pass with the updated fading behavior. Native folder-picker interaction and Linux remain manual checks. Evidence: windows-browser-125.json, windows-browser-150.json, windows-style-browser.json and windows-music-browser.json.

## Responsive music and opening another file - 2026-10-18

Music artwork now fits the available content area instead of stopping at a fixed 300 logical pixels. The cover/title group is centered within that area, keeps the artwork aspect ratio and scales typography and the fallback record motif with the player. Compact lyric views retain their thumbnail.

A labelled Open media button remains available while the other controls fade in windowed mode and fullscreen music. It uses the existing native file picker, starts in the current file's folder, replaces media in the same window and lets the user browse elsewhere. Fullscreen images/video retain a clear canvas; Ctrl+O and the menu remain available. Cancelling preserves the current file. No folder history, scan or network operation was added.

Validation: 82 unit tests and lint/format pass, including rendered cover growth/aspect/bounds across 500x300, 540x400, 960x640 and 1536x864. The extended 33-check music presentation probe passes at Windows DPR 1.25 and 1.5, including idle-button access and picker selection/cancellation with injected dialog results. Large and small Qt compositions were inspected. The nine-check style probe also passes. Evidence: windows-music-responsive-125.json, windows-music-responsive-150.json and windows-style-responsive.json. Native dialog browsing itself and Linux remain manual checks.

## Offline music presentation - 2026-10-18

Music reads embedded title/artist/album metadata, still artwork and text lyrics locally using pinned Mutagen 1.47.0. Companion same-basename LRC files take priority over TXT and embedded lyrics. Timestamped lyrics follow playback, forward/backward seeking and replay; plain text scrolls with the wheel or Page Up/Page Down and Home. L or the music menu toggles lyrics per window. Wide views combine a cover and lyric pane; compact views keep a thumbnail. Without artwork, a quiet record motif decorates the title. Linked artwork URLs are ignored; no online lookup, directory scan or media write was added.

Metadata work runs on the existing core worker, with load tokens rejecting stale results after switching media. Text reads and artwork decoding are bounded; malformed optional metadata falls back to the filename. Mutagen's upstream licence and notice are preserved. Runtime packaging inputs now include the additional dependency; older preview packages have not been rebuilt for this feature.

Validation: 77 unit tests and lint/format pass. The new 29-check music_presentation_probe passes at Windows DPR 1.25 and 1.5 using real generated MP3, FLAC, M4A and Ogg/Vorbis tags. It checks embedded covers/lyrics, LRC priority, playback/seek/replay synchronization, plain scrolling, hide/show, compact layout and stale metadata rejection. Compositions were visually inspected. The existing 44-check playback and nine-check style probes also pass. Audio remains muted/zero-volume; Linux and audible listening are not newly validated. Evidence: windows-music-presentation-125.json, windows-music-presentation-150.json, windows-playback-music.json and windows-style-music.json.

## Mute, image fit and video speed - 2026-10-18

Mute persists automatically in local preferences without overwriting other settings. The volume rail shows zero while muted, retains backend volume changes and restores the level on unmute; raising the rail unmutes. New windows use the configured default volume beneath their remembered mute. Reset fit now depicts an image inside frame corners instead of a rotation arrow. Video controls have a compact 0.25x-2x speed rail left of the transport buttons; clicking the multiplier restores 1?. New files start at 1?, and music hides this control.

Validation: 68 unit tests and lint/format pass. Live Windows checks cover remembered mute in a newly opened player, retained volume on loading media, decoder observer synchronization, actual fast/slow video clock advancement, speed reset and normal-speed music. The style probe passes all nine checks, including the 540-pixel window; the compact composition was inspected. Audio checks use muted/zero output. Evidence: windows-playback-controls.json and windows-style-controls.json. Linux and audible listening remain pending.

## Pointer/fullscreen regression - 2026-10-18

64 unit tests pass, including direct rail clicks near EOF, full-height dragging while clock updates arrive, release outside the rail, keyboard Home/End and absolute volume input. A live 34-check interaction probe passes at DPR 1.25 and effective 1.5. It exercises real pointer events against libmpv, playing/paused seeking, endpoint/replay, video fullscreen continuity, six corner-button transitions with duplicate-click suppression, valid presented image pixels at one physical size, exact windowed composition restoration, F autorepeat rejection, F11/Escape, maximized restoration and capture refusal during transitions. Evidence: windows-interaction-125.json and windows-interaction-150.json.

The broader 38-check playback probe also passes with isolated preferences and explicit natural-EOF setup. A user's saved repeat setting cannot invalidate its no-repeat assertions. Fullscreen frame traces verify Qt output; external compositor flicker remains a visual confirmation step. No new Linux or monitor-transition claim is made.


## Visual style pass - 2026-10-18

The full-client canvas and floating controls are exercised at native Windows 125% and effective 150%. The style probe checks removal of permanent menu/status bars, image-only controls, pointer pass-through at filenames/empty corner space, idle hiding, compact transport, icon accessibility/tooltips, fullscreen pointer hiding/restoration and a 540-pixel window. Qt-widget/media composition previews were inspected for empty, image, music, video, small-window, feedback and menu states; these previews exclude native decorations and are not an OS compositor comparison.

The 35-check UI probe, 38-check playback/output-state probe, 62-check capture regression at each DPR and 21-check window resilience probe pass after styling. 60 unit tests and lint/format pass. JSON evidence uses the windows-*-style and windows-style-* filenames. Audio checks remain muted/zero-volume. Linux, monitor transitions and native assistive-technology checks remain pending.


## M8/M9 update - 2026-10-18

60 unit tests and local source checks pass. Windows resilience: 21 assertions, 48 mixed-media switches, 16 alternating navigation actions and ten reopen/close cycles. Different folders/cores/render contexts, volume/mute/pause/seek/transforms, capture retry ownership, deleted/corrupt files, fullscreen/resizing, Ctrl+N ownership removal, survivor playback and thread-free closes are checked. The process probe verifies two distinct PIDs with isolated decoder/view state and captures, survival of the other process's exit and normal shutdown of both. Playback regression: 38 zero-volume/muted checks, including two audio windows and output release. Evidence: windows-resilience-m8.json, windows-processes-m8.json, windows-playback-m8.json.

M9 builds source/wheel offline with pinned tools, checks licence and source inclusion, installs hashed runtime wheels into a new venv without Qt Addons/dev packages, and runs the standalone installed-wheel media/GL smoke test outside the source tree. Evidence: windows-packaging-m9.json; instructions: PACKAGING.md. The native runtime remains the existing separately installed libmpv, not a redistributed runtime bundle.

These are local Windows desktop and fresh-venv checks. Mint/Wayland, a clean Windows OS, driver/context loss, monitor transitions, audible listening, native OS integration, prolonged soaking and the native dependency/source redistribution audit remain pending. No remote CI result or public release is claimed.


## M7 update ? 2026-10-18

58 unit tests pass, plus local Ruff lint/format. Windows UI integration validates idle fade/reveal; hover, keyboard focus, timeline drag and open-menu protection; unchanged framebuffer pixels and viewport dimensions during fading; Settings persistence and new-window default volume; repeat for video/music and EOF stop when disabled; Space/S/R/F/Esc; music/image/video mode switching; and configurable forward/backward wrap notices. Component renders of the toolbar, transport and Settings were visually inspected. Evidence: windows-ui-m7.json.

Capture regression at native DPR 1.25 and effective DPR 1.5 passes for landscape/portrait, zoom/pan, playing/paused/seek/resize/reset, physical sizes, control exclusion, save failure and retained-frame retry. The first 150% attempt exposed a stale video-dimension observation after switching; the current-token refresh fix and two regression tests address it, and final capture runs pass. Evidence: windows-capture-m7-125.json and windows-capture-m7-150.json. Existing 20-check session probe passes (windows-session-m7.json), including two independent videos and Right over the timeline navigating files.

UI tests use injected Qt events and temporary local settings; screenshots use framebuffer readback, not whole-window QWidget.grab. Audible output, OS compositor comparison, native picker/OS association, Linux/Mint desktop, accessibility with assistive software and monitor transitions remain pending. No new remote CI execution is claimed. Earlier entries below retain historical results.


M5/M6 update: 54 unit tests pass, including partial writes and denied output without overwriting existing data. Live capture tests passed 63 checks at native DPR 1.25 (including two real Pictures/AMP saves via action/S), 61 at effective DPR 1 and 1.5, and 62 in the final guarded-readback/retry run. Fourteen compositions per run cover image fit/pan and portrait/landscape video fit, letterboxed zoom, playing pan, paused seek, resize and reset. Expected image reference versus decoded-video samples differed by at most one RGB level in the native run. Physical sizes match Qt rounding, consecutive reads do not advance the renderer, and source fixture hashes are unchanged. Save-failure retry preserves pixels across a media change. A settled paused dynamic-video frame also matches Qt framebuffer bytes exactly. See windows-capture-*.json and windows-renderer-m6.json. Reference videos explicitly specify BT.709; these are composition tests, not a colour-management certification. Linux desktop and OS compositor timing remain untested.

[M5/M6 CI run 39120942010](https://github.com/DrakonWolfDev/AMP/actions/runs/39120942010) passed all 54 unit tests and lint/format on Windows and Ubuntu; it does not run desktop GL capture tests.

M4 update: 52 unit tests pass, including seek-boundary/unavailable-duration cases. The Windows playback probe passed 38 assertions with real WASAPI output at zero volume: H.264/AAC, pause/clock, exact timeline and ±5-second seek bounds, EOF/replay/no advance, volume/mute observer sync, same-duration media reload, WMV2/WMA WMV and H.264/AAC TS/MTS/M2TS, silent/video/image audio-output release, independent audio windows, rapid-switch close under two seconds and no leftover worker/event threads. Video/multiwindow and decoder-error navigation regressions pass. See windows-playback.json. Audible sound quality/latency is untested; Linux desktop playback remains deferred. User manually confirmed Windows image/video zoom/pan.

[M4 CI run 39118037634](https://github.com/DrakonWolfDev/AMP/actions/runs/39118037634) passed all 52 unit tests plus lint/format on Windows and Ubuntu. Desktop/audio integration evidence above comes from Windows only.

M3 update: 43 unit tests pass, including all EXIF orientation/mirror cases, PNG/JPEG/JFIF/BMP/WebP/GIF/TIFF decoding, GIF/TIFF first-frame/page behaviour, @2x handling, size-limit errors, portrait/ultrawide cursor anchors and zoomed-resize stability. Live image probes at DPR 1.25 and 1.5 exercise rendered quadrant colours/black bars/physical dimensions for portrait, ultrawide, 24-megapixel PNG and all EXIF cases, transparency, actual mouse/keyboard/fullscreen input, actual CLI entry point, picker selection/cancellation routing and real Qt local-file/remote-URL drag events. Picker results are injected, so native picker interaction remains manual QA. Image JSON evidence: windows-images-125.json and windows-images-150.json. The broader historical baseline below is retained; Linux desktop playback is still untested.

Both image runs passed 130 checks. The shared-transform video-renderer regression and corrupt-media navigation probe also passed. [CI run 39117119903](https://github.com/DrakonWolfDev/AMP/actions/runs/39117119903) passed lint, format and all 43 unit tests on Windows and Ubuntu. Linux desktop GL, native picker UI and actual OS drag/drop remain outside these automated claims.

M2 reliability update: 17 unit tests pass. A live navigation probe exercises corrupt MP4/MP3/PNG traversal forwards and backwards, accumulated skip counts, wrap notice expiry after three seconds, direct-open failure, bounded traversal of an all-broken folder, and rejection of a stale error after a new image opens. The video/multiwindow and music probes pass with request-correlated loading.

Windows and Ubuntu CI both passed lint, format and all 17 unit tests in [run 39116295011](https://github.com/DrakonWolfDev/AMP/actions/runs/39116295011). The workflow now installs the EGL/OpenGL libraries QtGui needs on Ubuntu. Linux desktop rendering, playback and Mint-specific behaviour remain untested; the earlier table below records the original local baseline.

Music/wrap update: 15 unit tests pass, including circular ordering, wrap flags in both directions, deleted anchors and single-file folders. The live Windows music probe exercises nine audio extensions (WAV/MP3/FLAC/Ogg/Opus/M4A/AAC/WMA/AIFF), transport/seek, mode switching and visible forward/backward loop banners. The probe uses zero volume, so this verifies decoding and transport rather than audible sound. The historical navigation boundary checks below refer to an earlier build; current behaviour intentionally wraps.

Windows development desktop: Python 3.12.10, Qt/PySide6 Essentials 6.12.0, python-mpv 1.0.8, PyOpenGL 3.1.10, mpv v0.41.0-dev-gfffe7a23a; Intel Iris Xe OpenGL 3.3.0 (31.0.101.3729). Native scaling: 125%. Effective 100% and 150% used Qt overrides, not changed OS settings.

| Area | Windows result | Mint 22.3 |
| --- | --- | --- |
| Unit tests | 13 passed: transforms, ordering/filtering/deleted anchor/boundaries, PNG collisions/pixels/dimensions/encoding/storage/Pictures errors, missing-runtime guidance | Not run locally |
| Source/setup | Ruff lint/format and pip check passed; setup install/checksum/extraction passed in existing environment; clean machine untested | Instructions only |
| M0 renderer | Generated portrait PNG and 640×360 H.264 MP4; playing/paused zoom/pan, seek/resize/switch/resume/close passed | Not run |
| Capture | Seven captures per DPR; readback does not increment render count; paused pixels exactly equal Qt framebuffer; inspected PNGs exclude toolbar/chrome | Not run |
| Navigation/input | clip2 before clip10; corrupt image skipped; Right over seek slider changes file; new file resets fit; Esc leaves fullscreen | Not run |
| Video formats | Synthetic H.264 MP4/MKV and VP9 WebM produce live frames; all fixtures have no audio | Not run |
| Transport | Pause state, duration >10 seconds, seek to 5 seconds within 1 second tolerance passed | Not run |
| Independent windows | Different folders/cores, independent zoom/volume UI state, one playing while one paused, separate PNGs, second survives first closing | Not run |
| Storage | Probe directory saves and unit error/collision tests passed; native Pictures permissions not exercised | Not run |
| Images | Portrait PNG inspected; EXIF-rotated JPEG, huge/ultrawide, BMP/WebP untested | Not run |
| Audio | Not tested; volume/mute wired; audible playback and shutdown pending | Not run |
| Controls polish | Fixed bars; hover/fade not implemented | Not run |
| Resilience | Basic switching/resize/seek/fullscreen/close passed; rapid stress, context loss, monitor transitions, multiple processes pending | Not run |
| Packaging | No installer or binary release | Not run |

## Capture dimensions

Expected dimensions use Qt QSize rounding (half pixels up).

| DPR | Logical viewport before / after resize | Expected PNG before / after | Actual |
| --- | --- | --- | --- |
| 1.0 | 800×555 / 900×605 | 800×555 / 900×605 | Exact match |
| 1.25 native | 800×555 / 900×605 | 1000×694 / 1125×756 | Exact match |
| 1.5 | 800×555 / 900×605 | 1200×833 / 1350×908 | Exact match |

The original Python-round implementation produced 832 rather than 833 at 150%; comparison with Qt caught this and the corrected run passed. Native-DPR fit/zoomed video and portrait captures were visually inspected for crop/aspect/bars and absent controls. OS compositor latency and exact monitor pixels have not been externally compared.

Reproduction commands are in README.md. The session harness enters real Qt event loops to allow libmpv worker callbacks to run. Desktop probes require a visible desktop. CI defines unit/static checks only and does not prove renderer behaviour.
