# Quick codec and software audit - 2026-10-18

The inspected development stack shows no obvious top-level licence incompatibility with AMP's AGPL-3.0-only source project. This is **not clearance to distribute a standalone binary bundle**. Exact transitive sources, notices and release packaging remain incomplete. This check covers local Windows package/build/licence evidence, not a vulnerability assessment, exhaustive dependency SBOM, legal opinion or codec-patent clearance.

## What was verified

| Component | Local evidence | Finding |
| --- | --- | --- |
| AMP source/wheels | AGPL-3.0-only metadata; four older local wheel copies inspected | No DLL, EXE or JAR inside those AMP wheels. Eight licence/notice files in each. They predate recent features and are not current release candidates. Dependency wheels are separate and can contain native code. |
| libmpv | `v0.41.0-dev-gfffe7a23a`; archive SHA-256 matches setup's pin | mpv reports `-Dgpl=false`. Embedded FFmpeg configuration lacks `--enable-gpl` and `--enable-nonfree`. This is build evidence, not a complete transitive licence audit. |
| FFmpeg inside libmpv | `git-2026-10-18-89d34d6`; embedded library licence strings | Libraries identify LGPL version 3 or later, matching `--enable-version3`. Earlier notes recording only the archive's LGPL 2.1 text were insufficient to describe this FFmpeg build. LGPLv3 and GPLv3 texts are already preserved in LICENSES. |
| Qt/PySide6 Essentials and shiboken6 | 6.12.0 distribution metadata | LGPLv3 is an available route. Exact Qt/plugin third-party notices and corresponding sources must accompany a distributed bundle as required. |
| Additional FFmpeg from Qt | Essentials includes `avcodec-63.dll`, other multimedia DLLs and the FFmpeg media plugin | Queried avcodec licence is LGPL 2.1 or later. Its configuration has neither GPL nor nonfree flags. AMP uses libmpv, not Qt Multimedia, but unused files still count if redistributed. |
| python-mpv | 1.0.8 metadata and preserved licence | GPLv2+ or LGPLv2.1+; the selected LGPL route remains plausible with this runtime. Retain exact notices and applicable terms. |
| PyOpenGL | 3.1.10, preserved upstream licence file | BSD-style and incorporated notices; retain the complete notice file. |
| Mutagen | 1.47.0 metadata, upstream documentation and preserved COPYING | GPL-2.0-or-later, not permissive/LGPL. The later-version option and GPLv3/AGPLv3 combination provisions support the current approach; retain Mutagen's own licence and corresponding source when required. |
| Test FFmpeg executable | imageio-ffmpeg 0.6.0 supplies FFmpeg 7.1 from gyan.dev | Executable configuration enables GPL, version3, x264 and x265. The Python wrapper's BSD licence does not describe the executable. It is development-only and absent from inspected AMP wheels; exclude it from an application bundle. |

`pip check` reports no broken installed requirements. libmpv advertises 516 decoder entries; this includes multiple implementations for some formats, not 516 separately audited codec products. H.264, HEVC, AV1, AAC, MP3 and FLAC implementations are present. Disabled x264/x265 *encoders* do not remove the H.264/HEVC *decoders* or settle patent questions. No additional playback codec was introduced by the recent UI, lyrics or artwork work.

## Before distributing a bundle

1. Fix the precise release file list. Exclude development tools/test media. The unpacked libmpv archive includes two unused libbluray Java JARs, headers and an import library; do not indiscriminately copy its whole folder into an installer. If any are included, audit them too.
2. Collect exact source revisions, patches, build recipes and complete notices for libmpv's statically linked stack, Qt's included libraries/image plugins and all other distributed components. Current FFmpeg configuration names many enabled third-party libraries; their individual versions and complete terms have not all been established here. The installed Essentials wheel also contains unused Qt PDF libraries/plugins. Do not infer that every bundled Qt module or its dependencies has identical licence options from the wheel's summary metadata; either exclude unused modules in a validated package or audit their exact terms too.
3. Cover LGPL source/replacement/relinking and attribution requirements for the actual bundle. Review visible library copyright notices as well as the legal files; the About page currently identifies AMP and points to dependency notices. Preserve AMP and Mutagen source/licence obligations. Include CPython's notices if embedding the interpreter.
4. Treat codec-patent assessment separately for intended distribution territories and features. A free application, LGPL build or operating-system decoder does not itself establish patent clearance.
5. Rebuild the current source/wheels and validate the chosen package on clean Windows and Linux. The older package evidence does not validate today's source as an installer. No visibility change, publication or release was performed.

The audited runtime DLL SHA-256 was `d8491ab850f73a892d3f3e765ef8aa6f43827223e7b508da430e2a35d630b342`; the archive SHA-256 was `9eda5c48918422bf28e211240b9010687f05e239c086d568aa86cc851a80fa6a`. The libmpv FFmpeg configuration/licence information was extracted from printable embedded strings because its FFmpeg functions are not exported; Qt avcodec data was queried through its exported functions.

Primary references checked: [FFmpeg licensing and configure options](https://ffmpeg.org/doxygen/trunk/md_LICENSE.html), [FFmpeg distribution guidance and patent discussion](https://ffmpeg.org/legal.html), [Qt 6.12 Multimedia notices](https://doc.qt.io/qt-6.12/qtmultimedia-index.html), [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [Mutagen licence](https://mutagen.readthedocs.io/en/latest/index.html), [GPLv3 section 13](https://www.gnu.org/licenses/gpl-3.0.en.html), [LGPLv3 section 4](https://www.gnu.org/licenses/lgpl-3.0.en.html).
