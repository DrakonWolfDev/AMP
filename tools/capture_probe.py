"""Quantitative M5/M6 framebuffer, transform and save/retry checks."""

import argparse
import hashlib
import json
import subprocess
import traceback
from pathlib import Path
from unittest.mock import patch

import imageio_ffmpeg
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp.app import Window, create_application
from amp.capture import pictures_directory, save_capture
from tools.image_fixtures import quadrants
from tools.playback_probe import snapshot
from tools.session_probe import wait


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/capture"))
    parser.add_argument(
        "--native-pictures",
        action="store_true",
        help="also save two real verification PNGs to OS Pictures/AMP",
    )
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fixtures = []
    for name, size in (("landscape", (800, 400)), ("portrait", (400, 800))):
        image_path = output / f"{name}.png"
        video_path = output / f"{name}.mp4"
        quadrants(size).save(image_path)
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                str(image_path),
                "-t",
                "30",
                "-r",
                "15",
                "-c:v",
                "libx264",
                "-crf",
                "12",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=out_color_matrix=bt709",
                "-colorspace",
                "bt709",
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                str(video_path),
            ],
            check=True,
            capture_output=True,
        )
        fixtures.extend((image_path, video_path))
    original_hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures}
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    window = Window()
    window.controls.volume.setValue(0)
    window.resize(820, 640)
    window.show()
    viewport = window.viewport
    report = {"checks": [], "captures": [], "errors": [], "native_captures": []}
    viewport.failed.connect(lambda message: report["errors"].append(message))

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    def capture_and_compare(name, source):
        count = viewport.render_count
        actual = viewport.capture()
        check(viewport.render_count == count, f"{name}: capture does not render a new video frame")
        check(actual == viewport.capture(), f"{name}: consecutive reads preserve displayed pixels")
        expected = QImage(actual.size(), QImage.Format.Format_RGBA8888)
        expected.fill(Qt.GlobalColor.black)
        expected.setDevicePixelRatio(viewport.devicePixelRatioF())
        painter = QPainter(expected)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(QRectF(*viewport.transform.rect), QImage(str(source)))
        painter.end()
        errors = []
        # Known uniform regions avoid measuring JPEG/YUV edge interpolation.
        for fy in (0.07, 0.23, 0.37, 0.63, 0.77, 0.93):
            for fx in (0.07, 0.23, 0.37, 0.63, 0.77, 0.93):
                x, y = int(fx * actual.width()), int(fy * actual.height())
                a, e = actual.pixelColor(x, y), expected.pixelColor(x, y)
                errors.append(
                    max(
                        abs(a.red() - e.red()), abs(a.green() - e.green()), abs(a.blue() - e.blue())
                    )
                )
        if max(errors) >= 25:
            actual.save(str(output / f"failed-{name}.png"))
            expected.save(str(output / f"expected-{name}.png"))
            print(
                {
                    "rect": viewport.transform.rect,
                    "sample_error": max(errors),
                    "core": snapshot(
                        window, "video-out-params", "video-zoom", "video-pan-x", "video-pan-y"
                    ),
                },
                flush=True,
            )
        check(max(errors) < 25, f"{name}: media crop/pan/zoom/bars match reference composition")
        check(
            actual.size() == viewport.size() * viewport.devicePixelRatioF(),
            f"{name}: physical dimensions exclude toolbar/title/status",
        )
        actual.save(str(output / f"view-{name}.png"))
        report["captures"].append(
            {
                "name": name,
                "logical": [viewport.width(), viewport.height()],
                "dpr": viewport.devicePixelRatioF(),
                "actual": [actual.width(), actual.height()],
                "max_sample_error": max(errors),
            }
        )

    def wheel_at(x, y, steps):
        point = QPointF(x, y)
        event = QWheelEvent(
            point,
            point,
            QPoint(),
            QPoint(0, steps * 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        QApplication.sendEvent(viewport, event)

    try:
        wait(200)
        window.open_path(output / "landscape.png")
        try:
            viewport.capture()
        except RuntimeError as error:
            check(
                "updating" in str(error),
                "Capture refuses stale pixels immediately after media switch",
            )
        else:
            raise AssertionError("Captured old media before first new paint")
        window.screenshot()
        check(
            window.pending_capture is None
            and "updating" in window.statusBar().currentMessage()
            and "retained" not in window.statusBar().currentMessage(),
            "Pre-render screenshot failure does not claim a retained frame exists",
        )
        wait(100)
        capture_and_compare("image-fit", output / "landscape.png")
        wheel_at(viewport.width() * 0.65, viewport.height() * 0.4, 2)
        viewport.transform.pan(-40, 35)
        viewport.apply_transform()
        wait(100)
        capture_and_compare("image-zoom-pan", output / "landscape.png")
        for name in ("landscape", "portrait"):
            source = output / f"{name}.png"
            window.open_path(output / f"{name}.mp4")
            wait(1000)
            capture_and_compare(f"{name}-video-fit", source)
            x, y, w, h = viewport.transform.rect
            wheel_at(x + 0.65 * w, y + 0.4 * h, 1)
            wait(150)
            capture_and_compare(f"{name}-video-letterbox-zoom", source)
            wheel_at(viewport.width() * 0.6, viewport.height() * 0.4, 4)
            QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=QPoint(350, 250))
            QTest.mouseMove(viewport, QPoint(300, 280))
            QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=QPoint(300, 280))
            wait(200)
            capture_and_compare(f"{name}-video-playing-pan", source)
            window.pause()
            wait(100)
            window.seek(3, "absolute")
            wait(150)
            capture_and_compare(f"{name}-video-paused-seek", source)
            window.resize(930, 710)
            wait(150)
            capture_and_compare(f"{name}-video-resized", source)
            viewport.reset()
            wait(150)
            capture_and_compare(f"{name}-video-reset", source)
        with patch(
            "amp.app.save_capture", side_effect=PermissionError("Test output is unwritable")
        ):
            window.screenshot()
        retained = window.pending_capture.copy()
        check(
            not retained.isNull() and "Screenshot failed" in window.statusBar().currentMessage(),
            "Save failure retains exact frame and shows an actionable error",
        )
        window.open_path(output / "landscape.png")
        wait(100)
        saved = []

        def retry(image):
            path = save_capture(image, output / "retried")
            saved.append(path)
            return path

        with patch("amp.app.save_capture", side_effect=retry):
            window.screenshot()
        check(
            window.pending_capture is None
            and QImage(str(saved[0])).convertToFormat(QImage.Format.Format_RGBA8888)
            == retained.convertToFormat(QImage.Format.Format_RGBA8888),
            "Retry saves retained frame even after visible media changes",
        )
        if args.native_pictures:
            directory = pictures_directory()
            before = set(directory.glob("AMP_*.png")) if directory.exists() else set()
            window.actions_by_name["Screenshot"].trigger()
            window.activateWindow()
            viewport.setFocus()
            wait(100)
            QTest.keyClick(viewport, Qt.Key.Key_S)
            added = set(directory.glob("AMP_*.png")) - before
            check(
                len(added) == 2,
                "Screenshot button and S save two collision-safe PNGs in OS Pictures/AMP",
            )
            check(
                all(
                    QImage(str(path)).size() == viewport.size() * viewport.devicePixelRatioF()
                    for path in added
                ),
                "Native Pictures PNGs have exact viewport dimensions",
            )
            report["native_captures"] = sorted(p.name for p in added)
        check(
            all(
                hashlib.sha256(p.read_bytes()).hexdigest() == digest
                for p, digest in original_hashes.items()
            ),
            "Original media fixtures remain byte-for-byte unchanged",
        )
        check(not report["errors"], "No unexpected backend errors")
        window.close()
        wait(100)
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- record every integration failure
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
        window.close()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
