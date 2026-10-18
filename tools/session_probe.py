"""Real window/control/navigation/isolation checks, following render_probe."""

import json
import shutil
import subprocess
import traceback
from contextlib import suppress
from pathlib import Path

import imageio_ffmpeg
from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtTest import QTest

from amp.app import Window, create_application
from amp.capture import save_capture


def wait(milliseconds):
    # Enter a real event loop so libmpv's Python callbacks can acquire the GIL.
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main():
    output = Path("artifacts/session")
    output.mkdir(parents=True, exist_ok=True)
    source = Path("artifacts/probe")
    for name in ("clip2.mp4", "clip10.mp4"):
        shutil.copyfile(source / "moving.mp4", output / name)
    shutil.copyfile(source / "portrait.png", output / "image.png")
    (output / "clip3.png").write_bytes(b"corrupt image")
    (output / "notes.txt").write_text("not media")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for filename, codec in (("sample.mkv", "copy"), ("sample.webm", "libvpx-vp9")):
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source / "moving.mp4"),
                "-t",
                "3",
                "-c:v",
                codec,
                str(output / filename),
            ],
            check=True,
            capture_output=True,
        )
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    windows = []
    report = {"checks": [], "errors": []}

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    try:
        first = Window()
        first.viewport.failed.connect(lambda message: report["errors"].append(message))
        windows.append(first)
        first.show()
        wait(250)
        check(first.open_path(output / "clip2.mp4"), "Open H.264 MP4 through application")
        wait(3000)
        print(first.statusBar().currentMessage(), flush=True)
        check(first.viewport.render_count > 5, "H.264 playback produces live frames")
        check(first.controls.duration > 10, "Duration arrives in visible controls")
        first.pause()
        wait(250)
        check(first.controls.play.text() == "Play", "Pause control updates")
        first.seek(5, "absolute")
        wait(300)
        check(abs(first.controls.position - 5) < 1, "Absolute seek updates timeline")
        first.new_window()
        second = app.amp_windows[-1]
        windows.append(second)
        wait(250)
        check(second.open_path(source / "moving.mp4"), "Open second video in another folder")
        wait(1200)
        check(
            second.viewport.backend.player is not first.viewport.backend.player,
            "Windows own distinct mpv cores",
        )
        first.controls.volume.setValue(20)
        first.viewport.transform.zoom_at(320, 240, 2)
        first.viewport.apply_transform()
        wait(200)
        check(
            second.viewport.transform.zoom == 1 and second.controls.volume.value() == 100,
            "Zoom and volume stay independent",
        )
        check(second.controls.play.text() == "Pause", "Second video plays while first is paused")
        before = first.current_path
        QTest.keyClick(first.controls.timeline, Qt.Key.Key_Right)
        wait(500)
        check(
            first.current_path.name == "clip10.mp4" and before.name == "clip2.mp4",
            "Right over timeline navigates files and skips corrupt image",
        )
        check(first.viewport.transform.zoom == 1, "New media resets fit")
        for suffix in ("mkv", "webm"):
            count = first.viewport.render_count
            check(first.open_path(output / f"sample.{suffix}"), f"Open {suffix}")
            wait(1000)
            check(first.viewport.render_count > count + 5, f"Live {suffix} playback")
        first.showFullScreen()
        wait(250)
        QTest.keyClick(first.viewport, Qt.Key.Key_Escape)
        wait(250)
        check(not first.isFullScreen(), "Escape leaves fullscreen")
        for window, name in ((first, "first"), (second, "second")):
            check(
                save_capture(window.viewport.capture(), output / "captures").is_file(),
                f"Independent {name} viewport PNG",
            )
        count = second.viewport.render_count
        first.close()
        wait(600)
        check(second.viewport.render_count > count, "Second video survives first window shutdown")
        second.close()
        wait(100)
        check(not report["errors"], "No unexpected decoder or backend errors")
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- the probe records any failure
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        for window in windows:
            # Qt may already have deleted a successfully closed window.
            with suppress(RuntimeError):
                window.close()
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
