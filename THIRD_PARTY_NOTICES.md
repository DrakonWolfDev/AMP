# Third-party notices

AMP's own code is Copyright © 2026 Andrew Hodgson trading as Wolf Forge, licensed under **AGPL-3.0-only**; see LICENSE. Dependencies retain their own copyrights and licences. This inventory records the development runtime; it is not a completed audit of a binary installer.

## PySide6 Essentials/Addons, Qt and shiboken6 — 6.12.0

- Use: GUI, image reading, OpenGL widget, Windows Media Foundation integration and Python bindings.
- Upstream: https://code.qt.io/pyside/pyside-setup.git/ and https://code.qt.io/qt/qtbase.git/
- Installed wheel metadata offers `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. AMP uses the LGPLv3 route for these components. No commercial Qt licence is claimed.
- Copyright holders include The Qt Company Ltd. and other contributors; retain upstream copyright/third-party files for the exact packaged components.
- Licence texts: LICENSES/LGPL-3.0-only.txt and LICENSES/GPL-3.0-only.txt (the latter is incorporated by LGPLv3).
- Qt also incorporates separately licensed code such as image decoders. The official Qt Base,
  Qt SVG, Qt Multimedia and Qt Wayland 6.12.0 source archives are pinned for the
  bundle; they retain their complete `LICENSES`, REUSE and attribution inputs. See
  docs/QT_REDISTRIBUTION.md. Do not assume this summary replaces those materials.
- Windows retains Qt Multimedia and its native Windows plugin, while rejecting Qt's FFmpeg plugin
  and FFmpeg DLLs. Linux excludes Qt Multimedia entirely. A changed wheel or bundle inventory
  requires the Qt source/notice mapping to be repeated. See docs/CODEC_AUDIT.md.
- References: https://doc.qt.io/qt-6/licensing.html and https://doc.qt.io/qt-6/licenses-used-in-qt.html

## python-mpv — 1.0.8

- Use: Linux Python libmpv binding, including its maintained Render API bridge.
- Copyright (C) 2017–2024 Sebastian Götte.
- Source: https://github.com/jaseg/python-mpv
- Upstream offers GPLv2-or-later or LGPLv2.1-or-later, following the linked Linux libmpv build.
- Preserved installed licence: LICENSES/LGPL-2.1-or-later.txt.

## Linux system libmpv and its FFmpeg/dependency stack

- Use: local video/music decoding, playback and OpenGL rendering.
- Source: https://github.com/mpv-player/mpv and https://ffmpeg.org/
- AMP's Debian package declares `libmpv2` as a system dependency and does not copy libmpv or
  FFmpeg into its archive. Linux system packages can have different build licences, including GPL
  builds; system installation does not erase compatibility obligations.
- Windows does not install or load libmpv. It uses the operating system's Media Foundation codecs
  through Qt's native plugin.

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

The Linux and Windows standalone builds embed CPython and the PyInstaller bootloader. Both build helpers copy the interpreter's LICENSE.txt and PyInstaller's COPYING.txt (including its bootloader exception) into the bundle's LICENSES directory. PyInstaller and its hook/tool dependencies are build-time tools, not additional playback libraries. Inno Setup creates the Windows installer; its unmodified licence is preserved in LICENSES/InnoSetup-6.7.3.txt. See docs/RELEASE_READINESS.md for outstanding release obligations.

Pillow 13.0.0 is used only to generate synthetic image/EXIF test fixtures, not to decode images in AMP. Its installed metadata identifies MIT-CMU; the complete installed licence is preserved at LICENSES/Pillow-13.0.0.txt. Source: https://github.com/python-pillow/Pillow. Preserve its notices if distributing the development environment.

The source installation uses the user's Python interpreter; standalone packages embed CPython and must retain its PSF licence and incorporated-software notices. pytest, Ruff, setuptools and imageio-ffmpeg are development/build dependencies, not application playback dependencies. Their source/wheel licence files must remain intact when distributing a development environment. The development FFmpeg fixture generator is not an AMP media runtime and is rejected from application bundles.

## Scope and provenance

The AGPL text is the standard upstream licence text. LGPL 2.1 terms are retained for the Linux
python-mpv path. LGPLv3/GPLv3 texts are preserved from upstream Qt's LICENSES directory;
PyOpenGL's full notice is from tag 3.1.10. See docs/LICENSING.md for the distribution policy and
outstanding release work. No codec-patent clearance is asserted by choosing an open-source licence
or calling an operating-system decoder.
