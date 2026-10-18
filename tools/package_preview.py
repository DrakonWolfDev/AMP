"""Offline source/wheel build and fresh-environment validation; never publishes.

Populate a wheelhouse using the commands in docs/PACKAGING.md first.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import venv
from datetime import UTC, datetime
from email.parser import BytesParser
from pathlib import Path
from zipfile import ZipFile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def python_in(folder):
    return folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def wheel_metadata(path):
    with ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = BytesParser().parsebytes(archive.read(name))
        return {
            "name": metadata["Name"],
            "version": metadata["Version"],
            "license_expression": metadata["License-Expression"],
            "license": metadata["License"],
            "project_urls": metadata.get_all("Project-URL", []),
            "license_files": metadata.get_all("License-File", []),
            "embedded_notices": [
                n for n in archive.namelist() if "license" in n.lower() or "copyright" in n.lower()
            ],
            "sha256": digest(path),
            "filename": path.name,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    wheelhouse = args.wheelhouse.resolve()
    output = (
        args.output
        or root / "artifacts/packaging" / datetime.now(UTC).strftime("preview-%Y%m%d-%H%M%S")
    ).resolve()
    if output.exists():
        parser.error(
            "Output already exists; choose a new directory. Existing builds are never overwritten."
        )
    if not wheelhouse.is_dir():
        parser.error("Populate the wheelhouse first; this builder does not access the network.")
    output.mkdir(parents=True)
    report = {"checks": [], "errors": [], "published": False}
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_NO_INDEX"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    # Fixed member timestamps for wheels; also record content hashes for each build.
    environment["SOURCE_DATE_EPOCH"] = "1792278000"

    def run(arguments, cwd=root):
        subprocess.run(
            [str(a) for a in arguments], cwd=cwd, env=environment, check=True, timeout=300
        )

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    try:
        run([sys.executable, "-m", "pytest", "-q"])
        run([sys.executable, "-m", "ruff", "check", "amp", "tools", "tests"])
        run([sys.executable, "-m", "ruff", "format", "--check", "amp", "tools", "tests"])
        build_env, install_env = output / "build-env", output / "install-env"
        venv.EnvBuilder(with_pip=True).create(build_env)
        build_python = python_in(build_env)
        run(
            [
                build_python,
                "-m",
                "pip",
                "install",
                "--no-compile",
                "--no-index",
                "--find-links",
                wheelhouse,
                "-r",
                root / "requirements-build.txt",
            ]
        )
        run([build_python, "-m", "build", "--no-isolation", "--outdir", output / "dist"])
        wheel = next((output / "dist").glob("*.whl"))
        source = next((output / "dist").glob("*.tar.gz"))
        with ZipFile(wheel) as archive:
            check(
                all(
                    archive.read("amp/" + path.name) == path.read_bytes()
                    for path in (root / "amp").glob("*.py")
                ),
                "Built wheel contains the current application source bytes",
            )
            for path in [
                root / "LICENSE",
                root / "THIRD_PARTY_NOTICES.md",
                *sorted((root / "LICENSES").glob("*")),
            ]:
                member = next(
                    n
                    for n in archive.namelist()
                    if n.endswith("/licenses/" + path.relative_to(root).as_posix())
                )
                assert archive.read(member) == path.read_bytes(), path.name
        check(True, "Wheel preserves all first-party and bundled licence/notice bytes")
        with tarfile.open(source) as archive:
            names = archive.getnames()
            check(
                all(
                    any(n.endswith("/" + wanted) for n in names)
                    for wanted in (
                        "tools/package_preview.py",
                        "tools/package_smoke.py",
                        "docs/PACKAGING.md",
                        "tests/test_video_dimensions.py",
                        "AMP_ROADMAP.md",
                        "MANIFEST.in",
                    )
                ),
                "Source archive includes build instructions, tools, tests and product specification",
            )
            check(
                not any("/artifacts/" in n or "/.venv/" in n or "/.git/" in n for n in names),
                "Source archive excludes local media, environments and Git internals",
            )
        runtime_names = {"pyside6-essentials", "shiboken6", "python-mpv", "pyopengl", "mutagen"}
        wheels = output / "wheelhouse"
        wheels.mkdir()
        shutil.copyfile(wheel, wheels / wheel.name)
        for path in wheelhouse.glob("*.whl"):
            metadata = wheel_metadata(path)
            if metadata["name"].lower().replace("_", "-") in runtime_names:
                shutil.copyfile(path, wheels / path.name)
        inventory = [wheel_metadata(p) for p in sorted(wheels.glob("*.whl"))]
        check(len(inventory) == 6, "Runtime wheelhouse has AMP and exactly five dependencies")
        lock = output / "requirements-runtime.txt"
        lock.write_text(
            "\n".join(f"{p['name']}=={p['version']} --hash=sha256:{p['sha256']}" for p in inventory)
            + "\n",
            encoding="utf-8",
        )
        venv.EnvBuilder(with_pip=True).create(install_env)
        installed_python = python_in(install_env)
        run(
            [
                installed_python,
                "-m",
                "pip",
                "install",
                "--no-compile",
                "--no-index",
                "--find-links",
                wheels,
                "--require-hashes",
                "-r",
                lock,
            ],
            cwd=output,
        )
        run([installed_python, "-m", "pip", "check"], cwd=output)
        run([installed_python, "-m", "amp", "--help"], cwd=output)
        run(
            [
                installed_python,
                root / "tools/package_smoke.py",
                "--output",
                output / "smoke",
                "--video",
                root / "artifacts/playback/av.mp4",
                "--music",
                root / "artifacts/playback/tone.wav",
            ],
            cwd=output,
        )
        smoke = json.loads((output / "smoke/report.json").read_text(encoding="utf-8"))
        check(
            smoke["passed"] and Path(smoke["amp_module"]).is_relative_to(install_env),
            "Installed-wheel media/GL tests pass outside the source tree and development venv",
        )
        report["inventory"] = inventory
        report["build_wheels"] = [
            wheel_metadata(p)
            for p in sorted(wheelhouse.glob("*.whl"))
            if wheel_metadata(p)["name"].lower().replace("_", "-") not in runtime_names
        ]
        report["build_tools"] = tomllib.loads(
            (root / "pyproject.toml").read_text(encoding="utf-8")
        )["build-system"]
        report["artifacts"] = {p.name: digest(p) for p in (wheel, source)}
        report["smoke"] = smoke
        report["runtime_bundled"] = False
        report["passed"] = True
    except Exception as error:  # noqa: BLE001 -- retain failed packaging evidence
        report["errors"].append(f"{type(error).__name__}: {error}")
        report["passed"] = False
        print(report["errors"][-1], file=sys.stderr)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Local package report: {output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
