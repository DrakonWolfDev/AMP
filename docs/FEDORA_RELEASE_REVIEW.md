# Fedora 44 release review — 21 October 2026

## Decision and scope

Fedora 44 x86_64 is suitable for an **unsigned upstream RPM preview** alongside
the existing Windows and Mint/Ubuntu preview builds. This is not final release
approval or admission to Fedora's official repositories. No release was
published and the tag-driven publication workflow is unchanged.

The existing Windows/Mint candidate approval does not cover these working-tree
changes. Rebuild all platform artifacts and their source bundle from one reviewed
commit before selecting a new release candidate.

## Code and packaging review findings

The local review found and fixed these issues:

- The frozen Linux runtime omitted `OpenGL.platform.egl`. It failed at import on
  Fedora Wayland although source playback worked. Both EGL and GLX are now
  explicitly collected; QtDBus is collected for optional SMB drops.
- The bundle policy missed versioned Linux libmpv names such as `libmpv.so.2`.
  They are now rejected alongside other forbidden decoder payloads.
- The offline runtime wheelhouse omitted the existing `packaging` dependency.
  It now includes all six runtime dependency distributions and the AMP wheel.
- The frozen smoke test accepted missing package metadata unconditionally. It
  now checks the actual required metadata, including `packaging`.
- A delayed SMB resolution could replace a file opened meanwhile through the
  file chooser or navigation. Opening any file now invalidates older replies.
- The source archive omitted the legal source manifest and preview/release
  workflows. Those build/compliance inputs are now included.
- The observed frozen runtime includes ICU 73.2 and Qt Image Formats 6.12.0.
  Their official sources are now hash-pinned, ICU's release licence is preserved,
  and Qt Image Formats' incorporated libtiff/libwebp notices are retained.

The new RPM builder shares the DEB runtime/layout and inventory gate. It records
host package versions and hashes, preserves licence files, maps `0.8b` to RPM
`0.8~b0`, retains generated system ABI requirements, and prevents private bundled
libraries from advertising themselves as system providers. Missing ABI generation
or leaked private providers causes the build to fail. No package is installed or
published by the builder.

The Package previews workflow now includes a Fedora 44 container job that builds,
installs, checks and removes the RPM. The workflow file has been parsed locally;
the new GitHub job itself has not yet run against a committed candidate.

## Local evidence

The following checks were performed on Fedora 44 KDE, using Python 3.14.8,
PySide6 6.12.0 and system mpv 0.41.0:

| Check | Result |
| --- | --- |
| Unit tests | 147 passed, 1 platform-specific skip |
| Ruff lint and format | Passed |
| Development dependency consistency (`pip check`) | Passed |
| Desktop-entry validation | Passed |
| Source archive and wheel build | Passed |
| All 11 pinned source archive downloads and hashes | Passed |
| Native frozen Wayland media/capture/subtitle/shutdown smoke | 17 checks passed |
| RPM construction, contents, system ABI/private-provider checks and digests | Passed |
| Fresh Fedora 44 container: DNF install, RPM verification, packaged smoke and removal | Passed, including 17 runtime checks |
| Offline wheel build and fresh installed-wheel desktop smoke | Passed, including 17 runtime checks |

The native Wayland check used the desktop's Mesa llvmpipe software renderer;
it is not evidence of successful hardware GPU rendering. A source renderer probe
also passed, including image and video captures, zoom, seek and resize. The user
reported successful source SMB dragging and playback, including recovery of an
initially blank video state; that transient state was not reproduced or diagnosed.

Local evidence is kept under ignored `artifacts/` paths:

- `fedora-rpm-final/report.json` and the matching build logs;
- `fedora-frozen-final/report.json` for the final Wayland bundle;
- `fedora-container-final/` for clean container install/removal and packaged smoke;
- `fedora-source-audit-final/corresponding-source/` for the 11 verified sources;
- `fedora-wheel-preview/report.json` for offline/fresh-environment validation.

Generated packages, inventories, logs and synthetic/private media are not committed.
The local candidate was built from the working tree, not an existing release tag.

## Codec, privacy and licence boundaries

The RPM does not contain libmpv, FFmpeg, Qt Multimedia, KIO or Samba. libmpv is a
system `mpv-libs` dependency; optional SMB drops call the installed KDE KIO FUSE
session service. Existing Qt Base/PySide6 licences cover QtDBus. No extra Python
runtime dependency, upload service, background scan or credential store is added.
KDE controls authentication, mounting and any local caching.

The development host decoded H.264 and VP9 samples but had no working HEVC decoder.
The clean container uses VP9/AAC/WAV fixtures so its result does not depend on
third-party codec repositories or claim H.264/HEVC support on every Fedora system.
Actual codec availability must be documented for each accepted target configuration.

The source/notice additions address observed redistributed components. Full source
archives and notices must accompany the final binaries as documented in
`SOURCE_DELIVERY.md`. An unsigned RPM still needs a published SHA-256 checksum.
The RPM's aggregate licence reference points to the original component terms;
it does not relicense dependencies or claim Fedora package collection approval.

Using Fedora's system decoders does not provide blanket codec-patent clearance.
The existing distribution/territory review in `LICENSING.md` still applies. This
engineering review does not replace a legal assessment of intended distribution.

## Before adding a published Fedora asset

1. Commit the reviewed changes and run Package previews for that exact revision.
   Inspect all three platform artifacts, inventories and matching source bundle.
2. Install the exact RPM on a clean Fedora 44 KDE desktop. Check terminal and
   desktop launch, Open With/default preservation, audible audio, images/GIF/TIFF/
   WebP, supported video/music, subtitles, seek/replay/repeat/speed, captures,
   fullscreen, multiple windows, scaling/monitor transitions and shutdown.
3. Check Dolphin SMB drops using the packaged QtDBus runtime, including credentials
   managed by KDE, unavailable service/share errors and a second selection while
   a mount request is pending. Do not expose addresses or credentials in errors.
4. Test RPM reinstall/upgrade and removal, including file associations, shared
   icon/desktop caches, preservation of unrelated applications' defaults and
   retention of user preferences/screenshots. The container proves headless
   install/removal only, not a desktop upgrade or GUI integration.
5. Repeat affected Windows and Mint package acceptance because this changes shared
   Python source, the Linux freezer and source/notice inputs. Do not carry over
   acceptance of the previous two-platform commit.
6. Complete final inventory/source/licence and codec-territory review, publish
   checksums, then add Fedora to the tag workflow's build/artifact completeness
   checks and website manifest mapping. Keep publication gated until then.

A separate Fedora package collection/COPR submission would need its own packaging
policy review; this upstream frozen preview is not represented as that submission.
