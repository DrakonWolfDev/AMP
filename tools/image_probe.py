"""Real image viewport/input regression checks; requires a visible desktop."""

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp import app as app_module
from amp.app import Window, create_application
from tools.image_fixtures import COLORS, ORIENTED_CORNERS, oriented_jpeg, quadrants
from tools.session_probe import wait


def cli_check(path):
    original = app_module.create_application

    def factory():
        app = original()

        def verify():
            windows = [w for w in app.topLevelWidgets() if isinstance(w, Window)]
            passed = bool(
                windows
                and windows[0].current_path == path.resolve()
                and not windows[0].viewport.image.isNull()
            )
            (path.parent / "cli-report.json").write_text(json.dumps({"passed": passed}))
            for window in windows:
                window.close()
            app.exit(0 if passed else 1)

        QTimer.singleShot(500, verify)
        return app

    app_module.create_application = factory
    sys.argv = ["amp", str(path)]
    return app_module.main()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli-check", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/images"))
    args = parser.parse_args()
    if args.cli_check:
        return cli_check(args.cli_check)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    for name, size in (
        ("portrait.png", (300, 1200)),
        ("ultrawide.png", (2400, 300)),
        ("large.png", (6000, 4000)),
    ):
        quadrants(size).save(output / name)
    for orientation in range(1, 9):
        oriented_jpeg(output / f"exif{orientation}.jpg", orientation)
    for suffix, format in (
        ("jfif", "JPEG"),
        ("gif", "GIF"),
        ("tiff", "TIFF"),
        ("webp", "WEBP"),
        ("bmp", "BMP"),
    ):
        quadrants().save(output / f"sample.{suffix}", format=format)
    transparent = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    ImageDraw.Draw(transparent).rectangle((100, 100, 300, 300), fill=(230, 30, 30, 255))
    transparent.save(output / "alpha.png")
    subprocess.run(
        [sys.executable, "-m", "tools.image_probe", "--cli-check", str(output / "portrait.png")],
        check=True,
        timeout=20,
    )
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    window = Window()
    window.resize(820, 650)
    window.show()
    report = {"checks": ["Actual CLI entry point opens local image"], "captures": [], "errors": []}

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    def inspect_quadrants(name, order=(0, 1, 2, 3)):
        viewport = window.viewport
        frame = viewport.capture()
        x, y, w, h = viewport.transform.rect
        dpr = viewport.devicePixelRatioF()
        for (fx, fy), index in zip(
            ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)), order, strict=True
        ):
            actual = frame.pixelColor(
                round((x + fx * w) * dpr), round((y + fy * h) * dpr)
            ).getRgb()[:3]
            check(
                all(abs(a - b) < 20 for a, b in zip(actual, COLORS[index], strict=True)),
                f"{name} quadrant {index} has expected rendered colour",
            )
        physical = viewport.size() * dpr
        check(frame.size() == physical, f"{name} capture uses physical viewport dimensions")
        check(frame.pixelColor(0, 0).red() < 5, f"{name} letterboxing is black")
        frame.save(str(output / f"capture-{name}.png"))
        report["captures"].append(
            {
                "name": name,
                "logical": [viewport.width(), viewport.height()],
                "dpr": dpr,
                "actual": [frame.width(), frame.height()],
            }
        )

    try:
        wait(200)
        for name in ("portrait.png", "ultrawide.png", "large.png"):
            check(window.open_path(output / name), f"Open {name}")
            wait(200)
            inspect_quadrants(Path(name).stem)
        for orientation in range(1, 9):
            check(window.open_path(output / f"exif{orientation}.jpg"), f"Open EXIF {orientation}")
            wait(80)
            inspect_quadrants(f"exif{orientation}", ORIENTED_CORNERS[orientation])
        for suffix in ("jfif", "gif", "tiff", "webp", "bmp"):
            check(window.open_path(output / f"sample.{suffix}"), f"Open {suffix} in viewer")
            wait(80)
            inspect_quadrants(suffix)
        for name in ("portrait.png", "ultrawide.png"):
            window.open_path(output / name)
            wait(80)
            viewport = window.viewport
            x, y, w, h = viewport.transform.rect
            point = QPointF(x + 0.7 * w, y + 0.6 * h)
            wheel = QWheelEvent(
                point,
                point,
                QPoint(),
                QPoint(0, 120),
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.NoScrollPhase,
                False,
            )
            QApplication.sendEvent(viewport, wheel)
            x, y, w, h = viewport.transform.rect
            check(
                abs(x + 0.7 * w - point.x()) < 0.01 and abs(y + 0.6 * h - point.y()) < 0.01,
                f"{name} wheel zoom anchors detail despite letterboxing",
            )
        window.open_path(output / "alpha.png")
        wait(100)
        frame = window.viewport.capture()
        check(
            frame.pixelColor(frame.width() // 2, frame.height() // 2).red() > 200,
            "Transparent PNG renders its opaque content",
        )
        x, y, w, h = window.viewport.transform.rect
        dpr = window.viewport.devicePixelRatioF()
        check(
            frame.pixelColor(round((x + 0.1 * w) * dpr), round((y + 0.1 * h) * dpr)).red() < 5,
            "Transparent PNG composites onto black",
        )
        viewport = window.viewport
        viewport.setFocus()
        position = QPointF(viewport.width() / 2, viewport.height() / 2)
        wheel = QWheelEvent(
            position,
            position,
            QPoint(),
            QPoint(0, 360),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        QApplication.sendEvent(viewport, wheel)
        check(viewport.transform.zoom > 1, "Actual wheel input zooms image")
        QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=QPoint(300, 250))
        QTest.mouseMove(viewport, QPoint(340, 280))
        QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=QPoint(340, 280))
        check(viewport.transform.pan_x != 0, "Actual mouse drag pans enlarged image")
        x, y, w, h = viewport.transform.rect
        centre = ((viewport.width() / 2 - x) / w, (viewport.height() / 2 - y) / h)
        zoom = viewport.transform.zoom
        window.resize(940, 720)
        wait(150)
        x, y, w, h = viewport.transform.rect
        resized = ((viewport.width() / 2 - x) / w, (viewport.height() / 2 - y) / h)
        check(
            all(abs(a - b) < 0.001 for a, b in zip(centre, resized, strict=True))
            and viewport.transform.zoom == zoom,
            "Zoomed resize preserves centred image detail",
        )
        check(
            viewport.capture().size() == viewport.size() * viewport.devicePixelRatioF(),
            "Resized image capture matches physical viewport",
        )
        QTest.mouseClick(viewport, Qt.MouseButton.MiddleButton)
        check(
            viewport.transform.zoom == 1 and viewport.transform.pan_x == 0,
            "Middle click restores fit",
        )
        viewport.transform.zoom_at(position.x(), position.y(), 2)
        viewport.apply_transform()
        QTest.keyClick(viewport, Qt.Key.Key_R)
        check(viewport.transform.zoom == 1, "R shortcut restores fit")
        QTest.mouseDClick(viewport, Qt.MouseButton.LeftButton)
        wait(200)
        check(window.isFullScreen(), "Double click enters fullscreen")
        QTest.keyClick(viewport, Qt.Key.Key_Escape)
        wait(200)
        check(not window.isFullScreen(), "Escape exits fullscreen")
        with patch(
            "amp.app.QFileDialog.getOpenFileName", return_value=(str(output / "portrait.png"), "")
        ) as chooser:
            window.choose()
            check(window.current_path.name == "portrait.png", "File picker selection opens image")
            check("*.tiff" in chooser.call_args.args[3], "Picker lists supported media filters")
        with patch("amp.app.QFileDialog.getOpenFileName", return_value=("", "")):
            window.choose()
            check(
                window.current_path.name == "portrait.png", "Cancelled picker keeps current media"
            )
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str((output / "ultrawide.png").resolve()))])
        enter = QDragEnterEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(window, enter)
        drop = QDropEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(window, drop)
        check(
            drop.isAccepted() and window.current_path.name == "ultrawide.png",
            "Actual local-file drag/drop events open image",
        )
        mime.setUrls([QUrl("https://example.invalid/image.png")])
        remote = QDragEnterEvent(
            QPointF(100, 100),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(window, remote)
        check(not remote.isAccepted(), "Remote URL drag is rejected")
        report["passed"] = True
        window.close()
        wait(100)
    except Exception:  # noqa: BLE001 -- record all desktop probe failures
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
        window.close()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
