from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from amp.viewport import MediaViewport


@pytest.mark.parametrize("method", [MediaViewport.open_video, MediaViewport.open_audio])
def test_window_preferences_reach_core_before_autoplay_load(method):
    backend = Mock()
    viewport = SimpleNamespace(
        ensure_video=Mock(),
        backend=backend,
        load_serial=0,
        transform=SimpleNamespace(),
        reset=Mock(),
        update=Mock(),
        music_view=Mock(),
        _stop_image_movie=Mock(),
    )
    path = Path("chosen-media.mp4")
    method(viewport, path, playback_options={"volume": 17, "mute": True, "loop-file": "inf"})
    calls = backend.method_calls
    expected_load = (
        call.load(path, 1, subtitles=[])
        if method is MediaViewport.open_video
        else call.load(path, 1)
    )
    load = calls.index(expected_load)
    assert calls.index(call.set("volume", 17)) < load
    assert calls.index(call.set("mute", True)) < load
    assert calls.index(call.set("loop-file", "inf")) < load
