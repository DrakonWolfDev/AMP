# Qt 6.12 redistribution record

AMP uses the LGPLv3 option for the dynamically linked Qt/PySide components. The application
does not use a commercial Qt licence.

The inspected Windows and Linux bundle inventories map to these official Qt 6.12.0 source
modules:

- `qtbase`: Qt Core, GUI, Widgets, Network, DBus, OpenGL, platform, TLS and image plugins;
- `qtimageformats`: TIFF, WebP and other retained image-format plugins;
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

## Fedora inventory addition, 21 October 2026

The frozen Fedora preview retains QtDBus for optional KDE SMB resolution; this
is covered by the existing Qt Base / PySide6 source modules. The observed image
plugins also require Qt Image Formats 6.12.0, now pinned in the source manifest.
Its incorporated libtiff/libwebp attribution and licence inputs are preserved in
`LICENSES/Qt-ImageFormats-6.12.0-notices.txt`.

The Linux wheel runtime also contains ICU 73.2, verified with its version API.
Its official source and full release licence are now recorded in the source
manifest and `LICENSES/ICU-73.2.txt`. Repeat this inventory comparison if a wheel,
freezer hook or Qt version changes; these records do not approve unseen payloads.
