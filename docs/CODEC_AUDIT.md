# Codec and bundle audit

This is an engineering compliance record, not legal advice or patent clearance.

## Current architecture

- Linux uses the distribution's `libmpv2`. The Debian archive does not contain libmpv, FFmpeg or
  Qt Multimedia.
- Windows uses Qt Multimedia's native Windows backend, selected with
  `QT_MEDIA_BACKEND=windows`. Playback is provided by Windows Media Foundation and the codecs
  available on the machine.
- The Windows bundle policy rejects `libmpv`, Qt's `ffmpegmediaplugin`, FFmpeg libraries and the
  development-only `imageio-ffmpeg` runtime.
- Video frames arrive through `QVideoSink` and are painted into AMP's existing OpenGL viewport,
  retaining zoom, pan and framebuffer capture without shipping a decoder implementation.

The former Windows `libmpv-2.dll` distribution path has been removed from setup, dependencies,
the PyInstaller specification, release preflight and source manifests. Linux remains unchanged.

## Redistributed source and notices

The Windows application redistributes PySide6 Addons, Qt Multimedia and Qt's native Windows media
plugin. `legal/source-manifest.json` pins the official Qt Multimedia 6.12.0 source archive and its
SHA-256 alongside Qt Base, Qt SVG, PySide6/shiboken6 and the other redistributed components. The
release source bundle is generated and hash-checked by `tools/source_compliance.py`.

Qt is dynamically linked under the selected LGPLv3 route. The generated package must retain Qt's
licence and attribution material and allow replacement of its shared libraries as described in
`QT_REDISTRIBUTION.md`.

## Required release evidence

Before approving a Windows binary release:

1. Inspect the generated inventory and confirm the native Windows media plugin and
   `Qt6Multimedia.dll` are present.
2. Confirm no libmpv DLL, FFmpeg plugin/library, development fixture runtime, JAR, test media or
   credentials are present.
3. On a clean supported Windows installation, test MP4/H.264/AAC video, MP3/WAV audio, seek,
   volume/mute, playback speed, EOF/replay/repeat, switching files, screenshots, fullscreen,
   multi-window playback and clean shutdown.
4. Record unsupported system-codec cases honestly. HEVC and less common containers/codecs may
   require an OS extension and are not guaranteed merely because AMP accepts their extension.
5. Publish the source archive and SHA-256 checksums beside the intentionally unsigned installer.

External SRT files are parsed and rendered by AMP rather than a decoder backend. The Windows
acceptance pass must check cue timing, CC visibility and subtitle inclusion in screenshots.

## Maintenance risk

Qt deprecated its Windows Media Foundation backend in Qt 6.10 and states that it will be removed
in the next major Qt release. AMP pins Qt 6.12 for this release. A future Qt-major upgrade must
either retain the audited Qt version or replace the Qt plugin with a direct Media Foundation
backend; it must not silently fall back to Qt's FFmpeg backend.

Primary references: [Qt Multimedia backends](https://doc.qt.io/qt-6/qtmultimedia-index.html),
[Microsoft Media Foundation formats](https://learn.microsoft.com/en-us/windows/win32/medfound/supported-media-formats-in-media-foundation),
[Qt licensing](https://doc.qt.io/qt-6/licensing.html), and
[Qt for Python licences](https://doc.qt.io/qtforpython-6/licenses.html).
