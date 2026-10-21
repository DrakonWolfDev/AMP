"""Build an unsigned upstream Fedora x86_64 RPM preview; never publish."""

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path

try:
    from .linux_bundle import digest, freeze_bundle, stage_package
except ImportError:  # Direct invocation: python tools/build_linux_*.py
    from linux_bundle import digest, freeze_bundle, stage_package
from packaging.version import Version


def rpm_version(value):
    """Sort a Python prerelease before the corresponding final RPM version."""
    version = Version(value)
    if version.epoch or version.dev is not None or version.post is not None or version.local:
        raise ValueError("RPM previews support release versions and a/b/rc prereleases only")
    result = version.base_version
    if version.pre:
        result += f"~{version.pre[0]}{version.pre[1]}"
    return result


def private_requires_pattern(bundle):
    # ELF generators annotate SONAME requirements with (SYMBOL_VERSION)(64bit).
    # Only suppress names actually present in this runtime; preserve system ABIs.
    names = {
        path.name
        for path in bundle.rglob("lib*.so*")
        if path.is_file() and re.fullmatch(r"[A-Za-z0-9_.+-]+", path.name)
    }
    if not names:
        raise ValueError("The frozen runtime contains no shared libraries")
    return (
        "^("
        + "|".join(name.replace(".", "[.]").replace("+", "[+]") for name in sorted(names))
        + ")([(]|$)"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rpmbuild", default="rpmbuild", help="RPM builder executable")
    args = parser.parse_args()
    if sys.platform != "linux" or platform.machine() != "x86_64":
        parser.error("Build this preview on x86_64 Fedora Linux.")
    system = platform.freedesktop_os_release()
    if system.get("ID") != "fedora" or system.get("VERSION_ID") != "44":
        parser.error("This preview currently targets Fedora 44 only.")
    if not shutil.which(args.rpmbuild):
        parser.error("Install rpm-build before building this preview.")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        parser.error("Choose a new output directory; existing builds are never overwritten.")
    output.mkdir(parents=True)
    report = {
        "passed": False,
        "published": False,
        "release_ready": False,
        "checks": [],
        "target": "Fedora 44 x86_64",
        "python": platform.python_version(),
    }

    def run(arguments, name, *, cwd=root):
        result = subprocess.run(
            [str(argument) for argument in arguments], cwd=cwd, capture_output=True, timeout=900
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
        run(["desktop-file-validate", root / "packaging/linux/amp.desktop"], "desktop-entry")
        run(["rpm", "-qa", "--qf", "%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n"], "host-packages")
        bundle = freeze_bundle(root, output, report, run)
        stage = output / "package"
        stage_package(root, stage, bundle)
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        top = output / "rpmbuild"
        for directory in ("SOURCES", "SPECS", "BUILD", "BUILDROOT", "RPMS", "SRPMS", "tmp"):
            (top / directory).mkdir(parents=True)
        with tarfile.open(top / "SOURCES/amp-runtime.tar.gz", "w:gz") as archive:
            archive.add(stage, arcname="amp-runtime")
        spec = (root / "packaging/fedora/amp.spec.in").read_text(encoding="utf-8")
        spec = spec.replace("@VERSION@", rpm_version(project["version"]))
        spec = spec.replace("@PRIVATE_REQUIRES@", private_requires_pattern(bundle))
        spec_path = top / "SPECS/amp-media-player.spec"
        spec_path.write_text(spec, encoding="utf-8")
        run(
            [
                args.rpmbuild,
                "--define",
                f"_topdir {top}",
                "--define",
                f"_tmppath {top / 'tmp'}",
                "-bb",
                spec_path,
            ],
            "rpmbuild",
        )
        packages = list((top / "RPMS/x86_64").glob("*.rpm"))
        if len(packages) != 1:
            raise RuntimeError("Expected exactly one x86_64 RPM")
        artifact = output / packages[0].name
        shutil.copyfile(packages[0], artifact)
        run(["rpm", "-qp", "--requires", artifact], "rpm-requires")
        requirements = (output / "rpm-requires.log").read_text(encoding="utf-8")
        if "libc.so.6" not in requirements:
            raise RuntimeError(
                "RPM did not generate system ABI requirements; check rpm-build helpers"
            )
        run(["rpm", "-qp", "--provides", artifact], "rpm-provides")
        provides = (output / "rpm-provides.log").read_text(encoding="utf-8")
        if any(line.startswith("lib") for line in provides.splitlines()):
            raise RuntimeError("RPM advertises private runtime libraries as system providers")
        run(["rpm", "-qpl", artifact], "rpm-files")
        run(["rpm", "-K", artifact], "rpm-integrity")
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
