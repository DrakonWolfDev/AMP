"""Build a standalone amd64 Debian package with desktop MIME integration."""

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

try:
    from .linux_bundle import digest, freeze_bundle, stage_package
except ImportError:  # Direct invocation: python tools/build_linux_*.py
    from linux_bundle import digest, freeze_bundle, stage_package


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Build the Debian package on Linux.")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose a new output directory; existing builds are never overwritten.")
    output.mkdir(parents=True)
    report = {"passed": False, "published": False, "release_ready": False, "checks": []}

    def run(arguments, name, *, cwd=root):
        result = subprocess.run(
            [str(argument) for argument in arguments],
            cwd=cwd,
            capture_output=True,
            timeout=900,
        )
        (output / f"{name}.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {output / (name + '.log')}")
        report["checks"].append(name)
        print(f"Passed: {name}", flush=True)

    try:
        run([sys.executable, "-m", "pytest", "-q"], "unit-tests")
        run([sys.executable, "-m", "ruff", "check", "amp", "tools", "tests"], "lint")
        run(
            [sys.executable, "-m", "ruff", "format", "--check", "amp", "tools", "tests"],
            "format",
        )
        bundle = freeze_bundle(root, output, report, run)

        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        package_root = output / "package"
        stage_package(root, package_root, bundle)

        debian = package_root / "DEBIAN"
        debian.mkdir()
        debian.joinpath("control").write_text(
            "\n".join(
                (
                    "Package: amp-media-player",
                    f"Version: {project['version']}",
                    "Section: video",
                    "Priority: optional",
                    "Architecture: amd64",
                    "Maintainer: Andrew Hodgson <support@wolf-forge.co.uk>",
                    "Depends: libmpv2, libegl1, libgl1, libopengl0, libxcb-cursor0, "
                    "libxcb-icccm4, libxcb-keysyms1, libxkbcommon-x11-0",
                    "Homepage: https://github.com/DrakonWolfDev/AMP",
                    "Description: Private-by-design local media player",
                    " AMP displays local images and plays local video and music without accounts,",
                    " telemetry, cloud services, or media-library scans.",
                    "",
                )
            ),
            encoding="utf-8",
        )
        postinst = debian / "postinst"
        postinst.write_text(
            "#!/bin/sh\nset -e\n"
            "command -v update-desktop-database >/dev/null && update-desktop-database -q || true\n"
            "command -v gtk-update-icon-cache >/dev/null && "
            "gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true\n",
            encoding="utf-8",
        )
        postinst.chmod(0o755)
        artifact = output / f"amp-media-player_{project['version']}_amd64.deb"
        run(["dpkg-deb", "--root-owner-group", "--build", package_root, artifact], "dpkg-deb")
        report["artifact"] = {
            "path": str(artifact),
            "bytes": artifact.stat().st_size,
            "sha256": digest(artifact),
        }
        report["passed"] = True
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        report["error"] = str(error)
        print(error, file=sys.stderr)
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
