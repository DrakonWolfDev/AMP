# Implementation plan

2026-10-18 scope amendment: add local music to M4 using the existing per-window backend/transport and a filename view. M2 folder navigation now wraps at both ends with a three-second amber notice (M7); this supersedes earlier no-wrap acceptance criteria. Include music formats in sorting/filtering and validate mode switching, single-file behaviour, skipped files across the boundary, independent state and cleanup (M8). No automatic next-track playback or playlist management is introduced.

The root AMP_ROADMAP.md is the product specification.

2026-10-20 amendment: natural music EOF advances to the next music file in the folder, while video retains Replay behaviour. Video and music repeat are stored separately.

## Sequence and acceptance

| Stage | Planned code/work | Verification | Principal risk |
| --- | --- | --- | --- |
| M0 | Isolated Qt OpenGL viewport, image backend, libmpv Render API bridge, shared transform and framebuffer capture probe | Real playing/paused video, images, zoom/pan, resize, switching, shutdown, physical PNG dimensions at normal/high DPI | Render callback threading, GL ownership, capture timing and teardown |
| M1 | Package/CLI, dependency diagnostics, empty window, pinned manifest, README, static checks and CI | Blank launch, path argument, actionable missing-runtime error, automated suite | Reproducible native dependencies |
| M2 | Current-directory navigator, natural ordering, open dialog/drop/CLI | Mixed folder, clip2/clip10, deleted/corrupt files, wrapping with a visible notice | Stable ordering and graceful decoder failures |
| M3 | Qt image reader with EXIF transform and tested view-transform math | Portrait/ultrawide/large/rotated fixtures, cursor anchor, clamps, reset, resize | DPI and coordinate conversions |
| M4 | Per-window mpv backend and transport controls | Actual MP4/H.264, MKV, WebM, silent video, pause/seek/volume/switching | Callback lifetime and lingering audio |
| M5 | Adapt shared transform to documented mpv zoom/pan units | Playing/paused zoom, corner anchor, pan, seek, resize and reset | Different renderer coordinate conventions |
| M6 | Media-only framebuffer capture, Pictures resolution, collision-safe save and feedback | Compare visible crop/bars/frame with PNG; physical dimensions; save errors | Playback timing and high DPI |
| M7 | Slim overlay controls, interaction-aware fading, shortcuts/fullscreen/help, local repeat/default-volume/banner preferences | Keyboard routing, focus/hover/menu/slider behaviour, images hide transport | Controls interfering with pan or capture |
| M8 | Window ownership and independent backend lifecycle | Two active videos, folders, transforms, volumes, screenshots, independent close | Shared state and GL teardown |
| M9 | Repeatable packaging, exact dependency/licence inventory, notices and handover | Clean installs and full matrix on Mint 22.3 and Windows | Native library/codec redistribution and untested platforms |

M0 is mandatory before implementing the dependent UI. Check the binding against current upstream API documentation and selected versions before writing integration code. If M0 fails, record the evidence and smallest alternatives in TECHNICAL_RISKS.md; only continue independent work.

Use small reviewable commits. Automated tests should cover transforms, folder filtering/ordering, capture paths/names/errors, keyboard routing and session isolation where meaningful. Platform/rendering claims require execution evidence. Source publication does not imply that binary release validation is complete.
