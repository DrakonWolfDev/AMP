# Qt 6.12 redistribution record

AMP uses the LGPLv3 option for the dynamically linked Qt/PySide components. The application
does not use a commercial Qt licence.

The inspected Windows and Linux bundle inventories map to these official Qt 6.12.0 source
modules:

- `qtbase`: Qt Core, GUI, Widgets, Network, OpenGL, platform, TLS and image plugins;
- `qtsvg`: SVG libraries, icon engine and image-format plugin;
- `qtmultimedia`: Qt Multimedia and the native Windows Media Foundation plugin; and
- `qtwayland`: Wayland client libraries and plugins in the Linux package.

The bundle gate excludes the unused Qt virtual-keyboard input plugin and its QML/Quick
dependencies. AMP uses Qt Widgets and its native platform text input; these additional modules
are outside the retained runtime/source set and must not reappear through hook collection.

Their official source archives and SHA-256 hashes are pinned in
`legal/source-manifest.json`. The downloads are hash-pinned from Qt's official release metadata. The source
archives retain their `LICENSES`, `REUSE.toml` and `qt_attribution.json` material, including the
third-party code incorporated by the relevant modules. PySide6 and shiboken6 share the separately
pinned `pyside-setup-everywhere-src-6.12.0.tar.xz` archive.

The release workflow places these archives, AMP's licence set, third-party notices and the exact
AMP tagged source in one corresponding-source download beside the binaries. Qt is shipped as
separate shared libraries; recipients can replace those libraries subject to ABI compatibility.
AMP imposes no technical restriction preventing that replacement.

This record covers the source and notice inputs for the Qt files observed in the inspected AMP
bundles. A future change to PySide6, Qt version, PyInstaller collection, or the retained plugin
set requires a new inventory comparison and updated hashes before release.
