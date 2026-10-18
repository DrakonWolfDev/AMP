import pytest
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from amp.music import Music
from amp.music_view import MusicView


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    yield app


def cover_bounds(width, height):
    art = QImage(200, 100, QImage.Format.Format_RGB32)
    art.fill(QColor("#ff2222"))
    view = MusicView()
    view.set_music(Music(title="Responsive title", artwork=art))
    image = QImage(width, height, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    view.paint(painter, width, height)
    painter.end()

    def red(x, y):
        pixel = image.pixelColor(x, y)
        return pixel.red() > 240 and pixel.green() < 60

    rows = [y for y in range(height) if red(width // 2, y)]
    assert rows, "Artwork must remain visible"
    columns = [x for x in range(width) if red(x, (min(rows) + max(rows)) // 2)]
    return min(columns), min(rows), max(columns), max(rows)


@pytest.mark.parametrize("size", [(500, 300), (540, 400), (960, 640), (1536, 864)])
def test_resizing_keeps_cover_aspect_correct_and_clear_of_controls(application, size):
    width, height = size
    left, top, right, bottom = cover_bounds(width, height)
    assert abs((right - left + 1) - 2 * (bottom - top + 1)) <= 3
    assert left >= 36 and right < width - 36
    assert top >= 78 and bottom < height - 112


def test_cover_grows_when_player_grows(application):
    small = cover_bounds(960, 640)
    large = cover_bounds(1536, 864)
    assert large[2] - large[0] > (small[2] - small[0]) * 1.4
