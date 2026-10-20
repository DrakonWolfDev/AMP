# Technical risks

The earlier Windows libmpv renderer baseline ran successfully. Windows now has a Media Foundation
replacement which still needs the reproducible desktop probes under `tools/` on a real Windows host.

- Linux retains the checked libmpv Render API path. Windows receives `QVideoSink` frames from Qt's
  native Media Foundation backend and paints them into the existing OpenGL viewport.
- Qt grabFramebuffer can repaint; AMP reads the preserved existing FBO instead. Paused pixels match Qt capture and readback does not render a new frame. Exact OS compositor timing has not been externally compared.
- Qt's exposed readback pointer API rejected the probe buffer. The implementation uses maintained PyOpenGL rather than an improvised FFI bridge.
- Python round differed from Qt at DPR 1.5. Qt QSize rounding fixed the observed missing pixel row, confirmed by the repeated equality/dimension probe.
- Freeing an active render context can emit an end-file error as it disables the VO. Intentional shutdown now marks the backend closing first; the session probe requires no unexpected errors.
- Qt deprecated its native Windows backend in Qt 6.10 and plans to remove it in the next major Qt
  release. AMP pins Qt 6.12 for this release; a direct Media Foundation integration will be needed
  before moving to a Qt version that removes the plugin.
- Context loss currently closes the viewport backend; recovery is not implemented. Audible playback, hover/fade controls, multiple monitors, scaling and fullscreen have been exercised on Linux and Windows. Huge captures/PNG encoding responsiveness, deliberate context loss, native assistive technology, Wayland-specific behavior and long soaking remain open. Windows programmatic WASAPI release and worker/event-thread cleanup pass the playback probe. Corrupt-video/music auto-skip passes the navigation probe, including bounded all-broken traversal and stale-request rejection.
- The next Windows preview must prove that no libmpv/FFmpeg payload remains and must repeat video,
  audio, seeking, AMP-rendered external SRT, capture, fullscreen and lifecycle tests.
