"""Shared release-bundle content policy."""

from pathlib import Path


def forbidden_runtime_file(path):
    """Return whether *path* is an unused or development-only bundled runtime file."""
    path = Path(path)
    normalized = f"/{str(path).replace('\\', '/').casefold().lstrip('/')}"
    filename = path.name.casefold()
    return (
        path.suffix.casefold() == ".jar"
        or "/opengl/dlls/" in normalized
        or (filename.startswith("libmpv") and path.suffix.casefold() in {".dll", ".so"})
        or any(
            marker in filename
            for marker in (
                "ffmpeg-win",
                "qt6pdf",
                "qt6qml",
                "qt6quick",
                "qt6virtualkeyboard",
                "qtvirtualkeyboardplugin",
                "avcodec-",
                "avformat-",
                "avutil-",
                "libavcodec",
                "libavformat",
                "libavutil",
                "swresample-",
                "swscale-",
                "libswresample",
                "libswscale",
                "ffmpegmediaplugin",
            )
        )
    )
