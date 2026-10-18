# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Core commands run on one worker; Render API calls belong to the Qt GL thread."""

import importlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

from PySide6.QtCore import QObject, Signal


def load_binding():
    if os.name == "nt":
        directory = os.environ.get("AMP_MPV_DIR")
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.binding = load_binding()
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="amp-mpv")
        self.closed = False
        self._entry_tokens = {}
        self._entry_lock = Lock()
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
                    ytdl=False,
                    load_scripts=False,
                    access_references=False,
                    autoload_files=False,
                    demuxer_lavf_o="protocol_whitelist=file",
                    osd_level=0,
                )
            ).result()
            self.version = self.worker.submit(self.player._get_property, "mpv-version").result()
            for name in (
                "time-pos",
                "duration",
                "pause",
                "volume",
                "mute",
                "video-out-params",
                "idle-active",
            ):
                self.worker.submit(self.player.observe_property, name, self._observed).result()
            self.player.event_callback("end-file")(self._ended)
        except Exception:
            if hasattr(self, "player"):
                self.worker.submit(self.player.terminate).result(timeout=15)
            self.worker.shutdown(wait=True)
            raise

    def _observed(self, name, value):
        if not self.closed:
            self.changed.emit(name, value)

    def _ended(self, event):
        if not self.closed and event.data.reason == self.binding.MpvEventEndFile.ERROR:
            with self._entry_lock:
                token = self._entry_tokens.pop(event.data.playlist_entry_id, None)
            if token is not None and not self.closed:
                self.load_failed.emit(token, "This media could not be decoded.")

    def load(self, path, token):
        def perform():
            # loadfile returns before decoding finishes. Map the new playlist
            # entry, not a mutable current filename, to the caller's request.
            # The lock also covers errors arriving before the mapping is ready.
            with self._entry_lock:
                self.player.command("loadfile", str(path), "replace")
                for entry in self.player._get_property("playlist"):
                    self._entry_tokens[entry["id"]] = token
                while len(self._entry_tokens) > 64:
                    self._entry_tokens.pop(next(iter(self._entry_tokens)))

        self.submit(perform)

    def submit(self, fn, *args):
        if self.closed:
            return
        future = self.worker.submit(fn, *args)

        def completed(result):
            try:
                result.result()
            except (RuntimeError, OSError, ValueError, AttributeError):
                if not self.closed:
                    self.failed.emit("Media operation failed. Try reopening the file.")

        future.add_done_callback(completed)

    def command(self, *args):
        self.submit(self.player.command, *args)

    def set(self, name, value):
        self.submit(self.player._set_property, name, value)

    def shutdown(self):
        self.closed = True
        self.worker.submit(self.player.terminate).result(timeout=15)
        self.worker.shutdown(wait=True)
