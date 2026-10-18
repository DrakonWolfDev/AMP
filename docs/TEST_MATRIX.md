# Test matrix

All application checks below are **not run**. No renderer or application exists yet.

| Area | Required cases | Windows | Mint 22.3 |
| --- | --- | --- | --- |
| M0 rendering | Live video in Qt-owned GL surface; image mode; aspect fit; resize/switch/close | Not run | Not run |
| Capture | Playing/paused, off-centre zoom/pan, bars, no controls, actual versus expected physical dimensions | Not run | Not run |
| DPI | 100%, 125%, 150%; screen transitions when available | Not run | Not run |
| Images | Portrait, ultrawide, EXIF-rotated JPEG, large PNG, BMP, WebP | Not run | Not run |
| Video | MP4/H.264, MKV, WebM, silent video; report actual codecs/runtime | Not run | Not run |
| Transforms | Cursor anchor, bounds, reset, fullscreen, resize under zoom, seek while zoomed | Not run | Not run |
| Navigation | clip2/clip10; mixed folder; deleted/corrupt/unsupported files; no recursion/wrap | Not run | Not run |
| Controls | Shortcuts, slider focus, hover/fade, image/video modes, fullscreen exit | Not run | Not run |
| Capture storage | OS Pictures/fallback, collision, unwritable folder, useful error | Not run | Not run |
| Isolation | Two active videos in different folders; independent state/capture/close | Not run | Not run |
| Resilience | Rapid navigation, close/reopen, no lingering audio or GL crashes | Not run | Not run |
| Packaging | Clean environment install, dependency diagnostics, runtime/licence inventory | Not run | Not run |

Record each execution with date, OS/display backend, GPU, Python/Qt/libmpv versions, command, fixture identity, expected/actual result and evidence location. Keep private media and generated captures out of Git. Report untested paths explicitly.
