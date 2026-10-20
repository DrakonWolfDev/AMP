# Renderer and packaging notes

AMP has separate platform playback backends behind the same viewport-facing property interface.

## Linux

Linux retains python-mpv and the libmpv OpenGL Render API. Qt owns the `QOpenGLWidget` context and
libmpv renders into its framebuffer. The Debian package depends on the distribution's `libmpv2`
and deliberately excludes libmpv, FFmpeg and Qt Multimedia from the frozen application.

## Windows

Windows uses `QMediaPlayer`, `QAudioOutput` and `QVideoSink` from Qt Multimedia with
`QT_MEDIA_BACKEND=windows`. That selects Qt's native Media Foundation plugin. Frames are converted
to `QImage` and painted into the same OpenGL viewport used for images, so AMP's fit, zoom, pan,
overlays and framebuffer screenshots remain shared UI behaviour.

The Windows source install depends on PySide6 Addons. The PyInstaller specification retains
`Qt6Multimedia.dll` and the native Windows media plugin, but filters out Qt's FFmpeg plugin and
FFmpeg DLLs. The bundle policy independently rejects libmpv and FFmpeg payloads if they reappear.
No `AMP_MPV_DIR`, downloaded codec archive or bundled `libmpv-2.dll` is used on Windows.

Media Foundation supplies common system-supported formats. Codec/container support can vary with
the Windows version, hardware and installed codec extensions. AMP parses matching external SRT
files independently of the playback backend and paints active cues into the shared viewport.

Qt deprecated this native backend in Qt 6.10 and plans to remove it in the next major Qt release.
AMP therefore pins Qt 6.12 for this implementation. Before a future major Qt upgrade, replace this
adapter with direct Media Foundation integration or another audited system-codec path; never allow
an unnoticed fallback to Qt's FFmpeg plugin.

## Capture

`grabFramebuffer()` can request a repaint and advance video. AMP instead reads the preserved
current Qt framebuffer with `glReadPixels`, flips the bottom-origin rows and copies them into a
`QImage`. This path is shared by images, Linux libmpv frames and Windows Media Foundation frames.

See `PACKAGING.md`, `CODEC_AUDIT.md` and `TEST_MATRIX.md` for build and acceptance gates.
