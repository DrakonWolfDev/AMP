# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Read local music tags and companion lyrics. Never resolve artwork URLs."""

import base64
import bisect
import re
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

import mutagen
from mutagen.flac import Picture
from PySide6.QtCore import QBuffer, QIODevice, QSize, Qt
from PySide6.QtGui import QImage, QImageReader

MAX_TEXT = 512 * 1024
MAX_ART = 16 * 1024 * 1024
STAMP = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")


@dataclass
class Lyrics:
    lines: list[str] = field(default_factory=list)
    times: list[float] = field(default_factory=list)

    def current(self, position):
        return bisect.bisect_right(self.times, position) - 1


@dataclass
class Music:
    title: str = ""
    artist: str = ""
    album: str = ""
    artwork: QImage = field(default_factory=QImage)
    lyrics: Lyrics = field(default_factory=Lyrics)


def parse_lyrics(text):
    text = text[:MAX_TEXT].lstrip("\ufeff")
    offsets = re.findall(r"\[offset:([+-]?\d{1,9})\]", text, re.IGNORECASE)
    offset = int(offsets[-1]) / 1000 if offsets else 0
    entries = []
    plain = []
    for line in text.splitlines():
        stamps = list(STAMP.finditer(line))
        if stamps:
            words = STAMP.sub("", line).strip()
            for stamp in stamps:
                minutes, seconds, fraction = stamp.groups()
                if int(seconds) < 60:
                    time = int(minutes) * 60 + int(seconds) + float("0." + (fraction or "0"))
                    entries.append((max(0, time + offset), words))
        elif not re.fullmatch(r"\s*\[[a-zA-Z]+:.*\]\s*", line):
            plain.append(line)
    if entries:
        entries.sort(key=lambda item: item[0])
        # Simultaneous translations/duets share the same highlighted block.
        times, lines = [], []
        for time, words in entries:
            if times and times[-1] == time:
                lines[-1] += "\n" + words
            else:
                times.append(time)
                lines.append(words)
        return Lyrics(lines, times)
    return Lyrics("\n".join(plain).strip().splitlines())


def companion_lyrics(path):
    for suffix in (".lrc", ".txt"):
        candidate = Path(path).with_suffix(suffix)
        try:
            with candidate.open("rb") as stream:
                data = stream.read(MAX_TEXT + 1)
            if len(data) > MAX_TEXT:
                continue
            encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            lyrics = parse_lyrics(data.decode(encoding))
            if lyrics.lines:
                return lyrics
        except (OSError, UnicodeError):
            continue
    return Lyrics()


def decode_artwork(data):
    if not data or len(data) > MAX_ART:
        return QImage()
    buffer = QBuffer()
    buffer.setData(bytes(data))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setAutoTransform(True)
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 32_000_000:
        return QImage()
    if max(size.width(), size.height()) > 1200:
        reader.setScaledSize(size.scaled(QSize(1200, 1200), Qt.AspectRatioMode.KeepAspectRatio))
    return reader.read()


def read_music(path):
    music = Music(title=Path(path).stem, lyrics=companion_lyrics(path))
    try:
        audio = mutagen.File(path)
        if audio is None:
            return music
        tags = audio.tags or {}

        def text(*keys):
            for key in keys:
                try:
                    value = tags.get(key)
                except (ValueError, KeyError):
                    continue  # Vorbis rejects the non-ASCII identifiers used by MP4.
                if value:
                    if hasattr(value, "text"):
                        value = value.text
                    if isinstance(value, (list, tuple)):
                        value = value[0]
                    return str(value)[:MAX_TEXT]
            return ""

        music.title = text("TIT2", "title", "\xa9nam", "Title") or music.title
        music.artist = text("TPE1", "artist", "\xa9ART", "Author")
        music.album = text("TALB", "album", "\xa9alb", "WM/AlbumTitle")
        if not music.lyrics.lines:
            embedded = text("lyrics", "unsyncedlyrics", "\xa9lyr", "WM/Lyrics")
            if not embedded and hasattr(tags, "getall"):
                frames = tags.getall("USLT")
                embedded = frames[0].text if frames else ""
            music.lyrics = parse_lyrics(embedded)
        pictures = list(getattr(audio, "pictures", []))
        if hasattr(tags, "getall"):
            pictures.extend(tags.getall("APIC"))
        for encoded in tags.get("metadata_block_picture", []):
            if len(encoded) <= MAX_ART * 4 // 3 + 8:
                with suppress(ValueError, mutagen.MutagenError):
                    pictures.append(Picture(base64.b64decode(encoded, validate=True)))
        pictures.sort(key=lambda picture: getattr(picture, "type", 0) != 3)
        candidates = [picture.data for picture in pictures if getattr(picture, "mime", "") != "-->"]
        candidates.extend(tags.get("covr", []))
        for data in candidates:
            music.artwork = decode_artwork(data)
            if not music.artwork.isNull():
                break
    except (mutagen.MutagenError, OSError, ValueError, TypeError, IndexError, OverflowError):
        pass  # Optional or damaged tags must never prevent local playback.
    return music
