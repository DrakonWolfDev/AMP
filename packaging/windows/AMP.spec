# Windows one-folder application bundle.
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parents[1]
data = [(str(root / "LICENSE"), "."), (str(root / "THIRD_PARTY_NOTICES.md"), "."), (str(root / "LICENSES"), "LICENSES")]
data += [(str(root / "amp/assets"), "amp/assets")]
data += [(str(root / "docs" / name), "docs") for name in ("PRIVACY.md", "CODEC_AUDIT.md")]
for name in ("andy-media-player", "PySide6-Essentials", "PySide6-Addons", "shiboken6", "PyOpenGL", "mutagen", "packaging"):
    data += copy_metadata(name)

a = Analysis(
    [str(root / "packaging/windows/entry.py")],
    pathex=[str(root)],
    binaries=[],
    datas=data,
    hiddenimports=["PySide6.QtMultimedia", "OpenGL.platform.win32"],
    excludes=["mpv", "PySide6.QtMultimediaWidgets", "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtQml", "PySide6.QtQuick", "tkinter", "PIL", "pytest", "imageio_ffmpeg", "numpy"],
)
# Qt's GUI hook collects every image plugin, including unused PDF support, and
# PyOpenGL collects legacy GLUT/GLE DLLs which AMP does not call. Exclude those
# payloads and their dependencies.
for name in ("binaries", "datas"):
    setattr(a, name, [item for item in getattr(a, name) if not any(part in item[0].replace("\\", "/").lower() for part in ("qpdf", "qt6pdf", "avcodec-", "avformat-", "avutil-", "swresample-", "swscale-", "ffmpegmediaplugin", "opengl/dlls/"))])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="AMP", console=False, debug=False, upx=False, icon=str(root / "amp/assets/amp.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="AMP")
