from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, USLT
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QColor, QImage

from amp.music import MAX_TEXT, Music, companion_lyrics, decode_artwork, parse_lyrics, read_music
from amp.viewport import MediaViewport


def picture():
    image = QImage(24, 16, QImage.Format.Format_RGB32)
    image.fill(QColor("#d9b579"))
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def test_lrc_repeated_timestamps_offset_and_backward_seeking():
    lyrics = parse_lyrics("[ar:Artist]\n[offset:-500]\n[00:03.00]Last\n[00:01.5][00:02.50]Again")
    assert lyrics.times == [1, 2, 2.5]
    assert lyrics.lines == ["Again", "Again", "Last"]
    assert [lyrics.current(time) for time in (0, 1, 5, 1.5)] == [-1, 0, 2, 0]


def test_lrc_translations_and_blank_lines_are_retained():
    lyrics = parse_lyrics("[00:01]Hello\n[00:01]Bonjour\n[00:02]\n[00:70]bad")
    assert lyrics.lines == ["Hello\nBonjour", ""]
    assert lyrics.times == [1, 2]


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16"])
def test_companion_precedence_and_unicode(tmp_path, encoding):
    track = tmp_path / "Song.flac"
    track.with_suffix(".lrc").write_text("[00:01]Café", encoding=encoding)
    track.with_suffix(".txt").write_text("Plain words", encoding="utf-8")
    assert companion_lyrics(track).lines == ["Café"]


def test_unreadable_or_oversized_lrc_falls_back_to_plain_text(tmp_path):
    track = tmp_path / "Song.mp3"
    track.with_suffix(".lrc").write_bytes(b"x" * (MAX_TEXT + 1))
    track.with_suffix(".txt").write_text("First\n\nLast", encoding="utf-8")
    assert companion_lyrics(track).lines == ["First", "", "Last"]


def test_id3_metadata_artwork_and_embedded_lyrics(monkeypatch, tmp_path):
    tags = ID3()
    for frame in (
        TIT2(text=["Title"]),
        TPE1(text=["Artist"]),
        TALB(text=["Album"]),
        USLT(text="Words"),
        APIC(mime="image/png", type=3, data=picture()),
    ):
        tags.add(frame)
    monkeypatch.setattr("amp.music.mutagen.File", lambda path: SimpleNamespace(tags=tags))
    music = read_music(tmp_path / "song.mp3")
    assert (music.title, music.artist, music.album) == ("Title", "Artist", "Album")
    assert music.lyrics.lines == ["Words"]
    assert not music.artwork.isNull()
    assert music.artwork.pixelColor(0, 0) == QColor("#d9b579")


def test_artwork_links_are_never_resolved(monkeypatch, tmp_path):
    tags = ID3()
    tags.add(APIC(mime="-->", type=3, data=b"https://example.com/cover.png"))
    monkeypatch.setattr("amp.music.mutagen.File", lambda path: SimpleNamespace(tags=tags))
    assert read_music(tmp_path / "song.mp3").artwork.isNull()
    assert decode_artwork(b"damaged image").isNull()


def test_missing_music_keeps_filename_and_local_lyrics(tmp_path):
    path = tmp_path / "Unavailable song.mp3"
    path.with_suffix(".lrc").write_text("[00:01]Local words", encoding="utf-8")
    music = read_music(path)
    assert music.title == "Unavailable song"
    assert music.lyrics.lines == ["Local words"]


def test_stale_metadata_cannot_replace_current_track_or_image():
    viewport = SimpleNamespace(
        closed=False,
        audio=True,
        load_serial=2,
        music_view=SimpleNamespace(position=4, set_music=Mock()),
        setAccessibleName=Mock(),
        update=Mock(),
    )
    music = Music(title="Old")
    MediaViewport._music_ready(viewport, 1, music)
    viewport.music_view.set_music.assert_not_called()
    viewport.audio = False
    MediaViewport._music_ready(viewport, 2, music)
    viewport.music_view.set_music.assert_not_called()
    viewport.audio = True
    MediaViewport._music_ready(viewport, 2, music)
    viewport.music_view.set_music.assert_called_once_with(music)
    assert viewport.music_view.position == 4
