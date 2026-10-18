"""Execute a real GL/video/capture smoke test: python -m tools.render_probe."""

import argparse
import hashlib
import json
import subprocess
import traceback
from pathlib import Path

import imageio_ffmpeg
from OpenGL import GL
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QImage, QPainter

from amp.app import Window, create_application


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/probe"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    video = output / "moving.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=640x360:rate=30",
            "-t",
            "12",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    image = QImage(400, 800, QImage.Format.Format_RGB32)
    image.fill(QColor("#efc42e"))
    painter = QPainter(image)
    painter.fillRect(0, 0, 200, 400, QColor("#e24040"))
    painter.fillRect(200, 400, 200, 400, QColor("#237ed0"))
    painter.end()
    image.save(str(output / "portrait.png"))
    app = create_application()
    window = Window()
    window.resize(800, 600)
    window.show()
    viewport = window.viewport
    report = {"captures": [], "errors": []}
    viewport.failed.connect(lambda message: report["errors"].append(message))

    def capture(name):
        count_before = viewport.render_count
        image = viewport.capture()
        assert viewport.render_count == count_before, "Capture triggered a newer video render"
        destination = output / f"{name}.png"
        assert image.save(str(destination))
        record = {
            "name": name,
            "logical": [viewport.width(), viewport.height()],
            "dpr": viewport.devicePixelRatioF(),
            "actual": [image.width(), image.height()],
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "render_count": viewport.render_count,
        }
        report["captures"].append(record)
        print(json.dumps(record), flush=True)

    def image_open():
        viewport.open_image(output / "portrait.png")

    def image_zoom():
        capture("image-fit")
        viewport.transform.zoom_at(320, 240, 2)
        viewport.transform.pan(-50, 60)
        viewport.apply_transform()

    def video_open():
        capture("image-zoom")
        viewport.open_video(video.resolve())

    def video_zoom():
        viewport.makeCurrent()
        report["gl_renderer"] = GL.glGetString(GL.GL_RENDERER).decode()
        report["gl_version"] = GL.glGetString(GL.GL_VERSION).decode()
        viewport.doneCurrent()
        report["mpv"] = viewport.backend.version
        capture("video-playing-fit")
        viewport.transform.zoom_at(220, 210, 2)
        viewport.transform.pan(-70, 40)
        viewport.apply_transform()

    def pause():
        capture("video-playing-zoom")
        viewport.backend.set("pause", True)

    def seek_resize():
        capture("video-paused-zoom")
        # Paused FBO readback must match Qt's own framebuffer capture exactly.
        actual = viewport.capture().convertToFormat(QImage.Format.Format_RGBA8888)
        qt_capture = viewport.grabFramebuffer().convertToFormat(QImage.Format.Format_RGBA8888)
        assert actual == qt_capture, (
            f"Direct FBO capture {actual.size()} differs from Qt framebuffer {qt_capture.size()}"
        )
        viewport.backend.command("seek", 5, "absolute")
        window.resize(900, 650)

    def resume():
        capture("video-paused-resized")
        viewport.backend.set("pause", False)

    def finish():
        capture("video-resumed")
        assert viewport.render_count > 20, "No sustained video rendering"
        assert report["captures"][2]["sha256"] != report["captures"][3]["sha256"]
        viewport.open_image(output / "portrait.png")
        window.close()
        report["passed"] = not report["errors"]
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        app.exit(0 if report["passed"] else 1)

    def guarded(fn):
        def run():
            try:
                fn()
            except Exception:  # noqa: BLE001 -- record every probe failure before exiting
                report["errors"].append(traceback.format_exc())
                print(report["errors"][-1], flush=True)
                (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                window.close()
                app.exit(1)

        return run

    for delay, fn in [
        (200, image_open),
        (600, image_zoom),
        (1000, video_open),
        (3000, video_zoom),
        (4000, pause),
        (4800, seek_resize),
        (5800, resume),
        (6800, finish),
    ]:
        QTimer.singleShot(delay, guarded(fn))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
