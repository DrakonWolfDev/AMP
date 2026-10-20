# Renderer and runtime notes

## Architecture and API verification

The installed python-mpv 1.0.8 source was inspected alongside the downloaded libmpv `render.h` and `render_gl.h`. The project uses `MpvRenderContext`, `opengl_init_params`, `opengl_fbo`, update callbacks, and explicit free. The ctypes proc-address callback belongs to the maintained binding; AMP does not invent libmpv ABI signatures.

Qt owns the OpenGL context and framebuffer. Render callbacks only emit a queued Qt signal. Normal core commands/property writes run on a per-window serial worker, separately from the Qt rendering thread. Each window owns a core, render context and transform. Cleanup disables error reporting for intentional VO teardown, frees the render context while Qt's GL context is current, then terminates the core.

M4 adds request-correlated file-loaded property snapshots, exact seek bounds and EOF/replay handling on the core worker. Gapless audio reuse is disabled, and queued UI commands check closing state before execution. A zero-volume Windows probe confirmed WASAPI output creation and release on silent-video/image switches, independent audio cores and worker/event-thread termination. This does not measure audible quality or hardware-buffer latency. New WMV/transport-stream extension support uses existing libmpv decoders and does not add a runtime dependency or constitute codec-patent clearance.

Images use QImageReader auto-transform and QPainter in the same isolated GL surface. Video zoom is log2(scale); mpv pan values are logical-pixel offsets divided by the scaled media dimensions. See the [mpv manual](https://mpv.io/manual/master/#options-video-pan-x) and [Render API headers](https://github.com/mpv-player/mpv/blob/master/include/mpv/render.h).

Image loading is isolated in image_backend.py. It keeps Qt's existing allocation limit, checks declared dimensions before full decoding, applies all EXIF transforms, and normalises icon-style @2x DPR metadata to actual media pixels. TIFF shows its first page; GIF animation is driven by Qt's image plugin and repainted through the same transformed viewport. GIF/JPEG/TIFF/WebP plugins are present in the pinned Qt Essentials wheel's installed file inventory; no new image runtime library was introduced. Pillow is development-only fixture generation. Shared resize math preserves the media point at the viewport centre, and smaller zoomed axes can pan inside letterbox space to retain cursor anchoring.

`grabFramebuffer()` can trigger a fresh paint. AMP instead reads the preserved current Qt FBO using PyOpenGL `glReadPixels`, flips bottom-origin rows, and copies into a QImage. The probe asserts readback does not increment the render count and compares it pixel-for-pixel with Qt's own framebuffer capture while paused. QOpenGLWidget uses PartialUpdate so its last framebuffer is preserved after composition. Physical dimensions use Qt QSize rounding; Python round gave a one-pixel discrepancy at 150% scaling and was replaced. See [Qt framebuffer documentation](https://doc.qt.io/qt-6/qopenglwidget.html#grabFramebuffer).

This validates framebuffer composition, not a promise about exact operating-system compositor presentation latency. Multi-monitor and scaling transitions have been tested manually on Linux and Windows; other drivers and deliberate context recreation remain open validation work. A destroyed context currently closes its viewport backend; automatic recovery after context loss is not implemented.

On Mint 22.3 under X11 with an NVIDIA RTX 4060 and driver 595.99.02, Qt created an
8-bit `GL_RGBA8` QOpenGLWidget framebuffer. Querying the active attachment at runtime and passing
its format explicitly in `MPV_RENDER_PARAM_OPENGL_FBO` fixed incorrect purple VP9 output on the
hardware OpenGL path; software OpenGL and VLC had already rendered the same file correctly. The
runtime query also preserves compatibility if Qt selects a renderbuffer or a different colour
format on another driver. The affected VP9 Profile 0/Opus MKV then rendered correctly through AMP
without `LIBGL_ALWAYS_SOFTWARE`.

M5/M6 track the media request and physical size last painted into the FBO and refuse capture if those no longer match. Disk writes reserve collision-safe names exclusively, detect short writes and attempt partial-file removal on failure. Failed saves retain the QImage for retry. Portrait/landscape known-pattern videos with explicit BT.709 conversion/tags provide composition-reference checks at DPR 1/1.25/1.5; no source-frame extraction is used as the actual capture. Dynamic video readback is separately tested; the pause comparison waits for decoder pause and a presented pause frame before comparing direct FBO bytes with Qt's repainting capture API.

## Local Windows runtime

- Official repository: https://github.com/mpv-player/mpv
- Asset: `libmpv-v0.41.0-dev-g6a262d11f-39135297726-x86_64-w64-mingw32-lgpl.zip`
- Source revision: `6a262d11f` (as identified by runtime/asset).
- SHA-256: `f3a6d4bc4571fd02cd229cd30077d45deba699b1cf75a9a6fc4b707833ad1120`
- The setup pin was refreshed on 2026-10-20 because the upstream `git-release` is rolling and removed the previously validated asset. The last manually tested Windows runtime reported `mpv v0.41.0-dev-gfffe7a23a`; the replacement must still pass the packaged desktop acceptance run.
- Archive comes from the upstream rolling `git-release`; the exact URL is in `tools/setup_windows.ps1`. If removed upstream, setup fails rather than silently selecting an unverified runtime. Retain the verified local archive or deliberately choose and validate a replacement.

The archive contains headers and LICENSE.LGPL. It is a development dependency under ignored artifacts, not a released AMP bundle. Synthetic fixtures are produced by imageio-ffmpeg 0.6.0's development-only executable, not used by AMP for playback or screenshots.

## Licensing and packaging status

AMP's own code is AGPL-3.0-only. See LICENSE, THIRD_PARTY_NOTICES.md and docs/LICENSING.md. PySide6/Qt Essentials 6.12.0 and shiboken6 6.12.0, python-mpv 1.0.8, PyOpenGL 3.1.10, and the exact libmpv build are the documented runtime inventory. Dependencies retain their original licences. The selected libmpv archive is labelled LGPL and carries LGPL 2.1 text; this label does not constitute a complete dependency or redistribution audit.

Before shipping, complete the exact dependency notices and corresponding-source/relinking obligations in `CODEC_AUDIT.md`, then validate the GitHub-built installers on clean Mint and Windows machines. Legal information is accessible from Help → About AMP / licences. Installable previews exist, but no codec-patent clearance, completed release-compliance conclusion, signed release, tag or deployment is provided here.

## M9 local package validation

See [PACKAGING.md](PACKAGING.md) for the pinned offline source/wheel builder and fresh minimal-venv smoke test. The generated report records exact artifact/dependency hashes, wheel licence metadata/notice paths and the separate libmpv DLL hash/build configuration. The runtime reports FFmpeg git-2026-10-18-89d34d6 and mpv build option `-Dgpl=false`; neither that option nor wheel metadata is a complete transitive audit. A fresh venv on this machine is not a clean-machine Windows installation. No standalone/frozen runtime or installer is produced.


## Runtime audit update - 2026-10-18

See [CODEC_AUDIT.md](CODEC_AUDIT.md) for the latest evidence. The libmpv DLL embeds FFmpeg LGPL version 3 or later notices, despite the archive containing LGPL 2.1 text. The installed Qt Essentials wheel also includes an unused FFmpeg/Multimedia stack. Mutagen 1.47.0 is now a runtime dependency under GPL-2.0-or-later. These findings refine the earlier inventory; a complete binary redistribution audit is still pending.
