"""Move from transport to fullscreen without clicking, including tooltip dwell."""

import argparse
import json
import time
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QHelpEvent, QImage, QMouseEvent
from PySide6.QtWidgets import QApplication, QToolButton

from amp.app import Window, create_application
from amp.settings import Preferences
from tools.playback_probe import snapshot
from tools.session_probe import wait
from tools.style_probe import compose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/hover"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "isolated.ini")
    preferences.volume, preferences.repeat = 0, False
    window = Window(preferences)
    image_path = output / "Image.png"
    image = QImage(1000, 700, QImage.Format.Format_RGB32)
    image.fill(QColor("#426478"))
    image.save(str(image_path))
    report = {"checks": [], "timings": []}

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    try:
        window.show()
        wait(200)
        button = next(
            b
            for b in window.toolbar.findChildren(QToolButton)
            if b.defaultAction() is window.actions_by_name["Fullscreen"]
        )
        for media, path in (("image", image_path), ("video", Path("artifacts/playback/av.mp4"))):
            window.open_path(path)
            wait(350)
            if media == "video":
                window.video_set("pause", True)
                wait(100)
            for fullscreen in (False, True):
                window.set_fullscreen(fullscreen)
                wait(200)
                before = window.viewport.capture()
                size = window.size()
                window.viewport.setFocus()
                QCursor.setPos(window.viewport.mapToGlobal(QPoint(30, 130)))
                wait(50)
                window.chrome.fade()
                wait(300)
                gaps = []
                last = [time.perf_counter()]
                timer = QTimer()
                timer.setInterval(10)

                def tick(samples=gaps, clock=last):
                    now = time.perf_counter()
                    samples.append(now - clock[0])
                    clock[0] = now

                timer.timeout.connect(tick)
                timer.start()
                start = QPointF(window.viewport.width() / 2, window.viewport.height() - 35)
                end = QPointF(button.mapTo(window.viewport, button.rect().center()))
                for step in range(31):
                    point = start + (end - start) * (step / 30)
                    QApplication.sendEvent(
                        window.viewport,
                        QMouseEvent(
                            QEvent.Type.MouseMove,
                            point,
                            QPointF(window.viewport.mapToGlobal(point.toPoint())),
                            Qt.MouseButton.NoButton,
                            Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier,
                        ),
                    )
                    wait(10)
                QCursor.setPos(button.mapToGlobal(button.rect().center()))
                QApplication.sendEvent(
                    button,
                    QHelpEvent(
                        QEvent.Type.ToolTip,
                        button.rect().center(),
                        button.mapToGlobal(button.rect().center()),
                    ),
                )
                wait(900)
                timer.stop()
                name = f"{media}-{'fullscreen' if fullscreen else 'windowed'}"
                report["timings"].append(
                    {"case": name, "max_event_gap_ms": round(max(gaps, default=0) * 1000, 2)}
                )
                check(
                    window.isFullScreen() == fullscreen
                    and window.size() == size
                    and not window.fullscreen_timer.isActive(),
                    f"{name}: hovering never requests a window transition",
                )
                check(
                    not any(
                        widget.isVisible() and widget.metaObject().className() == "QTipLabel"
                        for widget in QApplication.topLevelWidgets()
                    ),
                    f"{name}: no native tooltip window is created",
                )
                check(
                    all(not effect.isEnabled() for effect in window.chrome.effects),
                    f"{name}: visible controls bypass opacity effects",
                )
                check(
                    window.hover_hint.isVisible() and window.hover_hint.window() is window,
                    f"{name}: fullscreen hint stays inside the existing window",
                )
                check(
                    window.viewport.capture() == before,
                    f"{name}: hover leaves the media framebuffer unchanged",
                )
                compose(window, output / f"{name}.png")
        window.set_fullscreen(False)
        wait(200)
        window.video_set("pause", False)
        before = snapshot(window, "time-pos")["time-pos"]
        QApplication.sendEvent(
            button,
            QHelpEvent(
                QEvent.Type.ToolTip,
                button.rect().center(),
                button.mapToGlobal(button.rect().center()),
            ),
        )
        wait(600)
        check(
            not snapshot(window, "pause")["pause"]
            and snapshot(window, "time-pos")["time-pos"] > before,
            "Video continues playing while the fullscreen hint is visible",
        )
        report["passed"] = True
        report["dpr"] = window.viewport.devicePixelRatioF()
    finally:
        window.close()
        wait(100)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
