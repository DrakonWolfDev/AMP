"""Package an already validated Linux payload as RPM or AppImage."""

import os
import shutil
import urllib.request


def build_appimage(package_root, output, version, run, digest):
    appdir = output / "AMP.AppDir"
    shutil.copytree(package_root, appdir)
    shutil.copyfile(appdir / "usr/share/applications/amp.desktop", appdir / "amp.desktop")
    shutil.copyfile(appdir / "usr/share/icons/hicolor/256x256/apps/amp.png", appdir / "amp.png")
    apprun = appdir / "AppRun"
    apprun.write_text(
        '#!/bin/sh\nappdir="$(cd "$(dirname "$0")" && pwd)"\nexec "$appdir/opt/amp/AMP" "$@"\n',
        encoding="utf-8",
    )
    apprun.chmod(0o755)
    inputs = (
        (
            "appimagetool",
            "https://github.com/AppImage/appimagetool/releases/download/1.9.1/"
            "appimagetool-x86_64.AppImage",
            "ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0",
        ),
        (
            "runtime-x86_64",
            "https://github.com/AppImage/type2-runtime/releases/download/20251108/runtime-x86_64",
            "2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d",
        ),
    )
    for name, url, sha256 in inputs:
        target = output / name
        urllib.request.urlretrieve(url, target)
        if digest(target) != sha256:
            raise RuntimeError(f"Checksum mismatch for {name}")
        target.chmod(0o755)
    artifact = output / f"AMP-{version}-x86_64.AppImage"
    os.environ["ARCH"] = "x86_64"
    os.environ["VERSION"] = version
    run(
        [
            output / "appimagetool",
            "--appimage-extract-and-run",
            "--runtime-file",
            output / "runtime-x86_64",
            appdir,
            artifact,
        ],
        "appimagetool",
    )
    artifact.chmod(0o755)
    return artifact
