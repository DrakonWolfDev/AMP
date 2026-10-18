"""Only enumerate the selected file's immediate directory."""

import re
from dataclasses import dataclass
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".mpg", ".mpeg"}
AUDIO_SUFFIXES = {".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".wma", ".aiff", ".aif"}
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES | AUDIO_SUFFIXES


@dataclass(frozen=True)
class NavigationStep:
    path: Path
    wrapped: bool


def natural_key(path):
    name = Path(path).name
    parts = tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", name)
    )
    return parts, name.casefold(), name


def neighbours(current, direction):
    """Yield each other supported file at most once, wrapping at the boundary."""
    for step in navigation_steps(current, direction):
        yield step.path


def navigation_steps(current, direction):
    """Retain a deleted current file as anchor and report a crossed boundary."""
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
    increment = 1 if direction > 0 else -1
    for distance in range(1, len(entries)):
        raw_index = index + increment * distance
        yield NavigationStep(
            entries[raw_index % len(entries)], raw_index < 0 or raw_index >= len(entries)
        )
