from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parents[1]
data = [
    (str(root / "LICENSE"), "."),
    (str(root / "THIRD_PARTY_NOTICES.md"), "."),
    (str(root / "LICENSES"), "LICENSES"),
    (str(root / "amp/assets"), "amp/assets"),
]
for name in (
    "andy-media-player",
    "PySide6-Essentials",
    "shiboken6",
    "python-mpv",
    "PyOpenGL",
    "mutagen",
    "packaging",
):
    data += copy_metadata(name)

a = Analysis(
    [str(root / "packaging/linux/entry.py")],
    pathex=[str(root)],
    datas=data,
    hiddenimports=["mpv", "OpenGL.platform.glx"],
    excludes=[
        "PySide6.QtMultimedia",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PIL",
        "imageio_ffmpeg",
        "numpy",
        "pytest",
        "tkinter",
    ],
)
# Keep libmpv and its codec/dependency stack distro-managed. PyInstaller may
# otherwise follow python-mpv's ctypes lookup into /usr/lib and copy the host's
# native multimedia libraries into the application bundle.
a.exclude_system_libraries()
# PyOpenGL ships legacy Windows GLUT/GLE DLLs as package data. AMP only uses
# OpenGL.glReadPixels and must not carry those unrelated binaries on any target.
for name in ("binaries", "datas"):
    setattr(
        a,
        name,
        [
            item
            for item in getattr(a, name)
            if "opengl/dlls/" not in item[0].replace("\\", "/").lower()
        ],
    )
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AMP",
    console=False,
    debug=False,
    upx=False,
    icon=str(root / "amp/assets/amp.png"),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="AMP")
