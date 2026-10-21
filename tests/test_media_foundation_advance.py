from unittest.mock import Mock

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

QMediaPlayer = pytest.importorskip("PySide6.QtMultimedia", exc_type=ImportError).QMediaPlayer

from amp import media_foundation_backend as mf  # noqa: E402


class FakePlayer(QObject):
    MediaStatus = QMediaPlayer.MediaStatus
    PlaybackState = QMediaPlayer.PlaybackState
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    seekableChanged = Signal(bool)
    playbackRateChanged = Signal(float)
    playbackStateChanged = Signal(object)
    mediaStatusChanged = Signal(object)
    errorOccurred = Signal(object, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.status = self.MediaStatus.EndOfMedia
        self.state = self.PlaybackState.PlayingState
        self.setAudioOutput = Mock()
        self.setVideoSink = Mock()

    def mediaStatus(self):
        return self.status


@pytest.fixture
def backend(monkeypatch):
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    monkeypatch.setattr(mf, "QMediaPlayer", FakePlayer)
    monkeypatch.setattr(mf, "QAudioOutput", Mock())
    monkeypatch.setattr(mf, "QVideoSink", Mock())
    backend = mf.MediaFoundationBackend()
    backend.token = 7
    yield app, backend
    backend.closed = True


def test_next_track_starts_after_windows_finishes_stopping(backend):
    app, backend = backend
    ended = Mock()
    backend.playback_ended.connect(ended)

    def start_next(token):
        assert token == 7
        backend.player.state = FakePlayer.PlaybackState.PlayingState
        backend.player.status = FakePlayer.MediaStatus.LoadingMedia
        backend.token = 8

    backend.playback_ended.connect(start_next)
    backend.player.mediaStatusChanged.emit(FakePlayer.MediaStatus.EndOfMedia)
    ended.assert_not_called()
    # MFPlayerControl applies this stop after notifying mediaStatusChanged.
    backend.player.state = FakePlayer.PlaybackState.StoppedState
    app.processEvents()
    ended.assert_called_once_with(7)
    assert backend.player.state == FakePlayer.PlaybackState.PlayingState


@pytest.mark.parametrize("interruption", ["close", "replace", "replay", "stop"])
def test_pending_end_is_ignored_after_playback_changes(backend, interruption):
    app, backend = backend
    ended = Mock()
    backend.playback_ended.connect(ended)
    backend.player.mediaStatusChanged.emit(FakePlayer.MediaStatus.EndOfMedia)
    if interruption == "close":
        backend.closed = True
    elif interruption == "replace":
        backend.token += 1
    else:
        backend.player.status = (
            FakePlayer.MediaStatus.LoadedMedia
            if interruption == "replay"
            else FakePlayer.MediaStatus.NoMedia
        )
    app.processEvents()
    ended.assert_not_called()
