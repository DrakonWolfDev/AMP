"""Live corrupt-media traversal, stale-error and bounded-loop regression checks."""

import json
import traceback
from pathlib import Path

from PySide6.QtGui import QColor, QImage

from amp.app import Window, create_application
from tools.session_probe import wait


def main():
    output = Path("artifacts/navigation")
    output.mkdir(parents=True, exist_ok=True)
    mixed = output / "mixed"
    broken = output / "broken"
    for directory in (mixed, broken):
        directory.mkdir(exist_ok=True)
    image = QImage(320, 240, QImage.Format.Format_RGB32)
    image.fill(QColor("#368dad"))
    for name in ("file1.png", "file5.png"):
        image.save(str(mixed / name))
    for name in ("file2.mp4", "file3.mp3", "file4.png"):
        (mixed / name).write_bytes(b"deliberately corrupt media")
    for name in ("bad1.mp4", "bad2.mp3", "bad3.png"):
        (broken / name).write_bytes(b"deliberately corrupt media")
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    window = Window()
    window.show()
    report = {"checks": [], "errors": []}
    window.viewport.failed.connect(lambda message: report["errors"].append(message))

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    try:
        wait(200)
        window.open_path(mixed / "file1.png")
        window.navigate(1)
        wait(2200)
        check(
            window.current_path.name == "file5.png", "Forward skips corrupt video, music and image"
        )
        check("Skipped 3" in window.statusBar().currentMessage(), "All skipped files are reported")
        window.navigate(-1)
        wait(800)
        check(window.current_path.name == "file1.png", "Backward skips corrupt media")
        window.navigate(-1)
        check(
            window.current_path.name == "file5.png" and window.loop_notice.isVisible(),
            "Backward wrap keeps visible notice",
        )
        wait(3200)
        check(not window.loop_notice.isVisible(), "Loop notice expires after three seconds")
        window.open_path(broken / "bad1.mp4")
        wait(400)
        check(
            "could not be decoded" in window.statusBar().currentMessage(),
            "Direct corrupt-file open reports actionable error",
        )
        window.navigate(1)
        wait(600)
        serial = window.viewport.load_serial
        check(
            window.navigation_attempt is None
            and "No other readable" in window.statusBar().currentMessage(),
            "All-broken folder stops after one bounded traversal",
        )
        wait(500)
        check(window.viewport.load_serial == serial, "All-broken folder does not spin or reload")
        window.open_path(mixed / "file2.mp4")
        stale = window.viewport.load_serial
        window.open_path(mixed / "file1.png")
        message = window.statusBar().currentMessage()
        window.viewport._load_failed(stale, "Stale decoder failure")
        wait(500)
        check(
            window.current_path.name == "file1.png"
            and window.statusBar().currentMessage() == message,
            "Late decoder failure cannot replace a newly opened image",
        )
        check(not report["errors"], "No unexpected command or backend errors")
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
