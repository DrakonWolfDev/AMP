"""Real pointer scrubbing and corner-button fullscreen regression checks."""

import argparse
import json
import traceback
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QColor, QImage, QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolButton

from amp.app import Window, create_application
from amp.settings import Preferences
from tools.playback_probe import snapshot
from tools.session_probe import wait


class ObservedWindow(Window):
    def __init__(self, preferences):
        self.state_changes = []
        super().__init__(preferences)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self.state_changes.append(self.isFullScreen())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/interaction"))
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "unused.ini")
    preferences.volume = 0
    window = ObservedWindow(preferences)
    report = {"checks": [], "errors": [], "fullscreen_frames": []}
    window.viewport.failed.connect(report["errors"].append)

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def point(slider, fraction, y=None):
        return QPoint(
            round(6 + fraction * (slider.width() - 13)), slider.height() // 2 if y is None else y
        )

    target_state = None
    presented = []
    transition_frames = []

    def frame_presented():
        if target_state is None or window.isFullScreen() != target_state:
            return
        try:
            frame = window.viewport.capture()
        except RuntimeError:
            return
        colour = frame.pixelColor(frame.width() // 2, frame.height() // 2)
        recorded = {"size": [frame.width(), frame.height()], "rgb": list(colour.getRgb()[:3])}
        if window.fullscreen_timer.isActive():
            transition_frames.append(recorded)
        else:
            presented.append(recorded)

    try:
        window.show()
        wait(200)
        report["dpr"] = window.viewport.devicePixelRatioF()
        window.open_path("artifacts/playback/av.mp4")
        wait(600)
        window.pause()
        wait(150)
        slider = window.controls.timeline
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.75))
        wait(200)
        check(
            abs(snapshot(window, "time-pos")["time-pos"] - 6) < 0.3,
            "A rail click seeks paused video directly to 75 percent",
        )
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.75, y=1))
        QTest.mouseMove(slider, point(slider, 0.95))
        wait(100)
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.95))
        wait(200)
        check(
            abs(snapshot(window, "time-pos")["time-pos"] - 7.6) < 0.3,
            "Dragging from the full-height target seeks near EOF",
        )
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0))
        wait(150)
        check(snapshot(window, "time-pos")["time-pos"] < 0.2, "Clicking the start returns to zero")
        window.pause()
        wait(150)
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.2))
        QTest.mouseMove(slider, point(slider, 0.7))
        held = slider.value()
        wait(350)
        check(
            slider.isSliderDown() and slider.value() == held,
            "Live decoder clock updates cannot steal the user's drag position",
        )
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.7))
        wait(200)
        check(
            5.5 < snapshot(window, "time-pos")["time-pos"] < 6.2,
            "Release seeks playing video and playback continues",
        )
        window.pause()
        wait(100)
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=point(slider, 1))
        wait(200)
        check(
            snapshot(window, "time-pos")["time-pos"] > 7.9 and slider.value() >= 9900,
            "Clicking the rail endpoint seeks to the final video frame",
        )
        window.video_set("pause", False)
        wait(200)
        check(
            snapshot(window, "eof-reached")["eof-reached"]
            and window.controls.play.text() == "Replay",
            "Playing from the scrubbed endpoint reaches EOF and exposes Replay",
        )
        window.pause()
        wait(100)
        check(
            snapshot(window, "time-pos")["time-pos"] < 0.5,
            "Replay still works after scrubbing to the endpoint",
        )
        renders = window.viewport.render_count
        window.toggle_fullscreen()
        wait(220)
        check(
            window.isFullScreen()
            and window.updatesEnabled()
            and window.viewport.render_count > renders,
            "Playing video resumes live rendering after the settled fullscreen transition",
        )
        QTest.keyClick(window.viewport, Qt.Key.Key_Escape)
        wait(220)
        check(
            not window.isFullScreen()
            and window.updatesEnabled()
            and not snapshot(window, "pause")["pause"],
            "Escape returns playing video without changing its pause state",
        )

        image = QImage(600, 900, QImage.Format.Format_RGB32)
        image.fill(QColor("#426478"))
        image_path = output / "portrait.png"
        image.save(str(image_path))
        window.open_path(image_path)
        wait(200)
        before = window.viewport.capture()
        original_size = window.size()
        button = next(
            b
            for b in window.toolbar.findChildren(QToolButton)
            if b.defaultAction() is window.actions_by_name["Fullscreen"]
        )
        window.viewport.frameSwapped.connect(frame_presented)
        for index in range(6):
            target_state = not window.isFullScreen()
            presented.clear()
            transition_frames.clear()
            window.state_changes.clear()
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            check(window.updatesEnabled(), "Fullscreen never disables window painting")
            # A second click in the native transition must not bounce back.
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            if index == 0:
                window.screenshot()
                check(
                    window.pending_capture is None
                    and "updating" in window.statusBar().currentMessage(),
                    "Screenshot waits for the fullscreen transition instead of retaining stale pixels",
                )
            wait(220)
            check(
                transition_frames and all(f["rgb"] == [66, 100, 120] for f in transition_frames),
                f"Corner transition {index + 1}: valid media is presented during the native resize",
            )
            check(
                window.isFullScreen() == target_state
                and window.state_changes
                and all(s == target_state for s in window.state_changes),
                f"Corner transition {index + 1}: one intended fullscreen state without bouncing",
            )
            check(
                window.updatesEnabled() and not window.fullscreen_timer.isActive() and presented,
                f"Corner transition {index + 1}: rendering resumes after state/geometry settle",
            )
            check(
                all(f["rgb"] == [66, 100, 120] for f in presented)
                and len({tuple(f["size"]) for f in presented}) == 1,
                f"Corner transition {index + 1}: presented image frames are valid at one physical size",
            )
            report["fullscreen_frames"].append(
                {
                    "fullscreen": target_state,
                    "transition_frames": list(transition_frames),
                    "frames": list(presented),
                }
            )
        target_state = None
        check(
            window.size() == original_size and window.viewport.capture() == before,
            "Returning to windowed mode restores exact image composition and size",
        )
        repeat = QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key.Key_F, Qt.KeyboardModifier.NoModifier, "f", True, 1
        )
        QApplication.sendEvent(window.viewport, repeat)
        check(not window.isFullScreen(), "An auto-repeated F cannot repeatedly toggle the window")
        QTest.keyClick(window.viewport, Qt.Key.Key_F11)
        wait(200)
        QTest.keyClick(window.viewport, Qt.Key.Key_Escape)
        wait(200)
        check(
            not window.isFullScreen() and window.updatesEnabled(),
            "F11 and Escape use the same settled transition path",
        )
        window.showMaximized()
        wait(180)
        maximized_size = window.size()
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        wait(220)
        QTest.keyClick(window.viewport, Qt.Key.Key_Escape)
        wait(220)
        check(
            window.isMaximized() and not window.isFullScreen() and window.size() == maximized_size,
            "Leaving fullscreen restores a previously maximized window",
        )
        check(not report["errors"], "No backend errors during pointer/fullscreen interactions")
        window.toggle_fullscreen()
        window.close()
        wait(100)
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- retain every live interaction failure
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
        window.close()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
