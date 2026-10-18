"""Build/test a private portable AMP and optional Inno installer; never publish."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--iscc", type=Path, help="Existing Inno Setup 6.7.3 compiler")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Build the Windows package on Windows.")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose a new output directory; existing builds are never overwritten.")
    runtime = Path(os.environ.get("AMP_MPV_DIR", root / "artifacts/runtime/libmpv")).resolve()
    if not (runtime / "libmpv-2.dll").is_file():
        parser.error("Set AMP_MPV_DIR to the validated libmpv DLL directory.")
    if (
        args.iscc
        and digest(args.iscc) != "0a8757031b33777e4c9cbffee40f11a5062b36d25cbe144c1db73b6102b80ad7"
    ):
        parser.error("Compiler hash differs from the verified WolfLauncher Inno 6.7.3 tool.")
    output.mkdir(parents=True)
    report = {"passed": False, "published": False, "release_ready": False, "checks": []}
    environment = os.environ.copy()
    environment["AMP_MPV_DIR"] = str(runtime)

    def run(arguments, name, *, cwd=root, env=environment):
        result = subprocess.run(
            [str(arg) for arg in arguments], cwd=cwd, env=env, capture_output=True, timeout=600
        )
        (output / f"{name}.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(
                f"{name} failed ({result.returncode}); see {output / (name + '.log')}"
            )
        print(f"Passed: {name}", flush=True)
        report["checks"].append(name)

    try:
        run([sys.executable, "-m", "pytest", "-q"], "unit-tests")
        run([sys.executable, "-m", "ruff", "check", "amp", "tools", "tests"], "lint")
        run([sys.executable, "-m", "ruff", "format", "--check", "amp", "tools", "tests"], "format")
        run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--distpath",
                output / "dist",
                "--workpath",
                output / "build",
                root / "packaging/windows/AMP.spec",
            ],
            "freeze",
        )
        bundle = output / "dist/AMP"
        legal = bundle / "_internal/LICENSES"
        shutil.copyfile(Path(sys.base_prefix) / "LICENSE.txt", legal / "Python.txt")
        freezer = importlib.metadata.distribution("pyinstaller")
        for path in freezer.files or []:
            if Path(path).name == "COPYING.txt":
                shutil.copyfile(freezer.locate_file(path), legal / "PyInstaller.txt")
        (bundle / "PRIVATE_PREVIEW.txt").write_text(
            "Private validation build only. Not release-cleared. Exact transitive sources/notices and clean-machine/platform validation remain pending. See docs/CODEC_AUDIT.md and docs/RELEASE_READINESS.md in the source tree.\n",
            encoding="utf-8",
        )
        forbidden = [
            str(path.relative_to(bundle))
            for path in bundle.rglob("*")
            if path.is_file()
            and (
                path.suffix.lower() == ".jar"
                or any(
                    name in path.name.lower()
                    for name in ("ffmpeg-win", "qt6pdf", "qt6multimedia", "avcodec-", "avformat-")
                )
            )
        ]
        if forbidden:
            raise RuntimeError(f"Unexpected unused/development runtime files: {forbidden}")
        smoke_env = os.environ.copy()
        for key in ("AMP_MPV_DIR", "PYTHONPATH", "PYTHONHOME"):
            smoke_env.pop(key, None)
        smoke_env["PATH"] = str(Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "System32")
        smoke = output / "smoke"
        smoke.mkdir()
        run(
            [
                bundle / "AMP.exe",
                "--self-test",
                "--output",
                smoke,
                "--video",
                root / "artifacts/playback/av.mp4",
                "--music",
                root / "artifacts/playback/tone.wav",
            ],
            "standalone-smoke",
            cwd=smoke,
            env=smoke_env,
        )
        report["smoke"] = json.loads((smoke / "report.json").read_text(encoding="utf-8"))
        if not report["smoke"]["passed"]:
            raise RuntimeError("Standalone media/GL checks failed; see smoke/report.json")
        report["inventory"] = [
            {"file": str(p.relative_to(bundle)), "sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(bundle.rglob("*"))
            if p.is_file()
        ]
        report["bundle_bytes"] = sum(item["bytes"] for item in report["inventory"])
        release = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "version"
        ]
        if args.iscc:
            run(
                [
                    args.iscc.resolve(),
                    "/Qp",
                    f"/DBundleRoot={bundle}",
                    f"/DOutputRoot={output / 'installer'}",
                    f"/DAppVersion={release}",
                    root / "packaging/windows/AMP.iss",
                ],
                "inno-compile",
            )
            installer = next((output / "installer").glob("*.exe"))
            report["installer"] = {
                "path": str(installer),
                "sha256": digest(installer),
                "bytes": installer.stat().st_size,
                "install_uninstall_tested": False,
            }
        report["passed"] = True
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        report["error"] = str(error)
        print(error, file=sys.stderr)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
