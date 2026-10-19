# Windows one-folder application bundle.
import os
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parents[1]
runtime = Path(os.environ["AMP_MPV_DIR"])
data = [(str(root / "LICENSE"), "."), (str(root / "THIRD_PARTY_NOTICES.md"), "."), (str(root / "LICENSES"), "LICENSES")]
data += [(str(root / "amp/assets"), "amp/assets")]
for name in ("andy-media-player", "PySide6-Essentials", "shiboken6", "python-mpv", "PyOpenGL", "mutagen", "packaging"):
    data += copy_metadata(name)

a = Analysis(
    [str(root / "packaging/windows/entry.py")],
    pathex=[str(root)],
    binaries=[(str(runtime / "libmpv-2.dll"), "amp_runtime")],
    datas=data,
    hiddenimports=["mpv", "OpenGL.platform.win32"],
    excludes=["PySide6.QtMultimedia", "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtQml", "PySide6.QtQuick", "tkinter", "PIL", "pytest", "imageio_ffmpeg", "numpy"],
)
# Qt's GUI hook collects every image plugin, including unused PDF support.
# Exclude its plugin and dependencies: AMP has no PDF or Qt Multimedia feature.
for name in ("binaries", "datas"):
    setattr(a, name, [item for item in getattr(a, name) if not any(part in item[0].lower() for part in ("qpdf", "qt6pdf", "avcodec-", "avformat-", "avutil-", "swresample-", "swscale-", "ffmpegmediaplugin"))])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="AMP", console=False, debug=False, upx=False, icon=str(root / "amp/assets/amp.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="AMP")
