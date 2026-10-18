"""Synthetic image fixtures; Pillow is a development-only dependency."""

from PIL import Image, ImageDraw

COLORS = ((230, 30, 30), (30, 210, 30), (30, 30, 230), (230, 210, 30))
ORIENTED_CORNERS = {
    1: (0, 1, 2, 3),
    2: (1, 0, 3, 2),
    3: (3, 2, 1, 0),
    4: (2, 3, 0, 1),
    5: (0, 2, 1, 3),
    6: (2, 0, 3, 1),
    7: (3, 1, 2, 0),
    8: (1, 3, 0, 2),
}


def quadrants(size=(120, 80)):
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    w, h = size
    for box, color in zip(
        (
            (0, 0, w // 2 - 1, h // 2 - 1),
            (w // 2, 0, w - 1, h // 2 - 1),
            (0, h // 2, w // 2 - 1, h - 1),
            (w // 2, h // 2, w - 1, h - 1),
        ),
        COLORS,
        strict=True,
    ):
        draw.rectangle(box, fill=color)
    return image


def oriented_jpeg(path, orientation):
    exif = Image.Exif()
    exif[274] = orientation
    quadrants().save(path, format="JPEG", quality=95, subsampling=0, exif=exif)
