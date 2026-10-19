# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Core commands run on one worker; Render API calls belong to the Qt GL thread."""

import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

from PySide6.QtCore import QObject, Signal

from .music import read_music
from .playback import seek_target


def companion_subtitles(path):
    """Return same-folder SRT files belonging to a video, exact name first."""
    path = Path(path)
    prefix = f"{path.stem}.".casefold()
    try:
        matches = [
            candidate
            for candidate in path.parent.iterdir()
            if candidate.is_file()
            and candidate.suffix.casefold() == ".srt"
            and candidate.name.casefold().startswith(prefix)
        ]
    except OSError:
        return []
    exact = f"{path.stem}.srt".casefold()
    return sorted(
        matches,
        key=lambda candidate: (candidate.name.casefold() != exact, candidate.name.casefold()),
    )


def load_binding():
    if os.name == "nt":
        directory = os.environ.get("AMP_MPV_DIR")
        if not directory and getattr(sys, "frozen", False):
            directory = str(Path(sys._MEIPASS) / "amp_runtime")
        if directory:
            directory = str(Path(directory).resolve())
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
    try:
        return importlib.import_module("mpv")
    except (ImportError, OSError) as error:
        raise RuntimeError(
            "Music and video need libmpv. On Windows set AMP_MPV_DIR to the folder containing "
            "libmpv-2.dll; on Linux install libmpv (for Mint: sudo apt install libmpv2). "
            "Images still work without it."
        ) from error


class MpvBackend(QObject):
    changed = Signal(str, object)
    failed = Signal(str)
    load_failed = Signal(int, str)
    load_ready = Signal(int, object)
    music_ready = Signal(int, object)
    observed_properties = (
        "time-pos",
        "duration",
        "pause",
        "volume",
        "mute",
        "speed",
        "video-out-params",
        "idle-active",
        "eof-reached",
        "seekable",
        "track-list",
        "sub-visibility",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.binding = load_binding()
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="amp-mpv")
        self.closed = False
        self._entry_tokens = {}
        self._entry_lock = Lock()
        self._active_entry = None
        try:
            self.player = self.worker.submit(
                lambda: self.binding.MPV(
                    vo="libmpv",
                    hwdec="no",
                    config=False,
                    osc=False,
                    input_default_bindings=False,
                    input_vo_keyboard=False,
                    terminal=False,
                    idle=True,
                    keep_open=True,
                    gapless_audio="no",
                    ytdl=False,
                    load_scripts=False,
                    access_references=False,
                    autoload_files=False,
                    demuxer_lavf_o="protocol_whitelist=file",
                    osd_level=0,
                )
            ).result()
            self.version = self.worker.submit(self.player._get_property, "mpv-version").result()
            for name in self.observed_properties:
                self.worker.submit(self.player.observe_property, name, self._observed).result()
            self.player.event_callback("end-file")(self._ended)
            self.player.event_callback("start-file")(self._started)
            self.player.event_callback("file-loaded")(self._loaded)
        except Exception:
            if hasattr(self, "player"):
                self.worker.submit(self.player.terminate).result(timeout=15)
            self.worker.shutdown(wait=True)
            raise

    def _observed(self, name, value):
        if not self.closed:
            self.changed.emit(name, value)

    def _started(self, event):
        self._active_entry = event.data.playlist_entry_id

    def _loaded(self, _event):
        with self._entry_lock:
            token = self._entry_tokens.get(self._active_entry)
        if token is None or self.closed:
            return

        def refresh():
            values = {}
            for name in self.observed_properties:
                try:
                    values[name] = self.player._get_property(name)
                except AttributeError:
                    values[name] = None
            if not self.closed:
                self.load_ready.emit(token, values)

        self.submit(refresh)

    def _ended(self, event):
        if not self.closed and event.data.reason == self.binding.MpvEventEndFile.ERROR:
            with self._entry_lock:
                token = self._entry_tokens.pop(event.data.playlist_entry_id, None)
            if token is not None and not self.closed:
                self.load_failed.emit(token, "This media could not be decoded.")

    def load(self, path, token, *, subtitles=()):
        def perform():
            # loadfile returns before decoding finishes. Map the new playlist
            # entry, not a mutable current filename, to the caller's request.
            # The lock also covers errors arriving before the mapping is ready.
            with self._entry_lock:
                self.player.command("loadfile", str(path), "replace")
                for index, subtitle in enumerate(subtitles):
                    self.player.command(
                        "sub-add", str(subtitle), "select" if index == 0 else "auto"
                    )
                # Subtitle tracks remain attached and selectable, but every
                # newly opened video starts with captions hidden.
                self.player._set_property("sub-visibility", False)
                for entry in self.player._get_property("playlist"):
                    self._entry_tokens[entry["id"]] = token
                while len(self._entry_tokens) > 64:
                    self._entry_tokens.pop(next(iter(self._entry_tokens)))

        self.submit(perform)

    def submit(self, fn, *args):
        if self.closed:
            return
        # Already queued slider/seek/load commands become no-ops on shutdown,
        # so a busy UI cannot keep audio alive behind a long command backlog.
        future = self.worker.submit(lambda: fn(*args) if not self.closed else None)

        def completed(result):
            try:
                result.result()
            except (RuntimeError, OSError, ValueError, AttributeError, TypeError, SystemError):
                if not self.closed:
                    self.failed.emit("Media operation failed. Try reopening the file.")

        future.add_done_callback(completed)

    def command(self, *args):
        self.submit(self.player.command, *args)

    def read_music(self, path, token):
        def read():
            music = read_music(path)
            if not self.closed:
                self.music_ready.emit(token, music)

        self.submit(read)

    def refresh_video(self, token):
        def read():
            try:
                value = self.player._get_property("video-out-params")
            except AttributeError:
                value = None
            if not self.closed:
                self.load_ready.emit(token, {"video-out-params": value})

        self.submit(read)

    def toggle_playback(self):
        def perform():
            if self.player._get_property("eof-reached"):
                self.player.command("seek", 0, "absolute+exact")
                self.player._set_property("pause", False)
            else:
                self.player.command("cycle", "pause")

        self.submit(perform)

    def seek(self, seconds, mode):
        def perform():
            if not self.player._get_property("seekable"):
                return
            target = seek_target(
                seconds,
                mode,
                self.player._get_property("time-pos"),
                self.player._get_property("duration"),
            )
            if target is not None:
                self.player.command("seek", target, "absolute+exact")

        self.submit(perform)

    def set(self, name, value):
        self.submit(self.player._set_property, name, value)

    def shutdown(self):
        self.closed = True
        self.worker.submit(self.player.terminate).result(timeout=15)
        self.worker.shutdown(wait=True)
