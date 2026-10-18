# Renderer and runtime notes

## Architecture and API verification

The installed python-mpv 1.0.8 source was inspected alongside the downloaded libmpv `render.h` and `render_gl.h`. The project uses `MpvRenderContext`, `opengl_init_params`, `opengl_fbo`, update callbacks, and explicit free. The ctypes proc-address callback belongs to the maintained binding; AMP does not invent libmpv ABI signatures.

Qt owns the OpenGL context and framebuffer. Render callbacks only emit a queued Qt signal. Normal core commands/property writes run on a per-window serial worker, separately from the Qt rendering thread. Each window owns a core, render context and transform. Cleanup disables error reporting for intentional VO teardown, frees the render context while Qt's GL context is current, then terminates the core.

Images use QImageReader auto-transform and QPainter in the same isolated GL surface. Video zoom is log2(scale); mpv pan values are logical-pixel offsets divided by the scaled media dimensions. See the [mpv manual](https://mpv.io/manual/master/#options-video-pan-x) and [Render API headers](https://github.com/mpv-player/mpv/blob/master/include/mpv/render.h).

`grabFramebuffer()` can trigger a fresh paint. AMP instead reads the preserved current Qt FBO using PyOpenGL `glReadPixels`, flips bottom-origin rows, and copies into a QImage. The probe asserts readback does not increment the render count and compares it pixel-for-pixel with Qt's own framebuffer capture while paused. QOpenGLWidget uses PartialUpdate so its last framebuffer is preserved after composition. Physical dimensions use Qt QSize rounding; Python round gave a one-pixel discrepancy at 150% scaling and was replaced. See [Qt framebuffer documentation](https://doc.qt.io/qt-6/qopenglwidget.html#grabFramebuffer).

This validates framebuffer composition, not a promise about exact operating-system compositor presentation latency. Multi-monitor/context recreation, other drivers and Linux remain open validation work. A destroyed context currently closes its viewport backend; automatic recovery after context loss is not implemented.

## Local Windows runtime

- Official repository: https://github.com/mpv-player/mpv
- Asset: `libmpv-v0.41.0-dev-gfffe7a23a-39086651352-x86_64-w64-mingw32-lgpl.zip`
- Source revision: `fffe7a23a` (as identified by runtime/asset).
- SHA-256: `9eda5c48918422bf28e211240b9010687f05e239c086d568aa86cc851a80fa6a`
- Runtime reports `mpv v0.41.0-dev-gfffe7a23a`.
- Archive comes from the upstream rolling `git-release`; the exact URL is in `tools/setup_windows.ps1`. If removed upstream, setup fails rather than silently selecting an unverified runtime. Retain the verified local archive or deliberately choose and validate a replacement.

The archive contains headers and LICENSE.LGPL. It is a development dependency under ignored artifacts, not a released AMP bundle. Synthetic fixtures are produced by imageio-ffmpeg 0.6.0's development-only executable, not used by AMP for playback or screenshots.

## Licensing and packaging status

No AMP licence has been chosen. PySide6/Qt Essentials 6.12.0 and shiboken6 6.12.0, python-mpv 1.0.8, PyOpenGL 3.1.10, and the exact libmpv build are the runtime inventory for this preview. Qt/PySide6 provide LGPL/GPL/commercial licensing options; python-mpv follows the linked libmpv licence; the selected libmpv archive is labelled LGPL and carries LGPL 2.1 text. Those facts do not constitute a complete redistribution audit.

Before shipping, inspect each exact distribution's metadata/licences and FFmpeg build configuration; collect dependency notices and corresponding-source/relinking obligations as applicable; decide the AMP licence; and validate an installer on clean Mint and Windows machines. No bundled binary installer, codec-support guarantee, licence-compliance conclusion, tag or release is provided here.
