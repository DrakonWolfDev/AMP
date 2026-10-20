from pathlib import Path
from threading import Lock
from types import SimpleNamespace

from amp.mpv_backend import MpvBackend, companion_subtitles


def test_companion_subtitles_are_local_matching_and_exact_name_first(tmp_path):
    video = tmp_path / "Film.mkv"
    video.touch()
    exact = tmp_path / "Film.srt"
    english = tmp_path / "Film.en.SRT"
    forced = tmp_path / "Film.forced.srt"
    unrelated = tmp_path / "Other.srt"
    nested = tmp_path / "nested"
    nested.mkdir()
    for path in (exact, english, forced, unrelated, nested / "Film.srt"):
        path.touch()

    assert companion_subtitles(video) == [exact, english, forced]


def test_missing_companion_subtitle_directory_is_harmless(tmp_path):
    assert companion_subtitles(tmp_path / "missing" / "Film.mkv") == []


def test_backend_attaches_first_subtitle_and_keeps_other_tracks_available():
    source = Path("Film.mkv")
    subtitles = [Path("Film.srt"), Path("Film.en.srt")]

    class Player:
        def __init__(self):
            self.commands = []

        def command(self, *args):
            self.commands.append(args)

        def _get_property(self, name):
            assert name == "playlist"
            return [{"id": 7}]

        def _set_property(self, name, value):
            self.commands.append(("set-property", name, value))

    backend = SimpleNamespace(
        player=Player(),
        _entry_tokens={},
        _entry_lock=Lock(),
        submit=lambda fn, *args: fn(*args),
    )
    MpvBackend.load(backend, source, 3, subtitles=subtitles)

    assert backend.player.commands == [
        ("loadfile", "Film.mkv", "replace"),
        ("set-property", "pause", False),
        ("sub-add", "Film.srt", "select"),
        ("sub-add", "Film.en.srt", "auto"),
        ("set-property", "sub-visibility", False),
    ]
    assert backend._entry_tokens == {7: 3}
