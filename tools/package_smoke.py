"""Standalone installed-wheel smoke test using runtime dependencies only."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import threading
import traceback
from contextlib import suppress
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtGui import QColor, QImage

import amp
from amp.app import Window, create_application
from amp.capture import save_capture
from amp.settings import Preferences


def wait(milliseconds):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--music", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "unused-preferences.ini")
    preferences.volume, preferences.repeat = 0, False
    first, second = Window(preferences), Window(preferences)
    report = {
        "checks": [],
        "errors": [],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "amp_module": str(Path(amp.__file__).resolve()),
        "packages": sorted(
            (d.metadata["Name"], d.version) for d in importlib.metadata.distributions()
        ),
    }
    for window in (first, second):
        window.viewport.failed.connect(report["errors"].append)

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def core(window, names):
        backend = window.viewport.backend

        def read():
            result = {}
            for name in names:
                try:
                    result[name] = backend.player._get_property(name)
                except AttributeError:
                    result[name] = None
            return result

        return backend.worker.submit(read).result(timeout=3)

    try:
        first.show()
        second.show()
        wait(300)
        check(first.viewport.isValid(), "Blank installed application creates a valid GL viewport")
        package_names = {name.lower().replace("_", "-") for name, _ in report["packages"]}
        check(
            getattr(sys, "frozen", False)
            or package_names
            == {
                "pip",
                "andy-media-player",
                "pyside6-essentials",
                "shiboken6",
                "python-mpv",
                "pyopengl",
                "mutagen",
            },
            "Frozen executable carries runtime package metadata"
            if getattr(sys, "frozen", False)
            else "Fresh environment contains only pip, AMP and five runtime distributions",
        )
        image = QImage(300, 500, QImage.Format.Format_RGB32)
        image.fill(QColor("#337788"))
        image_path = output / "portrait.png"
        image.save(str(image_path))
        check(first.open_path(image_path), "Installed wheel decodes a still image")
        wait(200)
        frame = first.viewport.capture()
        check(
            frame.size() == first.viewport.size() * first.viewport.devicePixelRatioF(),
            "Installed image capture has physical viewport dimensions",
        )
        check(first.open_path(args.video), "Installed wheel opens H.264/AAC video")
        first.video_set("mute", True)
        check(second.open_path(args.video), "A second installed window opens video independently")
        second.video_set("mute", True)
        wait(900)
        check(
            first.viewport.render_count > 3 and second.viewport.render_count > 3,
            "Minimal runtime renders two live videos without Qt Addons",
        )
        first.pause()
        first.seek(2, "absolute")
        wait(200)
        check(
            core(first, ("pause",))["pause"] and not core(second, ("pause",))["pause"],
            "Installed-window playback remains independent",
        )
        first.viewport.transform.zoom_at(200, 200, 2)
        first.viewport.apply_transform()
        first.showFullScreen()
        wait(200)
        first.showNormal()
        first.resize(820, 590)
        wait(200)
        path = save_capture(first.viewport.capture(), output / "captures")
        check(path.is_file(), "Installed viewport capture survives zoom/fullscreen/resize")
        report["runtime"] = core(first, ("mpv-version", "ffmpeg-version", "mpv-configuration"))
        dll = Path(os.environ.get("AMP_MPV_DIR", "")) / "libmpv-2.dll"
        if dll.is_file():
            report["libmpv_sha256"] = hashlib.sha256(dll.read_bytes()).hexdigest()
        check(first.open_path(args.music), "Installed wheel opens local music")
        wait(400)
        check(
            first.viewport.audio and core(first, ("time-pos",))["time-pos"] > 0,
            "Installed music playback advances",
        )
        count = second.viewport.render_count
        first.close()
        wait(200)
        check(
            second.viewport.render_count > count, "Installed second window survives first closing"
        )
        second.close()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        wait(100)
        remaining = [
            t.name
            for t in threading.enumerate()
            if t.name.startswith("amp-mpv") or t.name == "MPVEventHandlerThread"
        ]
        check(
            not remaining and not report["errors"],
            "Installed application shuts down all decoder threads cleanly",
        )
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- standalone machine-readable install evidence
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        for window in (first, second):
            with suppress(RuntimeError):
                window.close()
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
