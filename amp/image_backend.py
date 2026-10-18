# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Read local still images with orientation and bounded decoder allocations."""

from PySide6.QtGui import QImageReader


def read_image(path):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    limit = QImageReader.allocationLimit()
    # Qt accounts for at least 32 bits/pixel when enforcing its allocation limit.
    if limit > 0 and size.isValid() and size.width() * size.height() * 4 > limit * 1024**2:
        raise RuntimeError(
            f"This image is too large to open at full resolution "
            f"({size.width()} × {size.height()} pixels; decoder limit {limit} MiB)."
        )
    image = reader.read()
    if image.isNull():
        if reader.error() == QImageReader.ImageReaderError.UnsupportedFormatError:
            raise RuntimeError("This image format is unavailable in this installation or damaged.")
        raise RuntimeError("This image could not be read. It may be damaged or unavailable.")
    # A media filename ending @2x is not an application icon. Use its actual pixels.
    image.setDevicePixelRatio(1)
    return image
