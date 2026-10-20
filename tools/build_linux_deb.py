"""Build a standalone amd64 Debian package with desktop MIME integration."""

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def python_license_path():
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = (
        Path(sys.base_prefix) / "LICENSE.txt",
        Path(sys.base_prefix) / "LICENSE",
        Path(sys.base_prefix) / "lib" / version / "LICENSE.txt",
        Path("/usr/share/doc") / version / "copyright",
    )
    try:
        return next(path for path in candidates if path.is_file())
    except StopIteration as error:
        raise RuntimeError("The embedded Python licence file could not be located.") from error


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
                root / "packaging/linux/AMP.spec",
            ],
            "freeze",
        )
        bundle = output / "dist/AMP"
        legal = bundle / "_internal/LICENSES"
        shutil.copyfile(python_license_path(), legal / "Python.txt")
        freezer = importlib.metadata.distribution("pyinstaller")
        copied_freezer_license = False
        for path in freezer.files or []:
            if Path(path).name == "COPYING.txt":
                shutil.copyfile(freezer.locate_file(path), legal / "PyInstaller.txt")
                copied_freezer_license = True
                break
        if not copied_freezer_license:
            raise RuntimeError("The PyInstaller licence file could not be located.")
        (bundle / "BUILD_INFORMATION.txt").write_text(
            "Built from the AMP source tree. See THIRD_PARTY_NOTICES.md and the LICENSES folder "
            "for licensing information. libmpv and its codec stack are supplied by the Linux "
            "distribution, not this bundle. Validate installation and playback on the target "
            "system.\n",
            encoding="utf-8",
        )
        forbidden = [
            str(path.relative_to(bundle))
            for path in bundle.rglob("*")
            if path.is_file()
            and any(
                name in path.name.casefold()
                for name in ("qt6multimedia", "qt6pdf", "libavcodec", "libavformat")
            )
        ]
        if forbidden:
            raise RuntimeError(f"Unexpected bundled multimedia/PDF libraries: {forbidden}")
        report["inventory"] = [
            {"file": str(p.relative_to(bundle)), "sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(bundle.rglob("*"))
            if p.is_file()
        ]
        report["bundle_bytes"] = sum(item["bytes"] for item in report["inventory"])

        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        package_root = output / "package"
        application = package_root / "opt/amp"
        shutil.copytree(bundle, application)
        binary = package_root / "usr/bin"
        binary.mkdir(parents=True)
        launcher = binary / "amp"
        launcher.write_text('#!/bin/sh\nexec /opt/amp/AMP "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
        applications = package_root / "usr/share/applications"
        applications.mkdir(parents=True)
        shutil.copyfile(root / "packaging/linux/amp.desktop", applications / "amp.desktop")
        icons = package_root / "usr/share/icons/hicolor/256x256/apps"
        icons.mkdir(parents=True)
        shutil.copyfile(root / "amp/assets/amp.png", icons / "amp.png")
        docs = package_root / "usr/share/doc/amp"
        docs.mkdir(parents=True)
        shutil.copyfile(root / "THIRD_PARTY_NOTICES.md", docs / "THIRD_PARTY_NOTICES.md")
        shutil.copyfile(root / "LICENSE", docs / "copyright")

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
                    "Depends: libmpv2, libegl1, libgl1, libopengl0, libxcb-cursor0",
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
