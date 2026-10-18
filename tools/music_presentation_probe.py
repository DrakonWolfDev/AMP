"""Generate local music tags and verify artwork/lyrics against the real player."""

import argparse
import base64
import json
import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import imageio_ffmpeg
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, USLT
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest

from amp.app import Window, create_application
from amp.music import read_music
from amp.settings import Preferences
from tools.playback_probe import snapshot
from tools.session_probe import wait
from tools.style_probe import compose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/music-presentation"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    image = QImage(480, 480, QImage.Format.Format_RGB32)
    image.fill(QColor("#26394b"))
    painter = QPainter(image)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#d9b579"))
    painter.drawEllipse(155, 105, 170, 170)
    painter.setBrush(QColor("#142431"))
    painter.drawRect(0, 300, 480, 180)
    painter.end()
    cover = output / "cover.png"
    image.save(str(cover))
    art = cover.read_bytes()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for suffix, codec in (
        ("mp3", "libmp3lame"),
        ("flac", "flac"),
        ("m4a", "aac"),
        ("ogg", "libvorbis"),
        ("wav", "pcm_s16le"),
    ):
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000",
                "-t",
                "12",
                "-c:a",
                codec,
                str(output / f"Evening.{suffix}"),
            ],
            check=True,
            capture_output=True,
        )
    tags = ID3()
    for frame in (
        TIT2(text=["Evening light"]),
        TPE1(text=["AMP studio"]),
        TALB(text=["Local sessions"]),
        USLT(text="Embedded words\nStay on this computer"),
        APIC(mime="image/png", type=3, data=art),
    ):
        tags.add(frame)
    tags.save(output / "Evening.mp3")
    picture = Picture()
    picture.mime, picture.type, picture.data = "image/png", 3, art
    flac = FLAC(output / "Evening.flac")
    flac["title"], flac["artist"], flac["lyrics"] = (
        "Evening light",
        "AMP studio",
        "Embedded FLAC words",
    )
    flac.add_picture(picture)
    flac.save()
    mp4 = MP4(output / "Evening.m4a")
    mp4["\xa9nam"], mp4["\xa9ART"], mp4["\xa9lyr"] = (
        ["Evening light"],
        ["AMP studio"],
        ["Embedded M4A words"],
    )
    mp4["covr"] = [MP4Cover(art, imageformat=MP4Cover.FORMAT_PNG)]
    mp4.save()
    ogg = OggVorbis(output / "Evening.ogg")
    ogg["title"], ogg["artist"], ogg["lyrics"] = "Evening light", "AMP studio", "Embedded Ogg words"
    ogg["metadata_block_picture"] = base64.b64encode(picture.write()).decode("ascii")
    ogg.save()
    preferences = Preferences(output / "isolated.ini")
    preferences.volume, preferences.repeat, preferences.muted = 0, False, False
    window = Window(preferences)
    report = {"checks": [], "errors": []}
    window.viewport.failed.connect(report["errors"].append)

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def loaded(path):
        check(window.open_path(path), f"Open {path.name}")
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            wait(50)
            if window.viewport.music_view.music.artist == "AMP studio":
                break
        wait(100)

    try:
        window.show()
        wait(250)
        # No companion file yet: each format must supply its own embedded words/art.
        for suffix in ("mp3", "flac", "m4a", "ogg"):
            music = read_music(output / f"Evening.{suffix}")
            check(
                not music.artwork.isNull() and bool(music.lyrics.lines),
                f"Read actual embedded cover and lyrics from {suffix}",
            )
            loaded(output / f"Evening.{suffix}")
            check(
                not window.viewport.music_view.music.artwork.isNull(),
                f"Display embedded {suffix} artwork",
            )
        window.controls.update_property("pause", True)
        window.video_set("pause", True)
        wait(100)
        compose(window, output / "embedded.png")
        (output / "Evening.lrc").write_text(
            "[00:00]Evening settles\n[00:03]Light across the water\n[00:06]Everything stays here\n[00:09]A quiet final line",
            encoding="utf-8",
        )
        loaded(output / "Evening.mp3")
        window.video_set("pause", True)
        wait(100)
        check(
            window.viewport.music_view.music.lyrics.times == [0, 3, 6, 9],
            "Companion LRC overrides embedded lyrics",
        )
        for target, expected in ((7, 2), (1, 0), (10, 3)):
            window.seek(target, "absolute")
            wait(250)
            view = window.viewport.music_view
            check(
                view.music.lyrics.current(view.position) == expected,
                f"Lyrics follow seek to {target}s",
            )
        window.seek(2.8, "absolute")
        window.video_set("pause", False)
        wait(700)
        window.video_set("pause", True)
        wait(100)
        view = window.viewport.music_view
        check(
            view.music.lyrics.current(view.position) == 1,
            "Highlighted lyric advances during real playback",
        )
        window.seek(12, "absolute")
        window.video_set("pause", False)
        wait(250)
        window.pause()
        wait(200)
        view = window.viewport.music_view
        check(
            view.position < 1 and view.music.lyrics.current(view.position) == 0,
            "Replay returns lyrics to the opening line",
        )
        window.video_set("pause", True)
        window.seek(3.5, "absolute")
        wait(150)
        compose(window, output / "synchronized.png")
        check(snapshot(window, "volume")["volume"] == 0, "Live music probe remains silent")
        window.lyrics_action.trigger()
        check(
            not window.viewport.music_view.show_lyrics, "Menu hides lyrics while preserving artwork"
        )
        compose(window, output / "artwork.png")
        window.resize(1400, 900)
        wait(150)
        compose(window, output / "artwork-large.png")
        window.resize(960, 640)
        wait(100)
        window.lyrics_action.trigger()
        window.resize(540, 400)
        wait(150)
        compose(window, output / "small.png")
        check(
            window.viewport.music_view.music.lyrics.current(window.viewport.music_view.position)
            == 1,
            "Compact view preserves synchronized lyric position",
        )
        (output / "Evening.lrc").unlink()
        (output / "Evening.txt").write_text(
            "\n".join(f"Local lyric line {index}" for index in range(1, 61)), encoding="utf-8"
        )
        loaded(output / "Evening.flac")
        wait(150)
        check(window.viewport.music_view.scroll_max > 0, "Plain lyrics have a scrollable document")
        QTest.keyClick(window.viewport, Qt.Key.Key_PageDown)
        wait(100)
        check(window.viewport.music_view.scroll > 0, "Page Down scrolls plain lyrics")
        compose(window, output / "plain.png")
        QTest.keyClick(window.viewport, Qt.Key.Key_Home)
        wait(100)
        check(window.viewport.music_view.scroll == 0, "Home returns to the start of plain lyrics")
        (output / "Evening.txt").unlink()
        window.resize(960, 640)
        window.open_path(output / "Evening.wav")
        wait(350)
        check(
            window.viewport.music_view.music.artwork.isNull()
            and not window.viewport.music_view.music.lyrics.lines,
            "Untagged music clears prior artwork and lyrics",
        )
        compose(window, output / "title.png")
        window.viewport.setFocus()
        window.chrome.fade()
        wait(300)
        check(
            window.open_media.graphicsEffect().opacity() == 0,
            "Open media fades with the other controls",
        )
        with patch(
            "amp.app.QFileDialog.getOpenFileName", return_value=(str(output / "Evening.flac"), "")
        ) as picker:
            window.choose()
        wait(250)
        check(
            window.current_path == (output / "Evening.flac").resolve()
            and picker.call_args.args[2] == str(output.resolve()),
            "Open media replaces the file in this window and starts in its folder",
        )
        other = output / "Other folder" / "Another song.wav"
        other.parent.mkdir(exist_ok=True)
        shutil.copyfile(output / "Evening.wav", other)
        with patch("amp.app.QFileDialog.getOpenFileName", return_value=(str(other), "")):
            window.choose()
        wait(150)
        check(
            window.current_path == other.resolve() and window.viewport.audio,
            "Open media switches to another folder without replacing the window",
        )
        with patch("amp.app.QFileDialog.getOpenFileName", return_value=("", "")):
            window.choose()
        check(
            window.current_path == other.resolve(),
            "Cancelling the picker preserves the current file",
        )
        window.open_path(output / "Evening.mp3")
        window.open_path(cover)
        wait(250)
        check(
            not window.viewport.audio and not window.lyrics_action.isVisible(),
            "Switch to image ignores queued music metadata and hides lyric action",
        )
        check(not report["errors"], "No playback or metadata errors")
        report["passed"] = True
        report["dpr"] = window.viewport.devicePixelRatioF()
    finally:
        window.close()
        wait(100)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
