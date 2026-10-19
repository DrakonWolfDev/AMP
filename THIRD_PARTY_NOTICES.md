# Third-party notices

AMP's own code is Copyright © 2026 Andrew Hodgson trading as Wolf Forge, licensed under **AGPL-3.0-only**; see LICENSE. Dependencies retain their own copyrights and licences. This inventory records the development runtime; it is not a completed audit of a binary installer.

## PySide6 Essentials / Qt and shiboken6 — 6.12.0

- Use: GUI, image reading, OpenGL widget and Python bindings.
- Upstream: https://code.qt.io/pyside/pyside-setup.git/ and https://code.qt.io/qt/qtbase.git/
- Installed wheel metadata offers `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. AMP uses the LGPLv3 route for these components. No commercial Qt licence is claimed.
- Copyright holders include The Qt Company Ltd. and other contributors; retain upstream copyright/third-party files for the exact packaged components.
- Licence texts: LICENSES/LGPL-3.0-only.txt and LICENSES/GPL-3.0-only.txt (the latter is incorporated by LGPLv3).
- Qt also incorporates separately licensed code such as image decoders. Before any binary bundle, collect the notices and matching source obligations for the actual Qt plugins/libraries included. Do not assume this summary replaces them.
- The installed Essentials wheel also contains unused Qt Multimedia/FFmpeg libraries. Its `avcodec-63.dll` reports LGPL version 2.1 or later and a configuration without `--enable-gpl` or `--enable-nonfree`. AMP does not import Qt Multimedia, but distributing the whole wheel includes these files; their full third-party notices and corresponding-source obligations still need covering. See docs/CODEC_AUDIT.md.
- References: https://doc.qt.io/qt-6/licensing.html and https://doc.qt.io/qt-6/licenses-used-in-qt.html

## python-mpv — 1.0.8

- Use: Python libmpv binding, including its maintained Render API bridge.
- Copyright (C) 2017–2024 Sebastian Götte.
- Source: https://github.com/jaseg/python-mpv
- Upstream offers GPLv2-or-later or LGPLv2.1-or-later, following the linked libmpv build. AMP's selected Windows runtime uses the LGPL route.
- Preserved installed licence: LICENSES/LGPL-2.1-or-later.txt.

## libmpv and its FFmpeg/dependency stack

- Use: local video/music decoding, playback and OpenGL rendering.
- Source: https://github.com/mpv-player/mpv and https://ffmpeg.org/
- Development build: `mpv v0.41.0-dev-gfffe7a23a`, official x86_64 Windows asset labelled LGPL. Exact asset/hash: docs/RENDERER_AND_PACKAGING.md.
- Archive licence preserved at LICENSES/libmpv-LICENSE.LGPL. It contains LGPL 2.1 terms. mpv and FFmpeg licences depend on build configuration and linked dependencies; the archive label alone does not settle the complete dependency inventory or patent rights.
- The 2026-10-18 audit found embedded FFmpeg library notices identifying **LGPL version 3 or later**, consistent with `--enable-version3`. The inspected configuration has no `--enable-gpl` or `--enable-nonfree`; x264/x265 encoders are disabled, while H.264/HEVC decoders remain present. Preserve LGPLv3/GPLv3 terms and the exact corresponding source, not only the archive's LGPL 2.1 file.
- Before distributing binaries: archive the exact corresponding source/configuration/patches and third-party notices; verify all linked components and satisfy their applicable source/replacement obligations.
- Linux system packages can have different build licences, including GPL builds. Audit the selected distribution packages as well; system installation does not erase compatibility obligations.

## PyOpenGL — 3.1.10

- Use: readback of the preserved Qt framebuffer.
- Source: https://github.com/mcfletch/pyopengl/tree/3.1.10
- BSD-style licences with additional incorporated-code notices. Full upstream release text: LICENSES/PyOpenGL-3.1.10.txt.
- Includes copyright notices for Michael C. Fletcher and contributors, earlier PyOpenGL contributors and other incorporated projects. Preserve the full notice rather than replacing it with a single SPDX label.
- If a future bundle includes its optional native DLLs/Tk components, retain their additional shipped notices too. AMP does not call GLUT, GLE or Tk.

## Mutagen — 1.47.0

- Use: read-only local music metadata, embedded lyrics and cover images. AMP does not call its tag-writing functions or resolve linked artwork.
- Source and documentation: https://github.com/quodlibet/mutagen and https://mutagen.readthedocs.io/en/latest/.
- Installed distribution licence: GPL-2.0-or-later. Full upstream licence is preserved at LICENSES/mutagen-1.47.0.txt; retain its notices and source obligations when distributing.

## Python and development tools

The Windows standalone build embeds CPython and the PyInstaller bootloader. Its build helper copies the interpreter's LICENSE.txt and PyInstaller's COPYING.txt (including its bootloader exception) into the bundle's LICENSES directory. PyInstaller and its hook/tool dependencies are build-time tools, not additional playback libraries. Inno Setup creates the Windows installer; its unmodified licence is preserved in LICENSES/InnoSetup-6.7.3.txt. See docs/RELEASE_READINESS.md for outstanding release obligations.

Pillow 13.0.0 is used only to generate synthetic image/EXIF test fixtures, not to decode images in AMP. Its installed metadata identifies MIT-CMU; the complete installed licence is preserved at LICENSES/Pillow-13.0.0.txt. Source: https://github.com/python-pillow/Pillow. Preserve its notices if distributing the development environment.

The current source installation uses the user's Python interpreter. A future installer embedding CPython must include its PSF licence and bundled third-party notices. pytest, Ruff, setuptools and imageio-ffmpeg are development/build dependencies, not application playback dependencies. Their source/wheel licence files must remain intact when distributed. The development FFmpeg fixture generator is not a licence-cleared AMP media runtime and must not accidentally enter a release bundle.

## Scope and provenance

The AGPL text is the standard upstream licence text. LGPL 2.1 texts are copied from the installed python-mpv wheel and downloaded libmpv archive. LGPLv3/GPLv3 texts are preserved from upstream Qt's LICENSES directory; PyOpenGL's full notice is from tag 3.1.10. See docs/LICENSING.md for the distribution policy and outstanding release work. No codec-patent clearance is asserted by choosing an open-source licence.
