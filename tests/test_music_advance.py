from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, call

from amp.app import Window
from amp.mpv_backend import MpvBackend


def test_music_advances_at_eof_when_repeat_is_disabled(tmp_path):
    current_path = tmp_path / "track1.mp3"
    current_path.touch()
    (tmp_path / "track2.flac").touch()
    window = SimpleNamespace(
        viewport=SimpleNamespace(audio=True),
        preferences=SimpleNamespace(repeat_music=False),
        current_path=current_path,
        navigation_attempt=None,
        _continue_navigation=Mock(),
        notify=Mock(),
    )
    Window.playback_ended(window)
    window._continue_navigation.assert_called_once_with()
    assert window.navigation_attempt.direction == 1


def test_music_does_not_advance_when_repeating_or_for_video():
    window = SimpleNamespace(
        viewport=SimpleNamespace(audio=True),
        preferences=SimpleNamespace(repeat_music=True),
        current_path=Mock(),
        _continue_navigation=Mock(),
    )
    Window.playback_ended(window)
    window.viewport.audio = False
    window.preferences.repeat_music = False
    Window.playback_ended(window)
    window._continue_navigation.assert_not_called()


def test_backend_correlates_natural_eof_with_the_loaded_file_token():
    backend = SimpleNamespace(
        closed=False,
        binding=SimpleNamespace(MpvEventEndFile=SimpleNamespace(ERROR="error", EOF="eof")),
        _entry_tokens={42: 7},
        _entry_lock=nullcontext(),
        playback_ended=Mock(),
        load_failed=Mock(),
    )
    event = SimpleNamespace(data=SimpleNamespace(playlist_entry_id=42, reason="eof"))
    MpvBackend._ended(backend, event)
    backend.playback_ended.emit.assert_called_once_with(7)
    assert 42 not in backend._entry_tokens


def test_backend_uses_eof_property_while_keep_open_retains_the_entry():
    backend = SimpleNamespace(
        closed=False,
        changed=Mock(),
        playback_ended=Mock(),
        _active_entry=42,
        _entry_tokens={42: 7},
        _entry_lock=nullcontext(),
    )
    MpvBackend._observed(backend, "eof-reached", True)
    backend.changed.emit.assert_called_once_with("eof-reached", True)
    backend.playback_ended.emit.assert_called_once_with(7)


def test_backend_unpauses_after_replacing_the_file():
    player = Mock()
    player._get_property.return_value = [{"id": 42}]
    backend = SimpleNamespace(
        player=player,
        _entry_lock=nullcontext(),
        _entry_tokens={},
        submit=lambda function: function(),
    )
    MpvBackend.load(backend, "next.flac", 7)
    calls = player.method_calls
    loaded = calls.index(call.command("loadfile", "next.flac", "replace"))
    unpaused = calls.index(call._set_property("pause", False))
    assert loaded < unpaused
