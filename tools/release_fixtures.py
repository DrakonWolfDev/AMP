"""Generate synthetic local files for the packaged release smoke test."""

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=44100",
            "-t",
            "8",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(args.output / "av.mp4"),
        ],
        check=True,
    )
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=44100",
            "-t",
            "8",
            str(args.output / "tone.wav"),
        ],
        check=True,
    )
    (args.output / "av.srt").write_text(
        "1\n00:00:00,000 --> 00:00:08,000\nAMP subtitle verification\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
