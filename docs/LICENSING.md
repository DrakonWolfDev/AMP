# AMP licensing policy

AMP is licensed under **AGPL-3.0-only**. AMP first-party code is Copyright © 2026 Andrew Hodgson trading as Wolf Forge. Contributions are accepted under the same licence unless separately agreed; retain third-party attribution.

For distribution, provide recipients the licence, applicable notices and corresponding source using a method permitted by the licence. Do not impose additional restrictions contradicting their licensed rights. AMP currently has no remote-service interface; if a modified version later supports remote network interaction, review AGPL section 13's source-offer requirements.

## Dependency approach

- Keep dependencies under their original licences, recorded in THIRD_PARTY_NOTICES.md and preserved under LICENSES. The whole application licence does not relabel third-party code.
- Prefer the audited LGPL libmpv/FFmpeg route where practical. Check GPL versions/compatibility for system Linux packages rather than assuming every mpv/FFmpeg build is equivalent. Avoid non-redistributable/nonfree combinations in any distributed binary.
- Use distro-managed libmpv on Linux initially; validate the actual decoder set and exact build licence. AMP does not automatically use arbitrary GStreamer or OS codec plugins.
- On Windows, the current backend uses libmpv/FFmpeg, not Windows Media Foundation. OS codec extensions do not automatically become AMP decoder licences or capabilities.
- Software-licence compliance and codec-patent rights are separate. An open-source decoder or system package is not a universal patent grant. HEIC/HEVC and other patent-sensitive additions need a separate distribution assessment; no blanket patent clearance is claimed.

## Before a binary release (M9)

1. Pin the runtime and every included plugin/library, capture their actual licence/build metadata, and preserve their complete notices. Include CPython notices if embedding Python. Check Qt image-plugin transitive dependencies.
2. Preserve exact corresponding sources, build instructions/configuration and patches for copyleft components. Provide the required source delivery/offer with the binary and ensure dependency replacement/relinking rights are satisfied as applicable. A link to a moving upstream branch alone is not the release source archive.
3. Include AMP's AGPL licence, third-party licences/notices and visible legal information. The Python wheel/sdist includes the licence bundle; the app has Help → About AMP / licences. Verify a future frozen installer preserves the same material and source access.
4. Check selected GPL/LGPL versions and all dependencies for compatibility. Do not copy system codec DLLs into an installer merely because they are installed on the developer's machine.
5. Review codec-patent requirements for the intended territories/distribution, then test clean Windows/Mint installations. Record gaps rather than claiming that an LGPL-labelled DLL or an AGPL project automatically clears them.

This establishes the source-project licence and compliance workflow; a complete bundled-runtime audit remains unfinished. No public repository visibility change, binary release, tag or deployment is authorized by this work.

References: [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html), [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [mpv Copyright](https://github.com/mpv-player/mpv/blob/master/Copyright), [FFmpeg legal guidance](https://ffmpeg.org/legal.html).
