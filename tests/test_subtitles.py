from pathlib import Path
from threading import Lock
from types import SimpleNamespace

from amp.mpv_backend import MpvBackend, companion_subtitles
from amp.subtitles import SubtitleCue, SubtitleTrack, parse_srt_text, read_srt


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


def test_srt_parser_handles_bom_multiline_markup_and_dot_milliseconds():
    cues = parse_srt_text(
        "\ufeff1\n00:00:01,250 --> 00:00:03.5\n<i>Hello &amp; welcome</i>\nSecond line\n\n"
        "broken\nnot timing\nignored\n"
    )

    assert cues == [SubtitleCue(1.25, 3.5, "Hello & welcome\nSecond line")]


def test_track_combines_overlapping_cues_and_treats_end_as_exclusive():
    track = SubtitleTrack(
        [
            SubtitleCue(1, 3, "First"),
            SubtitleCue(2, 4, "Second"),
            SubtitleCue(4, 5, "Third"),
        ]
    )

    assert track.text_at(0.9) == ""
    assert track.text_at(2.5) == "First\nSecond"
    assert track.text_at(3) == "Second"
    assert track.text_at(4) == "Third"
    assert track.text_at(5) == ""


def test_srt_reader_accepts_utf16(tmp_path):
    path = tmp_path / "Film.srt"
    path.write_bytes("1\n00:00:00,000 --> 00:00:01,000\nHello\n".encode("utf-16"))

    assert read_srt(path).text_at(0.5) == "Hello"


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
