"""Bounded M8 two-process playback/capture/normal-shutdown probe.

The JSON command/heartbeat files belong only to this test harness, not AMP.
Run playback_probe first to create the video fixture. No output is audible.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QTimer

from amp.app import Window, create_application
from amp.capture import save_capture
from amp.settings import Preferences


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    # Windows readers can briefly deny replacement while a heartbeat is open.
    for attempt in range(20):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.01)


def worker(folder):
    app = create_application()
    preferences = Preferences(folder / "preferences.ini")
    preferences.save(False, 0, 3)
    window = Window(preferences)
    window.controls.mute.setChecked(True)
    state = {"pid": os.getpid(), "errors": [], "last_command": 0}
    window.viewport.failed.connect(state["errors"].append)
    window.show()
    report_path = folder / "state.json"
    command_path = folder / "command.json"

    def tick():
        try:
            if command_path.exists():
                command = json.loads(command_path.read_text(encoding="utf-8"))
                if command["id"] > state["last_command"]:
                    state["last_command"] = command["id"]
                    action = command["action"]
                    if action == "pause":
                        window.pause()
                        window.seek(2, "absolute")
                        window.controls.volume.setValue(21)
                        window.viewport.transform.zoom_at(250, 200, 2)
                        window.viewport.apply_transform()
                    elif action == "capture":
                        state["capture"] = str(
                            save_capture(window.viewport.capture(), folder / "captures")
                        )
                    elif action == "close":
                        timer.stop()
                        window.close()
                        return
            backend = window.viewport.backend
            if backend:

                def read():
                    return {
                        name: backend.player._get_property(name)
                        for name in ("pause", "time-pos", "volume", "mute")
                    }

                state.update(backend.worker.submit(read).result(timeout=2))
            state.update(
                renders=window.viewport.render_count,
                zoom=window.viewport.transform.zoom,
                path=str(window.current_path),
                heartbeat=time.monotonic(),
            )
            write_json(report_path, state)
        except Exception:  # noqa: BLE001 -- preserve worker failure and exit normally
            state["errors"].append(traceback.format_exc())
            timer.stop()
            window.close()

    def open_media():
        window.open_path(folder / "file1.mp4")
        window.video_set("loop-file", "inf")

    timer = QTimer()
    timer.setInterval(150)
    timer.timeout.connect(tick)
    timer.start()
    QTimer.singleShot(250, open_media)
    QTimer.singleShot(25000, window.close)
    app.exec()
    state["closed"] = True
    state["remaining_threads"] = [
        t.name
        for t in threading.enumerate()
        if t.name.startswith("amp-mpv") or t.name == "MPVEventHandlerThread"
    ]
    write_json(report_path, state)
    return 0 if not state["errors"] and not state["remaining_threads"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    output = Path("artifacts/processes")
    report = {"checks": [], "errors": [], "pids": []}
    processes = []
    logs = []

    def read(folder):
        path = folder / "state.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def until(predicate, seconds=8):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.05)
        raise AssertionError("Timed out waiting for process state")

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    try:
        folders = [output / "first", output / "second"]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile("artifacts/playback/av.mp4", folder / "file1.mp4")
            for filename in ("state.json", "command.json"):
                (folder / filename).unlink(missing_ok=True)
            log = (folder / "process.log").open("w", encoding="utf-8")
            logs.append(log)
            processes.append(
                subprocess.Popen(
                    [sys.executable, "-m", "tools.process_probe", "--worker", str(folder)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            )
        first, second = folders
        until(lambda: all(read(f).get("renders", 0) > 3 for f in folders))
        report["pids"] = [read(f)["pid"] for f in folders]
        check(
            len(set(report["pids"])) == 2 and all(p.poll() is None for p in processes),
            "Two independent AMP application processes render concurrently",
        )
        write_json(first / "command.json", {"id": 1, "action": "pause"})
        until(lambda: read(first).get("pause") and read(first).get("volume") == 21)
        check(
            read(first)["zoom"] == 2
            and read(second)["zoom"] == 1
            and read(second)["volume"] == 0
            and not read(second)["pause"],
            "Pause, seek, volume and transform changes do not cross processes",
        )
        check(
            abs(read(first)["time-pos"] - 2) < 0.3 and not read(second)["pause"],
            "First process seeks to two seconds while second remains in playback",
        )
        for folder in folders:
            write_json(folder / "command.json", {"id": 2, "action": "capture"})
        until(lambda: all(read(f).get("capture") for f in folders))
        check(
            all(Path(read(f)["capture"]).is_file() for f in folders),
            "Both processes save their own rendered viewport PNG",
        )
        before = read(second)["renders"]
        write_json(first / "command.json", {"id": 3, "action": "close"})
        until(lambda: processes[0].poll() is not None)
        until(lambda: read(second)["renders"] > before + 5)
        check(
            processes[0].returncode == 0 and processes[1].poll() is None,
            "Normal exit of first process leaves the other video rendering",
        )
        write_json(second / "command.json", {"id": 3, "action": "close"})
        until(lambda: processes[1].poll() is not None)
        check(
            processes[1].returncode == 0
            and all(
                read(f).get("closed") and not read(f)["remaining_threads"] and not read(f)["errors"]
                for f in folders
            ),
            "Both processes exit normally with no mpv threads or backend errors",
        )
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- preserve failures before bounded child cleanup
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        for log in logs:
            log.close()
        write_json(output / "process-report.json", report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
