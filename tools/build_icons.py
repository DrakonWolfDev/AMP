"""Render the editable AMP SVG into PNG and multi-resolution Windows ICO assets."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QRectF  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402


def main():
    app = QGuiApplication([])
    assets = Path(__file__).resolve().parents[1] / "amp/assets"
    renderer = QSvgRenderer(str(assets / "amp.svg"))
    if not renderer.isValid():
        raise RuntimeError("Invalid AMP icon SVG")
    sizes = (16, 20, 24, 32, 40, 48, 64, 128, 256)
    frames = []
    for size in (*sizes, 512):
        image = QImage(size * 4, size * 4, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        renderer.render(painter, QRectF(0, 0, image.width(), image.height()))
        painter.end()
        # Supersampling keeps the smallest shell icons clean and consistent.
        rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
        pixels = Image.frombytes(
            "RGBA",
            (image.width(), image.height()),
            rgba.constBits().tobytes(),
        ).resize((size, size), Image.Resampling.LANCZOS)
        if size == 512:
            pixels.save(assets / "amp.png")
        else:
            frames.append(pixels)
    frames[-1].save(assets / "amp.ico", sizes=[(s, s) for s in sizes], append_images=frames[:-1])
    print("Created amp.png and amp.ico:", sizes)
    app.quit()


if __name__ == "__main__":
    main()
