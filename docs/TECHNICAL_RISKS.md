# Technical risks

No renderer has been implemented or executed. These are open validation requirements, not observed renderer failures.

1. **Render API and GL lifecycle:** verify the selected binding against current libmpv headers/documentation. Qt must own the current OpenGL context/framebuffer. Queue render notifications safely to the UI thread and release render resources before the Qt context disappears.
2. **Exact capture:** validate QOpenGLWidget framebuffer capture with playing and paused video. Confirm current displayed composition, pan/zoom, bars, and physical pixel dimensions. Source-frame screenshots, frame extraction and desktop screenshots do not satisfy the contract.
3. **Transform parity:** test mpv zoom/pan units against shared cursor-anchor math, aspect fit, resize and DPI changes. Do not assume image coordinates transfer directly.
4. **Runtime discovery:** Python is present; PySide6/python-mpv are absent from the inspected environment. mpv/FFmpeg are absent from PATH. Select a compatible Windows libmpv runtime and document provenance; PATH inspection alone is not a DLL inventory.
5. **Platform coverage:** the current workspace is Windows. Mint 22.3, Wayland, other GPUs and high-DPI paths remain untested.
6. **Distribution:** audit exact Qt, binding, libmpv and FFmpeg versions/build configurations, licences and source obligations before shipping binaries. Do not infer codec support from extensions.

M0 must produce reproducible execution evidence. If a candidate approach fails, append the environment, command, observed failure and smallest alternatives here before proceeding with dependent work.
