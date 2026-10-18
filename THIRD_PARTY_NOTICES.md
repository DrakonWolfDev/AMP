# Third-party notices

AMP's own code is Copyright © 2026 Andrew Hodgson trading as Wolf Forge, licensed under **AGPL-3.0-only**; see LICENSE. Dependencies retain their own copyrights and licences. This inventory records the development runtime; it is not a completed audit of a binary installer.

## PySide6 Essentials / Qt and shiboken6 — 6.12.0

- Use: GUI, image reading, OpenGL widget and Python bindings.
- Upstream: https://code.qt.io/pyside/pyside-setup.git/ and https://code.qt.io/qt/qtbase.git/
- Installed wheel metadata offers `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. AMP uses the LGPLv3 route for these components. No commercial Qt licence is claimed.
- Copyright holders include The Qt Company Ltd. and other contributors; retain upstream copyright/third-party files for the exact packaged components.
- Licence texts: LICENSES/LGPL-3.0-only.txt and LICENSES/GPL-3.0-only.txt (the latter is incorporated by LGPLv3).
- Qt also incorporates separately licensed code such as image decoders. Before any binary bundle, collect the notices and matching source obligations for the actual Qt plugins/libraries included. Do not assume this summary replaces them.
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
- Before distributing binaries: archive the exact corresponding source/configuration/patches and third-party notices; verify all linked components and satisfy their applicable source/replacement obligations.
- Linux system packages can have different build licences, including GPL builds. Audit the selected distribution packages as well; system installation does not erase compatibility obligations.

## PyOpenGL — 3.1.10

- Use: readback of the preserved Qt framebuffer.
- Source: https://github.com/mcfletch/pyopengl/tree/3.1.10
- BSD-style licences with additional incorporated-code notices. Full upstream release text: LICENSES/PyOpenGL-3.1.10.txt.
- Includes copyright notices for Michael C. Fletcher and contributors, earlier PyOpenGL contributors and other incorporated projects. Preserve the full notice rather than replacing it with a single SPDX label.
- If a future bundle includes its optional native DLLs/Tk components, retain their additional shipped notices too. AMP does not call GLUT, GLE or Tk.

## Python and development tools

The current source installation uses the user's Python interpreter. A future installer embedding CPython must include its PSF licence and bundled third-party notices. pytest, Ruff, setuptools and imageio-ffmpeg are development/build dependencies, not application playback dependencies. Their source/wheel licence files must remain intact when distributed. The development FFmpeg fixture generator is not a licence-cleared AMP media runtime and must not accidentally enter a release bundle.

## Scope and provenance

The AGPL text is copied verbatim from the user's existing WolfLauncher LICENSE. LGPL 2.1 texts are copied from the installed python-mpv wheel and downloaded libmpv archive. LGPLv3/GPLv3 texts are preserved from upstream Qt's LICENSES directory; PyOpenGL's full notice is from tag 3.1.10. See docs/LICENSING.md for the distribution policy and outstanding release work. No codec-patent clearance is asserted by choosing an open-source licence.
