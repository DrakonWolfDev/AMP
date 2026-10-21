# AMP licensing policy

AMP is licensed under **AGPL-3.0-only**. AMP first-party code is Copyright © 2026 Andrew Hodgson trading as Wolf Forge. Contributions are accepted under the same licence unless separately agreed; retain third-party attribution.

For distribution, provide recipients the licence, applicable notices and corresponding source using a method permitted by the licence. Do not impose additional restrictions contradicting their licensed rights. AMP currently has no remote-service interface; if a modified version later supports remote network interaction, review AGPL section 13's source-offer requirements.

## Dependency approach

- Keep dependencies under their original licences, recorded in THIRD_PARTY_NOTICES.md and preserved under LICENSES. The whole application licence does not relabel third-party code.
- Check GPL versions/compatibility for system Linux packages rather than assuming every mpv/FFmpeg build is equivalent. Avoid non-redistributable/nonfree combinations in any distributed binary.
- Use distro-managed libmpv on Linux initially; validate the actual decoder set and exact build licence. AMP does not automatically use arbitrary GStreamer or OS codec plugins.
- On Windows, use Qt Multimedia's native Media Foundation backend. The bundle policy rejects libmpv, FFmpeg libraries and Qt's FFmpeg media plugin. Codec availability remains dependent on Windows and installed system extensions.
- Software-licence compliance and codec-patent rights are separate. An open-source decoder or system package is not a universal patent grant. HEIC/HEVC and other patent-sensitive additions need a separate distribution assessment; no blanket patent clearance is claimed.

## Before a binary release (M9)

1. Pin the runtime and every included plugin/library, capture their actual licence/build metadata, and preserve their complete notices. Include CPython notices if embedding Python. Check Qt image-plugin transitive dependencies.
2. Preserve exact corresponding sources, build instructions/configuration and patches for copyleft components. Provide the required source delivery/offer with the binary and ensure dependency replacement/relinking rights are satisfied as applicable. A link to a moving upstream branch alone is not the release source archive.
3. Include AMP's AGPL licence, third-party licences/notices and visible legal information. The Python wheel/sdist includes the licence bundle; the app has Help → About AMP / licences. Verify a future frozen installer preserves the same material and source access.
4. Check selected GPL/LGPL versions and all dependencies for compatibility. Do not copy system codec DLLs into an installer merely because they are installed on the developer's machine.
5. Review codec-patent requirements for the intended territories/distribution, then test clean Windows/Mint installations. Record gaps rather than claiming that an LGPL-labelled DLL or an AGPL project automatically clears them.

The 2026-10-20 frozen-bundle findings and remaining blockers are recorded in `CODEC_AUDIT.md`.
Pinned source inputs and the release-bundle procedure are recorded in
`legal/source-manifest.json` and `SOURCE_DELIVERY.md`. The builders preserve CPython/PyInstaller
notices and reject known unused media/PDF runtimes. The Qt Base, SVG, Wayland and Multimedia
source sets are pinned and mapped. A Windows package must still pass its inventory gate and
clean-machine Media Foundation playback tests before publication is approved.

References: [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html), [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [mpv Copyright](https://github.com/mpv-player/mpv/blob/master/Copyright), [FFmpeg legal guidance](https://ffmpeg.org/legal.html).

## Fedora and optional KDE SMB integration

Running a private source checkout on Fedora does not itself create a new binary
release or a requirement to publish that private checkout. See the
[GNU licensing FAQ](https://www.gnu.org/licenses/gpl-faq.html#NoDistributionRequirements).
Reading a user-selected SMB file is client access to a file server, not offering
AMP as a remote application service.

SMB drops optionally call the separately installed KDE KIO FUSE service over the
session D-Bus interface using the existing PySide6 QtDBus module. AMP does not
bundle KIO FUSE, KDE KIO, Samba, or additional codecs. No new Python dependency is
introduced. The interface is documented in the
[KIO FUSE usage guide](https://github.com/KDE/kio-fuse#usage).

Before distributing a Fedora RPM or frozen build, apply the existing release
audit to its actual included libraries and plugins, preserve notices and
corresponding source as required, and review the chosen libmpv/FFmpeg build and
codec-patent position. Do not assume a Fedora package or a third-party codec
repository provides blanket redistribution or patent clearance. Adding a Fedora
runtime setup guide does not establish that a Fedora binary release is audited.
