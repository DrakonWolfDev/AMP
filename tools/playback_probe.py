"""Live transport/audio-output/lifecycle checks. Tests use zero output volume."""

import json
import subprocess
import threading
import time
import traceback
from contextlib import suppress
from pathlib import Path

import imageio_ffmpeg
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from amp.app import Window, create_application
from amp.settings import Preferences
from tools.session_probe import wait


def snapshot(window, *names):
    backend = window.viewport.backend

    def read():
        result = {}
        for name in names:
            try:
                result[name] = backend.player._get_property(name)
            except AttributeError:
                result[name] = None
        return result

    future = backend.worker.submit(read)
    deadline = time.monotonic() + 4
    while not future.done() and time.monotonic() < deadline:
        wait(20)
    assert future.done(), "mpv worker stalled"
    return future.result()


def main():
    output = Path("artifacts/playback")
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    def generate(name, arguments):
        subprocess.run(
            [ffmpeg, "-y", *arguments, str(output / name)], check=True, capture_output=True
        )

    generate(
        "av.mp4",
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "8",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
        ],
    )
    generate("tone.wav", ["-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000", "-t", "8"])
    generate("silent.mkv", ["-i", str(output / "av.mp4"), "-an", "-c:v", "copy"])
    generate("legacy.wmv", ["-i", str(output / "av.mp4"), "-c:v", "wmv2", "-c:a", "wmav2"])
    for suffix in ("ts", "mts", "m2ts"):
        options = ["-mpegts_m2ts_mode", "1"] if suffix == "m2ts" else []
        generate(
            f"camera.{suffix}",
            ["-i", str(output / "av.mp4"), "-c", "copy", "-f", "mpegts", *options],
        )
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    windows = []
    baseline = {thread.ident for thread in threading.enumerate()}
    report = {"checks": [], "errors": [], "audio_output": None}

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    try:
        preferences = Preferences(output / "unused-preferences.ini")
        preferences.repeat, preferences.volume = False, 0
        first = Window(preferences)
        windows.append(first)
        first.controls.volume.setValue(0)
        first.viewport.failed.connect(lambda message: report["errors"].append(message))
        first.show()
        wait(200)
        check(first.open_path(output / "av.mp4"), "Open video with AAC audio")
        wait(1600)
        state = snapshot(first, "current-ao", "audio-out-params", "audio-params", "volume")
        report["audio_output"] = state
        check(
            state["current-ao"] not in (None, "null") and bool(state["audio-out-params"]),
            "Real system audio output opens for decoded AAC at zero volume",
        )
        check(state["volume"] == 0, "Probe produces no test tone at the output")
        first.controls.mute.setChecked(True)
        first.viewport.backend.set("volume", 37)
        wait(100)
        state = snapshot(first, "volume", "mute")
        check(state["volume"] == 37 and state["mute"], "Volume/mute reach mpv")
        reopened = Window(Preferences(preferences.path))
        windows.append(reopened)
        check(
            reopened.controls.mute.isChecked() and reopened.controls.volume.value() == 0,
            "A newly opened player restores saved mute with a zero slider",
        )
        reopened.show()
        reopened.open_path(output / "silent.mkv")
        wait(400)
        restored = snapshot(reopened, "volume", "mute")
        check(
            restored["mute"] and restored["volume"] == reopened.controls.volume_level,
            "Opening media while muted preserves its underlying restore volume",
        )
        reopened.close()
        # Keep muted while verifying observer-to-widget synchronisation.
        first.viewport.backend.set("volume", 19)
        wait(100)
        check(
            first.controls.volume.value() == 0 and first.controls.volume_level == 19,
            "Muted slider stays zero while retaining decoder volume changes",
        )
        first.viewport.backend.set("volume", 0)
        first.viewport.backend.set("mute", False)
        wait(100)
        check(not first.controls.mute.isChecked(), "Decoder mute changes update button")
        first.controls.speed.setValue(40)
        wait(100)
        check(snapshot(first, "speed")["speed"] == 2, "Speed slider sets decoder to 2×")
        start = first.controls.position
        wait(500)
        fast_delta = first.controls.position - start
        first.controls.speed.setValue(10)
        wait(150)
        start = first.controls.position
        wait(500)
        slow_delta = first.controls.position - start
        check(
            0.6 < fast_delta < 1.5 and 0.1 < slow_delta < 0.5,
            "Video clock advances at selected fast and slow playback rates",
        )
        first.controls.speed_label.click()
        wait(100)
        check(snapshot(first, "speed")["speed"] == 1, "Speed label restores normal playback")
        first.seek(0, "absolute")
        wait(100)
        QTest.mouseClick(first.controls.play, Qt.MouseButton.LeftButton)
        wait(100)
        paused_at = first.controls.position
        wait(200)
        check(
            first.controls.play.text() == "Play" and abs(first.controls.position - paused_at) < 0.1,
            "Play button pauses the video clock",
        )
        first.seek(-5, "relative")
        wait(150)
        check(first.controls.position < 0.1, "Backward seek clamps at zero")
        first.controls.timeline.setSliderPosition(5000)
        first.controls.seek()
        wait(150)
        check(abs(first.controls.position - 4) < 0.3, "Timeline seeks paused video to halfway")
        QTest.mouseClick(first.controls.seek_buttons[1], Qt.MouseButton.LeftButton)
        wait(200)
        check(first.controls.position > 7, "Forward button clamps at media end")
        # The clamped seek above may already be EOF. Test natural completion
        # from a known point before it, without accidentally invoking Replay.
        first.seek(7.5, "absolute")
        first.video_set("pause", False)
        deadline = time.monotonic() + 2
        while first.controls.play.text() != "Replay" and time.monotonic() < deadline:
            wait(20)
        check(first.controls.play.text() == "Replay", "End of file exposes Replay")
        path = first.current_path
        wait(150)
        check(first.current_path == path, "End of file does not navigate or loop automatically")
        QTest.mouseClick(first.controls.play, Qt.MouseButton.LeftButton)
        wait(350)
        check(
            first.controls.play.text() == "Pause" and first.controls.position < 1,
            "Replay restarts video from beginning",
        )
        for name in ("silent.mkv", "legacy.wmv", "camera.ts", "camera.mts", "camera.m2ts"):
            before = first.viewport.render_count
            check(first.open_path(output / name), f"Open {name}")
            wait(650)
            check(first.viewport.render_count > before + 5, f"Live playback: {name}")
            check(
                first.controls.duration > 7 and first.controls.play.text() == "Pause",
                f"Transport refreshes after same-duration media switch: {name}",
            )
            if name == "silent.mkv":
                state = snapshot(first, "audio-params", "current-ao")
                check(
                    state["audio-params"] is None and state["current-ao"] is None,
                    "Switch to silent video releases prior audio stream/output",
                )
        first.controls.speed.setValue(30)
        first.open_path(output / "tone.wav")
        wait(300)
        check(
            not first.controls.speed_panel.isVisible() and snapshot(first, "speed")["speed"] == 1,
            "Music hides video speed controls and restores normal playback rate",
        )
        first.seek(100, "absolute")
        wait(200)
        check(first.controls.play.text() == "Replay", "Music end exposes Replay")
        first.pause()
        wait(200)
        check(
            first.controls.position < 1 and first.controls.play.text() == "Pause",
            "Music Replay restarts track",
        )
        second = Window(preferences)
        windows.append(second)
        second.controls.volume.setValue(0)
        second.viewport.failed.connect(lambda message: report["errors"].append(message))
        second.show()
        wait(150)
        second.open_path(output / "tone.wav")
        wait(500)
        first.pause()
        wait(100)
        before = second.controls.position
        wait(250)
        check(
            second.controls.position > before and first.controls.play.text() == "Play",
            "Two audio windows keep independent pause/play state",
        )
        first.open_path(Path("artifacts/probe/portrait.png"))
        wait(250)
        state = snapshot(first, "idle-active", "current-ao", "audio-params", "time-pos")
        check(
            state["idle-active"]
            and state["current-ao"] is None
            and state["audio-params"] is None
            and state["time-pos"] is None,
            "Image switch stops playback and releases audio output",
        )
        first_backend = first.viewport.backend
        event_thread = first_backend.player._event_thread
        first.close()
        wait(150)
        check(
            first_backend.closed and not event_thread.is_alive(),
            "Close terminates first core and event thread",
        )
        before = second.controls.position
        wait(200)
        check(second.controls.position > before, "Other audio window survives first shutdown")
        for index in range(12):
            second.open_path(output / ("tone.wav" if index % 2 else "av.mp4"))
        started = time.monotonic()
        second.close()
        check(
            time.monotonic() - started < 2, "Rapid media switching still closes within two seconds"
        )
        wait(150)
        leftovers = [
            t.name
            for t in threading.enumerate()
            if t.ident not in baseline
            and (t.name.startswith("amp-mpv") or t.name == "MPVEventHandlerThread")
        ]
        check(not leftovers, "No leftover mpv worker/event threads after both windows close")
        check(not report["errors"], "No backend operation errors")
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- record every integration failure
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        for window in windows:
            with suppress(RuntimeError):
                window.close()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
