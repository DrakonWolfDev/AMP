"""Only enumerate the selected file's immediate directory."""

import re
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".mpg", ".mpeg"}
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES


def natural_key(path):
    name = Path(path).name
    parts = tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", name)
    )
    return parts, name.casefold(), name


def neighbours(current, direction):
    """Yield candidates in one direction, retaining a missing current file as anchor."""
    current = Path(current)
    entries = [
        entry
        for entry in current.parent.iterdir()
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    if current not in entries:
        entries.append(current)
    entries.sort(key=natural_key)
    index = entries.index(current)
    if direction > 0:
        yield from entries[index + 1 :]
    else:
        yield from reversed(entries[:index])
