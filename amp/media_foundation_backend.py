# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Windows playback through Qt's native Media Foundation backend."""

import os

from PySide6.QtCore import QObject, Qt, QUrl, Signal, Slot

# Select the native Windows backend before the first multimedia object is made.
# The Windows bundle deliberately excludes Qt's FFmpeg plugin and libraries.
os.environ.setdefault("QT_MEDIA_BACKEND", "windows")

from PySide6.QtMultimedia import (  # noqa: E402
    QAudioOutput,
    QMediaPlayer,
    QVideoSink,
)

from .music import read_music
from .playback import seek_target


class MediaFoundationBackend(QObject):
    """Present Media Foundation using the property vocabulary expected by AMP."""

    changed = Signal(str, object)
    failed = Signal(str)
    load_failed = Signal(int, str)
    load_ready = Signal(int, object)
    music_ready = Signal(int, object)
    playback_ended = Signal(int)
    _end_pending = Signal(int)
    frame_ready = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.video_sink = QVideoSink(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoSink(self.video_sink)
        self.closed = False
        self.token = 0
        self.version = "Windows Media Foundation"
        self._mute = False
        self._end_pending.connect(self._finish_playback, Qt.ConnectionType.QueuedConnection)

        self.player.positionChanged.connect(
            lambda value: self.changed.emit("time-pos", value / 1000)
        )
        self.player.durationChanged.connect(
            lambda value: self.changed.emit("duration", value / 1000)
        )
        self.player.seekableChanged.connect(lambda value: self.changed.emit("seekable", value))
        self.player.playbackRateChanged.connect(lambda value: self.changed.emit("speed", value))
        self.player.playbackStateChanged.connect(self._state_changed)
        self.player.mediaStatusChanged.connect(self._status_changed)
        self.player.errorOccurred.connect(self._error)
        self.video_sink.videoFrameChanged.connect(self._frame_changed)

    def _state_changed(self, state):
        self.changed.emit("pause", state != QMediaPlayer.PlaybackState.PlayingState)

    def _status_changed(self, status):
        if self.closed:
            return
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.load_ready.emit(
                self.token,
                {
                    "duration": self.player.duration() / 1000,
                    "pause": self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState,
                    "volume": round(self.audio_output.volume() * 100),
                    "mute": self._mute,
                    "speed": self.player.playbackRate(),
                    "seekable": self.player.isSeekable(),
                    "track-list": [],
                    "sub-visibility": False,
                },
            )
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Qt's Windows backend emits this status before setting StoppedState.
            # Loading the next source here lets that trailing stop affect it.
            self._end_pending.emit(self.token)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.load_failed.emit(self.token, "This media could not be decoded by Windows.")

    @Slot(int)
    def _finish_playback(self, token):
        if (
            not self.closed
            and token == self.token
            and self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia
        ):
            self.changed.emit("eof-reached", True)
            self.playback_ended.emit(token)

    def _error(self, _error, message):
        if not self.closed:
            self.load_failed.emit(
                self.token, message or "This media could not be decoded by Windows."
            )

    def _frame_changed(self, frame):
        if self.closed or not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        image.setDevicePixelRatio(1)
        self.frame_ready.emit(image)
        size = frame.surfaceFormat().viewport().size()
        if size.isEmpty():
            size = frame.size()
        self.load_ready.emit(
            self.token, {"video-out-params": {"dw": size.width(), "dh": size.height()}}
        )

    def load(self, path, token, *, subtitles=()):
        # External SRT is parsed and painted by AMP above the decoder backend.
        del subtitles
        self.token = token
        self.changed.emit("eof-reached", False)
        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.player.play()

    def read_music(self, path, token):
        try:
            music = read_music(path)
        except (OSError, ValueError):
            return
        if not self.closed and token == self.token:
            self.music_ready.emit(token, music)

    def refresh_video(self, token):
        frame = self.video_sink.videoFrame()
        if frame.isValid():
            self._frame_changed(frame)

    def toggle_playback(self):
        if self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek(self, seconds, mode):
        target = seek_target(
            seconds, mode, self.player.position() / 1000, self.player.duration() / 1000
        )
        if target is not None and self.player.isSeekable():
            self.player.setPosition(round(target * 1000))

    def set(self, name, value):
        if name == "volume":
            self.audio_output.setVolume(max(0, min(100, float(value))) / 100)
            self.changed.emit("volume", round(self.audio_output.volume() * 100))
        elif name == "mute":
            self._mute = bool(value)
            self.audio_output.setMuted(self._mute)
            self.changed.emit("mute", self._mute)
        elif name == "speed":
            self.player.setPlaybackRate(float(value))
        elif name == "sub-visibility":
            # External subtitle attachment is not exposed by this backend.
            self.changed.emit("sub-visibility", False)
        elif name == "vid":
            self.player.setVideoSink(self.video_sink if value != "no" else None)
        elif name == "loop-file":
            self.player.setLoops(
                QMediaPlayer.Loops.Infinite if value == "inf" else QMediaPlayer.Loops.Once
            )

    def command(self, name, *_args):
        if name == "stop":
            self.player.stop()
            self.player.setSource(QUrl())

    def shutdown(self):
        self.closed = True
        self.player.stop()
        self.player.setVideoSink(None)
