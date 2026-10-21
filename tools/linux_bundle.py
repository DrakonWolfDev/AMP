"""Shared frozen Linux runtime and desktop layout for upstream DEB/RPM previews."""

import hashlib
import importlib.metadata
import shutil
import sys
from pathlib import Path

try:
    from .bundle_policy import forbidden_runtime_file
except ImportError:  # Directly invoked build helper.
    from bundle_policy import forbidden_runtime_file


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def python_license_path():
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = (
        Path(sys.base_prefix) / "LICENSE.txt",
        Path(sys.base_prefix) / "LICENSE",
        Path(sys.base_prefix) / "lib" / version / "LICENSE.txt",
        Path(sys.base_prefix) / "lib64" / version / "LICENSE.txt",
        Path("/usr/share/doc") / version / "copyright",
    )
    try:
        return next(path for path in candidates if path.is_file())
    except StopIteration as error:
        raise RuntimeError("The embedded Python licence file could not be located.") from error


def freeze_bundle(root, output, report, run):
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
        if path.is_file() and forbidden_runtime_file(path.relative_to(bundle))
    ]
    if forbidden:
        raise RuntimeError(f"Unexpected bundled multimedia/PDF libraries: {forbidden}")
    report["inventory"] = [
        {"file": str(p.relative_to(bundle)), "sha256": digest(p), "bytes": p.stat().st_size}
        for p in sorted(bundle.rglob("*"))
        if p.is_file()
    ]
    report["bundle_bytes"] = sum(item["bytes"] for item in report["inventory"])
    return bundle


def stage_package(root, package_root, bundle):
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
