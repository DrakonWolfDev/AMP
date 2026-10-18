# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Save captures without ever overwriting an existing file."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def pictures_directory():
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
    if not location:
        raise OSError("The OS Pictures folder is unavailable. Check your Pictures folder settings.")
    return Path(location) / "AMP"


def save_capture(image, directory=None, now=None):
    directory = Path(directory) if directory is not None else pictures_directory()
    directory.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now()
    stem = "AMP_" + now.strftime("%Y%m%d_%H%M%S_") + f"{now.microsecond // 1000:03}"
    # Encode before reserving a name; never leave an empty PNG on encode failure.
    from PySide6.QtCore import QBuffer, QIODevice

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if image.isNull() or not image.save(buffer, "PNG"):
        raise OSError("The viewport could not be encoded as a PNG.")
    data = bytes(buffer.data())
    for number in range(10000):
        suffix = f"_{number}" if number else ""
        path = directory / f"{stem}{suffix}.png"
        try:
            output = path.open("xb")
        except FileExistsError:
            continue
        try:
            with output:
                output.write(data)
            return path
        except OSError:
            path.unlink(missing_ok=True)
            raise
    raise OSError("Too many captures have the same timestamp. Try again shortly.")
