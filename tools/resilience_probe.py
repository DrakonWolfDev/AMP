"""M8 live window ownership, navigation churn, capture and teardown checks.

Run render_probe and playback_probe first. Output is silent/muted throughout.
"""

import gc
import json
import shutil
import threading
import time
import traceback
from contextlib import suppress
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from amp.app import Window, create_application
from amp.capture import save_capture
from amp.settings import Preferences
from tools.playback_probe import snapshot
from tools.session_probe import wait


def media_threads():
    return [
        t
        for t in threading.enumerate()
        if t.name.startswith("amp-mpv") or t.name == "MPVEventHandlerThread"
    ]


def main():
    output = Path("artifacts/resilience")
    output.mkdir(parents=True, exist_ok=True)
    for name, colour in (("first", "#884433"), ("second", "#337788")):
        folder = output / name
        folder.mkdir(exist_ok=True)
        shutil.copyfile("artifacts/playback/av.mp4", folder / "file1.mp4")
        image = QImage(300, 500, QImage.Format.Format_RGB32)
        image.fill(QColor(colour))
        image.save(str(folder / "file2.png"))
        shutil.copyfile("artifacts/playback/tone.wav", folder / "file3.wav")
        (folder / "file4.mp4").write_bytes(b"deliberately corrupt")
    preferences_path = output / "preferences.ini"
    Preferences(preferences_path).save(False, 0, 3)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    report = {"checks": [], "errors": [], "close_seconds": [], "switches": 0}
    windows = []
    baseline = {t.ident for t in media_threads()}

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def new_window():
        window = Window(Preferences(preferences_path))
        window.viewport.failed.connect(report["errors"].append)
        windows.append(window)
        window.show()
        wait(150)
        return window

    def close(window):
        start = time.monotonic()
        window.close()
        elapsed = time.monotonic() - start
        report["close_seconds"].append(elapsed)
        assert elapsed < 2, f"Window close took {elapsed:.2f}s"
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        wait(50)

    try:
        first = new_window()
        report["dpr"] = first.viewport.devicePixelRatioF()
        check(first.open_path(output / "first/file1.mp4"), "First video opens")
        wait(500)
        with patch("amp.app.Preferences", side_effect=lambda: Preferences(preferences_path)):
            QTest.keyClick(first.viewport, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
        wait(200)
        check(len(app.amp_windows) == 1, "Ctrl+N owns a new top-level window")
        second = app.amp_windows[0]
        windows.append(second)
        second.viewport.failed.connect(report["errors"].append)
        check(second.open_path(output / "second/file1.mp4"), "Second window opens another folder")
        second.video_set("loop-file", "inf")
        wait(650)
        check(
            first.viewport.backend is not second.viewport.backend
            and first.viewport.renderer is not second.viewport.renderer,
            "Windows own separate cores and GL render contexts",
        )
        first.controls.volume.setValue(23)
        second.controls.volume.setValue(61)
        first.video_set("mute", True)
        second.video_set("mute", True)
        first.pause()
        first.seek(2, "absolute")
        second.seek(4, "absolute")
        first.viewport.transform.zoom_at(200, 200, 2)
        first.viewport.transform.pan(-30, 20)
        first.viewport.apply_transform()
        second.viewport.transform.zoom_at(400, 250, 3)
        second.viewport.transform.pan(25, -10)
        second.viewport.apply_transform()
        wait(300)
        a = snapshot(first, "pause", "volume", "time-pos")
        b = snapshot(second, "pause", "volume", "time-pos")
        check(
            a["pause"] and not b["pause"] and a["volume"] == 23 and b["volume"] == 61,
            "Pause, volume and seek are independent in actual decoder cores",
        )
        check(
            abs(a["time-pos"] - 2) < 0.3 and b["time-pos"] > 4, "Seek position remains per window"
        )
        check(
            first.viewport.transform.zoom == 2 and second.viewport.transform.zoom == 3,
            "Zoom and pan remain per window",
        )
        with patch("amp.app.save_capture", side_effect=PermissionError("Probe storage failure")):
            first.screenshot()
        retained = first.pending_capture.copy()
        second_frame = second.viewport.capture()
        second_capture = save_capture(second_frame, output / "captures")
        check(
            first.pending_capture == retained
            and second.pending_capture is None
            and second_capture.is_file(),
            "Capture failure/retry state is isolated per window",
        )
        first.open_path(output / "first/file2.png")
        saved = []

        def retry(image):
            path = save_capture(image, output / "captures")
            saved.append(path)
            return path

        with patch("amp.app.save_capture", side_effect=retry):
            first.screenshot()
        check(
            len(saved) == 1
            and QImage(str(saved[0])).convertToFormat(retained.format()) == retained
            and first.pending_capture is None,
            "First window retries its own exact earlier video frame",
        )
        survivor_transform = second.viewport.transform.rect
        survivor_count = second.viewport.render_count
        for index in range(48):
            name = ("file1.mp4", "file3.wav", "file4.mp4", "file2.png")[index % 4]
            first.open_path(output / "first" / name)
            if index % 8 == 0:
                first.showFullScreen()
            elif index % 8 == 4:
                first.showNormal()
                first.resize(700 + index, 480 + index)
            wait(35)
            report["switches"] += 1
        first.open_path(output / "first/file2.png")
        wait(350)
        check(
            first.current_path.name == "file2.png" and not first.viewport.playable,
            "Rapid video/music/corrupt/image switching settles on the latest request",
        )
        check(
            snapshot(first, "idle-active", "current-ao")
            == {
                "idle-active": True,
                "current-ao": None,
            },
            "Final image releases the churned audio output",
        )
        check(
            second.viewport.render_count > survivor_count
            and second.viewport.transform.rect == survivor_transform
            and second.current_path.parent.name == "second"
            and snapshot(second, "volume", "pause") == {"volume": 61, "pause": False},
            "Other video keeps playing with unchanged folder, transform, volume and pause",
        )
        (output / "first/file2.png").unlink()
        first.navigate(1)
        wait(400)
        check(
            first.current_path.name == "file3.wav" and first.viewport.audio,
            "Navigation survives deletion of the displayed file",
        )
        first.navigate(1)
        wait(600)
        check(
            first.current_path.name == "file1.mp4" and first.loop_notice.isVisible(),
            "Navigation skips corrupt video across a folder boundary",
        )
        for index in range(16):
            first.navigate(1 if index % 2 else -1)
            wait(15)
        first.open_path(output / "first/file3.wav")
        wait(250)
        check(
            first.viewport.audio and first.current_path.name == "file3.wav",
            "Rapid direction changes cannot revive superseded navigation",
        )
        first_backend = first.viewport.backend
        event_thread = first_backend.player._event_thread
        close(first)
        check(
            not event_thread.is_alive() and first_backend.closed,
            "Closing churned window terminates its event/core threads",
        )
        survivor_count = second.viewport.render_count
        wait(250)
        check(
            second.viewport.render_count > survivor_count,
            "Surviving video continues after other window closes",
        )
        close(second)
        check(not app.amp_windows, "Destroyed Ctrl+N window is removed from ownership registry")
        for index in range(10):
            temporary = new_window()
            temporary.open_path(output / "first" / ("file3.wav" if index % 2 else "file1.mp4"))
            wait(70)
            temporary.seek(3, "absolute")
            close(temporary)
            assert not isValid(temporary), "Qt window was not deleted"
        gc.collect()
        wait(200)
        leftovers = [t.name for t in media_threads() if t.ident not in baseline]
        check(not leftovers, "Ten reopen/close cycles leave no mpv workers or event threads")
        check(max(report["close_seconds"]) < 2, "Every stressed window closes within two seconds")
        check(not report["errors"], "No unexpected backend command or render errors")
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- preserve all live integration failures
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        for window in windows:
            with suppress(RuntimeError):
                window.close()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
