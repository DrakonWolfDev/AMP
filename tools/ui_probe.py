"""Visible Windows M7 probe; run after render_probe and playback_probe."""

import json
import traceback
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from amp.app import Window, create_application
from amp.settings import Preferences, SettingsDialog
from tools.playback_probe import snapshot
from tools.session_probe import wait


def main():
    output = Path("artifacts/ui")
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "preferences.ini")
    preferences.save(False, 0, 3)
    window = Window(preferences)
    report = {"checks": [], "errors": []}
    window.viewport.failed.connect(report["errors"].append)

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def idle():
        window.viewport.setFocus()
        QCursor.setPos(window.viewport.mapToGlobal(window.viewport.rect().center()))
        window.chrome.reveal()
        wait(2700)

    try:
        window.show()
        wait(400)
        check(window.open_path("artifacts/probe/portrait.png"), "Open image")
        wait(300)
        size = window.viewport.size()
        before = window.viewport.capture()
        before.save(str(output / "before.png"))
        check(not window.controls.isVisible(), "Image hides transport")
        # Native presentation is checked separately from framebuffer readback.
        idle()
        check(window.chrome.hidden, "Idle controls fade completely")
        check(window.viewport.size() == size, "Fading does not resize viewport")
        after = window.viewport.capture()
        after.save(str(output / "after.png"))
        check(after == before, "Fading leaves captured image pixels unchanged")

        QApplication.sendEvent(
            window.viewport,
            QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(100, 100),
                QPointF(100, 100),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
        wait(100)
        check(not window.chrome.hidden, "Pointer movement reveals controls")
        QCursor.setPos(window.toolbar.mapToGlobal(QPoint(15, 15)))
        wait(2700)
        check(not window.chrome.hidden, "Toolbar hover prevents fading")

        check(window.open_path("artifacts/playback/av.mp4"), "Open video")
        wait(800)
        check(window.controls.isVisible(), "Video shows transport")
        window.pause()
        wait(250)
        frame = window.viewport.capture()
        idle()
        check(window.chrome.hidden, "Video controls fade while idle")
        check(window.viewport.capture() == frame, "Overlays are absent from paused video capture")
        window.controls.volume.setFocus(Qt.FocusReason.TabFocusReason)
        wait(2700)
        check(not window.chrome.hidden, "Keyboard focus reveals controls and prevents fading")
        window.viewport.setFocus()
        window.controls.timeline.setSliderDown(True)
        wait(2700)
        check(not window.chrome.hidden, "Timeline drag prevents fading")
        window.controls.timeline.setSliderDown(False)
        menu = QMenu(window)
        menu.addAction("Probe menu")
        menu.popup(window.mapToGlobal(QPoint(50, 50)))
        wait(2700)
        check(not window.chrome.hidden, "Open menu prevents fading")
        menu.close()
        menu.deleteLater()

        def edit_settings():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, SettingsDialog)
            dialog.repeat.setChecked(True)
            dialog.volume.setValue(17)
            dialog.banner.setValue(1)
            dialog.grab().save(str(output / "settings.png"))
            dialog.accept()

        QTimer.singleShot(100, edit_settings)
        window.settings()
        wait(100)
        check(
            snapshot(window, "loop-file")["loop-file"] == "inf",
            "Settings enable current-file repeat",
        )
        check(
            window.controls.volume.value() == 0, "Default-volume setting preserves current volume"
        )
        restored = Preferences(preferences.path)
        check(
            (restored.repeat, restored.volume, restored.banner_seconds) == (True, 17, 1),
            "Settings persist to the isolated local file",
        )
        second = Window(restored)
        check(second.controls.volume.value() == 17, "New window uses saved default volume")
        second.close()
        window.seek(7.5, "absolute")
        window.pause()
        wait(1500)
        values = snapshot(window, "time-pos", "eof-reached")
        check(
            not values["eof-reached"] and values["time-pos"] < 3,
            "Enabled repeat crosses EOF and restarts the same video",
        )
        window.preferences.repeat = False
        window.video_set("loop-file", "no")
        window.seek(7.5, "absolute")
        wait(1000)
        check(snapshot(window, "eof-reached")["eof-reached"], "Repeat off restores EOF stop")
        window.chrome.reveal()
        for panel, effect, name in zip(
            window.chrome.panels,
            window.chrome.effects,
            ("filename", "toolbar", "transport", "image-dock", "open-media", "folder-browser"),
            strict=True,
        ):
            enabled = effect.isEnabled()
            effect.setEnabled(False)
            panel.grab().save(str(output / f"{name}.png"))
            effect.setEnabled(enabled)
        window.viewport.setFocus()
        QTest.keyClick(window.viewport, Qt.Key.Key_Space)
        wait(200)
        check(not snapshot(window, "pause")["pause"], "Space replays media from EOF")
        QTest.keyClick(window.viewport, Qt.Key.Key_Space)
        wait(200)
        check(snapshot(window, "pause")["pause"], "Space pauses playback")
        idle()
        with patch("amp.app.save_capture", return_value=output / "capture.png") as save:
            QTest.keyClick(window.viewport, Qt.Key.Key_S)
            check(save.called, "S captures while controls are faded")
        window.viewport.transform.zoom_at(100, 100, 2)
        QTest.keyClick(window.viewport, Qt.Key.Key_R)
        check(window.viewport.transform.zoom == 1, "R resets fit through shortcut routing")
        window.controls.volume.setFocus()
        QTest.keyClick(window.controls.volume, Qt.Key.Key_F)
        wait(200)
        check(window.isFullScreen(), "F from a focused slider enters fullscreen")
        QTest.keyClick(window.controls.volume, Qt.Key.Key_Escape)
        wait(200)
        check(not window.isFullScreen(), "Escape leaves fullscreen")
        check(window.open_path("artifacts/playback/tone.wav"), "Open music")
        wait(400)
        check(
            window.controls.isVisible() and not window.actions_by_name["Screenshot"].isEnabled(),
            "Music keeps transport and disables screenshots",
        )
        window.video_set("loop-file", "inf")
        window.seek(7.5, "absolute")
        wait(1500)
        values = snapshot(window, "time-pos", "eof-reached")
        check(
            not values["eof-reached"] and values["time-pos"] < 3,
            "Repeat also restarts the same music file",
        )
        folder = output / "folder"
        folder.mkdir(exist_ok=True)
        before.save(str(folder / "image1.png"))
        before.save(str(folder / "image2.png"))
        window.open_path(folder / "image2.png")
        wait(200)
        size = window.viewport.size()
        QTest.keyClick(window.viewport, Qt.Key.Key_Right)
        wait(200)
        check(window.current_path.name == "image1.png", "Right wraps to first file")
        check(
            window.loop_notice.isVisible() and window.loop_timer.interval() == 1000,
            "Wrap notice uses saved duration",
        )
        check(window.viewport.size() == size, "Wrap notice does not resize media viewport")
        wait(1100)
        check(not window.loop_notice.isVisible(), "Wrap notice expires")
        QTest.keyClick(window.viewport, Qt.Key.Key_Left)
        wait(200)
        check(window.current_path.name == "image2.png", "Left wraps to last file")
        check(not report["errors"], "No backend errors")
        report["passed"] = True
        report["dpr"] = window.viewport.devicePixelRatioF()
    except Exception:  # noqa: BLE001 -- preserve integration failure evidence
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        window.close()
        wait(200)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
