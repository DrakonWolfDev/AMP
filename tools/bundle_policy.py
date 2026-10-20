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
        or any(
            marker in filename
            for marker in (
                "ffmpeg-win",
                "qt6pdf",
                "qt6multimedia",
                "avcodec-",
                "avformat-",
                "libavcodec",
                "libavformat",
                "ffmpegmediaplugin",
            )
        )
    )
