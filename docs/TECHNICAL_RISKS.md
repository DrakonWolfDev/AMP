# Technical risks

The Windows renderer baseline now runs successfully. The reproducible desktop probes under `tools/` provide renderer validation.

- Render API ownership/threading and cleanup were checked against downloaded libmpv headers and binding source. Qt owns the GL context; normal core commands run on a worker. Linux and Windows monitor/scaling/fullscreen transitions have been tested manually; other drivers and long stress runs remain untested.
- Qt grabFramebuffer can repaint; AMP reads the preserved existing FBO instead. Paused pixels match Qt capture and readback does not render a new frame. Exact OS compositor timing has not been externally compared.
- Qt's exposed readback pointer API rejected the probe buffer. The implementation uses maintained PyOpenGL rather than an improvised FFI bridge.
- Python round differed from Qt at DPR 1.5. Qt QSize rounding fixed the observed missing pixel row, confirmed by the repeated equality/dimension probe.
- Freeing an active render context can emit an end-file error as it disables the VO. Intentional shutdown now marks the backend closing first; the session probe requires no unexpected errors.
- The verified official LGPL Windows runtime is local and ignored. Its upstream rolling asset may disappear; setup fails rather than silently choosing an unverified replacement. See RENDERER_AND_PACKAGING.md.
- Context loss currently closes the viewport backend; recovery is not implemented. Audible playback, hover/fade controls, multiple monitors, scaling and fullscreen have been exercised on Linux and Windows. Huge captures/PNG encoding responsiveness, deliberate context loss, native assistive technology, Wayland-specific behavior and long soaking remain open. Windows programmatic WASAPI release and worker/event-thread cleanup pass the playback probe. Corrupt-video/music auto-skip passes the navigation probe, including bounded all-broken traversal and stale-request rejection.
- Installable Linux and Windows previews now exist, but exact Qt/libmpv/FFmpeg corresponding sources, transitive notices, LGPL replacement instructions and codec-patent assessment remain release blockers. There is no public binary distribution compliance claim.
