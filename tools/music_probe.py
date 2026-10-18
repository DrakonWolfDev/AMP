"""Real audio decoding/transport and folder-loop UI checks."""

import json
import subprocess
import traceback
from pathlib import Path

import imageio_ffmpeg

from amp.app import Window, create_application
from tools.session_probe import wait


def main():
    output = Path("artifacts/music")
    output.mkdir(parents=True, exist_ok=True)
    (output / "ui").mkdir(exist_ok=True)
    # Keep generated UI previews out of the directory whose media order is tested.
    for name in ("music-window.png", "loop-notice.png"):
        (output / name).unlink(missing_ok=True)
    (output / "aaa.png").write_bytes(b"corrupt first image")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    for suffix in ("wav", "mp3", "flac", "ogg", "opus", "m4a", "aac", "wma", "aiff"):
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000",
                "-t",
                "4",
                str(output / f"tone.{suffix}"),
            ],
            check=True,
            capture_output=True,
        )
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    window = Window()
    window.show()
    window.controls.volume.setValue(0)
    report = {"checks": [], "errors": []}
    window.viewport.failed.connect(lambda message: report["errors"].append(message))

    def check(condition, label):
        assert condition, label
        report["checks"].append(label)
        print(label, flush=True)

    try:
        wait(250)
        for suffix in ("wav", "mp3", "flac", "ogg", "opus", "m4a", "aac", "wma", "aiff"):
            check(window.open_path(output / f"tone.{suffix}"), f"Open {suffix}")
            wait(1000)
            check(
                window.controls.position > 0.1 and window.controls.duration > 2,
                f"{suffix} audio decoding advances playback",
            )
        check(
            window.controls.isVisible() and window.viewport.audio and not window.viewport.video,
            "Music mode exposes transport without video",
        )
        check(not window.actions_by_name["Screenshot"].isEnabled(), "Music screenshot disabled")
        window.grab().save(str(output / "ui/music-window.png"))
        music_frame = window.viewport.grabFramebuffer()
        music_frame.save(str(output / "ui/music-fbo.png"))
        check(
            any(
                music_frame.pixelColor(x, y).red() > 100
                for y in range(music_frame.height() // 3, music_frame.height() * 2 // 3, 2)
                for x in range(music_frame.width() // 3, music_frame.width() * 2 // 3, 2)
            ),
            "Music filename is visibly rendered",
        )
        window.pause()
        wait(200)
        check(window.controls.play.text() == "Play", "Music pauses")
        window.seek(2, "absolute")
        wait(200)
        check(abs(window.controls.position - 2) < 0.5, "Music seeks")
        # Natural endpoints, including music, wrap with a prominent visible clue.
        window.open_path(output / "tone.wma")
        window.navigate(1)
        check(
            window.current_path.suffix == ".aac" and window.loop_notice.isVisible(),
            "Forward wrap opens first file and displays banner",
        )
        window.grab().save(str(output / "ui/loop-notice.png"))
        window.navigate(-1)
        check(
            window.current_path.suffix == ".wma" and "end" in window.loop_notice.text(),
            "Backward wrap opens last file and displays banner",
        )
        check(window.open_path(Path("artifacts/probe/portrait.png")), "Music switches to image")
        wait(300)
        check(
            not window.viewport.audio and not window.controls.isVisible(),
            "Image switch exits music mode and hides transport",
        )
        check(
            window.open_path(Path("artifacts/probe/moving.mp4")), "Music backend switches to video"
        )
        wait(1000)
        check(window.viewport.render_count > 5, "Video rendering restored after audio-only mode")
        window.close()
        wait(100)
        check(not report["errors"], "No unexpected backend errors")
        report["passed"] = True
    except Exception:  # noqa: BLE001 -- record integration failures
        report["errors"].append(traceback.format_exc())
        print(report["errors"][-1], flush=True)
        report["passed"] = False
        window.close()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
