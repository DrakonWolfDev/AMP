# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Small, local-only SubRip parser and time-indexed subtitle track."""

import html
import re
from bisect import bisect_right
from dataclasses import dataclass

_TIMING = re.compile(
    r"^\s*(\d+):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})(?:\s+.*)?$"
)
_TAG = re.compile(r"<[^>\r\n]*>")


@dataclass(frozen=True)
class SubtitleCue:
    start: float
    end: float
    text: str


def _seconds(groups):
    hours, minutes, seconds, milliseconds = (int(value) for value in groups)
    return hours * 3600 + minutes * 60 + seconds + milliseconds / (10 ** len(groups[3]))


def _plain_text(lines):
    # SubRip permits a small HTML-like formatting subset. AMP intentionally
    # renders plain text, decoding entities but never interpreting markup.
    return "\n".join(html.unescape(_TAG.sub("", line)).strip() for line in lines).strip()


def parse_srt_text(value):
    """Parse valid cues from SubRip text, tolerating malformed unrelated blocks."""
    cues = []
    blocks = re.split(r"\r?\n\s*\r?\n", value.replace("\ufeff", "").strip())
    for block in blocks:
        lines = block.splitlines()
        timing_index = next((i for i, line in enumerate(lines[:2]) if "-->" in line), None)
        if timing_index is None:
            continue
        match = _TIMING.match(lines[timing_index])
        if not match:
            continue
        start = _seconds(match.groups()[:4])
        end = _seconds(match.groups()[4:])
        text = _plain_text(lines[timing_index + 1 :])
        if text and end > start:
            cues.append(SubtitleCue(start, end, text))
    return sorted(cues, key=lambda cue: (cue.start, cue.end))


def read_srt(path):
    """Read a local SRT using BOM-aware Unicode with a conservative fallback."""
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16")
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252")
    return SubtitleTrack(parse_srt_text(text))


class SubtitleTrack:
    """A cue track compiled into event snapshots for O(log n) lookup."""

    def __init__(self, cues=()):
        events = {}
        for order, cue in enumerate(cues):
            events.setdefault(cue.start, []).append((True, order, cue.text))
            events.setdefault(cue.end, []).append((False, order, cue.text))

        active = {}
        self.times = []
        self.texts = []
        for when in sorted(events):
            # End times are exclusive; remove ending cues before adding cues
            # that start at the same timestamp.
            changes = sorted(events[when], key=lambda item: item[0])
            for starting, order, text in changes:
                if starting:
                    active[order] = text
                else:
                    active.pop(order, None)
            self.times.append(when)
            self.texts.append("\n".join(active[key] for key in sorted(active)))

    def __bool__(self):
        return bool(self.times)

    def text_at(self, seconds):
        index = bisect_right(self.times, max(0, seconds or 0)) - 1
        return self.texts[index] if index >= 0 else ""
