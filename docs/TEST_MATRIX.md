# Test matrix — 2026-10-18

M3 update: 43 unit tests pass, including all EXIF orientation/mirror cases, PNG/JPEG/JFIF/BMP/WebP/GIF/TIFF decoding, GIF/TIFF first-frame/page behaviour, @2x handling, size-limit errors, portrait/ultrawide cursor anchors and zoomed-resize stability. Live image probes at DPR 1.25 and 1.5 exercise rendered quadrant colours/black bars/physical dimensions for portrait, ultrawide, 24-megapixel PNG and all EXIF cases, transparency, actual mouse/keyboard/fullscreen input, actual CLI entry point, picker selection/cancellation routing and real Qt local-file/remote-URL drag events. Picker results are injected, so native picker interaction remains manual QA. Image JSON evidence: windows-images-125.json and windows-images-150.json. The broader historical baseline below is retained; Linux desktop playback is still untested.

M2 reliability update: 17 unit tests pass. A live navigation probe exercises corrupt MP4/MP3/PNG traversal forwards and backwards, accumulated skip counts, wrap notice expiry after three seconds, direct-open failure, bounded traversal of an all-broken folder, and rejection of a stale error after a new image opens. The video/multiwindow and music probes pass with request-correlated loading. See docs/evidence/windows-navigation.json; native dialog/drop and audio-output verification remain pending.

Windows and Ubuntu CI both passed lint, format and all 17 unit tests in [run 39116295011](https://github.com/DrakonWolfDev/AMP/actions/runs/39116295011). The workflow now installs the EGL/OpenGL libraries QtGui needs on Ubuntu. Linux desktop rendering, playback and Mint-specific behaviour remain untested; the earlier table below records the original local baseline.

Music/wrap update: 15 unit tests pass, including circular ordering, wrap flags in both directions, deleted anchors and single-file folders. The live Windows music probe exercises nine audio extensions (WAV/MP3/FLAC/Ogg/Opus/M4A/AAC/WMA/AIFF), transport/seek, mode switching and visible forward/backward loop banners. The probe uses zero volume, so this verifies decoding and transport rather than audible sound. See docs/evidence/windows-music.json. The historical navigation boundary checks below refer to the earlier preview; current behaviour intentionally wraps. Linux remains untested.

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

Reproduction commands: README.md. Successful machine-readable reports: docs/evidence. The session harness enters real Qt event loops to allow libmpv worker callbacks to run. Desktop probes require a visible desktop. CI defines unit/static checks only and does not prove renderer behaviour.
