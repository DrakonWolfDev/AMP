# Technical risks

The Windows renderer baseline now runs successfully. The reproducible desktop probes under `tools/` provide renderer validation.

- Render API ownership/threading and cleanup were checked against downloaded libmpv headers and binding source. Qt owns the GL context; normal core commands run on a worker. Other drivers/platforms and long stress runs remain untested.
- Qt grabFramebuffer can repaint; AMP reads the preserved existing FBO instead. Paused pixels match Qt capture and readback does not render a new frame. Exact OS compositor timing has not been externally compared.
- Qt's exposed readback pointer API rejected the probe buffer. The implementation uses maintained PyOpenGL rather than an improvised FFI bridge.
- Python round differed from Qt at DPR 1.5. Qt QSize rounding fixed the observed missing pixel row, confirmed by the repeated equality/dimension probe.
- Freeing an active render context can emit an end-file error as it disables the VO. Intentional shutdown now marks the backend closing first; the session probe requires no unexpected errors.
- The verified official LGPL Windows runtime is local and ignored. Its upstream rolling asset may disappear; setup fails rather than silently choosing an unverified replacement. See RENDERER_AND_PACKAGING.md.
- Context loss currently closes the viewport backend; recovery is not implemented. Audible-output quality/hardware latency, huge captures/PNG encoding responsiveness, hover/fade controls, multiple monitors, Linux Mint and Wayland remain open. Windows programmatic WASAPI release and worker/event-thread cleanup now pass the playback probe. Corrupt-video/music auto-skip passes the navigation probe, including bounded all-broken traversal and stale-request rejection.
- Exact dependency/FFmpeg build licensing, source/relink obligations, notices and clean-machine packaging need audit before any binary release. There is no distribution compliance claim or installer yet.
