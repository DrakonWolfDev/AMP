# Source delivery for binary releases

AMP binary releases must place their corresponding-source bundle beside the Windows and
Linux downloads. This is an engineering compliance record, not legal advice.

The bundle is generated from `legal/source-manifest.json`. It contains the licence and notice
set plus hash-verified upstream source archives for redistributed components.
`tools/source_compliance.py --check-ready` refuses release while an entry is unresolved;
`--download DIR` downloads and verifies pinned archives without overwriting an existing folder.
AMP's own release source is produced from the same tagged commit by the release workflow.

The source bundle must identify the same AMP tag and commit as the binaries. Keep it available
for at least as long as the corresponding binaries, with its checksum in `SHA256SUMS.txt`.
Recipients may replace the dynamically loaded LGPL Qt libraries. Windows playback calls Media
Foundation through Qt Multimedia and does not redistribute libmpv or FFmpeg. Build instructions are in
`PACKAGING.md` and `RENDERER_AND_PACKAGING.md`.

## Current position

The Python dependency, PySide6/shiboken6, Qt Base, Qt SVG, Qt Image Formats, Qt Multimedia, Qt Wayland and ICU source archives are
pinned by official URL and SHA-256. `QT_REDISTRIBUTION.md` maps the Qt archives to the observed
bundle inventory. The Windows inventory gate rejects libmpv, FFmpeg libraries and Qt's FFmpeg
media plugin, leaving the native Windows media plugin as the only packaged playback backend.

Linux obtains libmpv and its codec stack from the distribution rather than from AMP's `.deb` or Fedora `.rpm`.
The rebuilt Windows artifact still requires inventory inspection and clean-machine playback tests.

Version 0.8b is intentionally unsigned. Release notes and the download page must say this
plainly and publish SHA-256 checksums; signing is not represented as a remaining gate for this
version.
