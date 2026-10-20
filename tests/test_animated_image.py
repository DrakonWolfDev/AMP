from PIL import Image
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp.viewport import MediaViewport


def test_gif_frames_advance_and_stop_when_another_image_opens(tmp_path):
    application = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    gif = tmp_path / "animated.gif"
    Image.new("RGB", (40, 30), "red").save(
        gif,
        save_all=True,
        append_images=[Image.new("RGB", (40, 30), "blue")],
        duration=80,
        loop=0,
    )
    still = tmp_path / "still.png"
    Image.new("RGB", (40, 30), "green").save(still)

    viewport = MediaViewport()
    viewport.open_image(gif)
    assert viewport.image_movie is not None
    assert viewport.image.pixelColor(20, 15).red() == 255

    QTest.qWait(100)
    application.processEvents()
    assert viewport.image.pixelColor(20, 15).blue() == 255

    viewport.open_image(still)
    assert viewport.image_movie is None
    assert viewport.image.pixelColor(20, 15).green() > 100
    viewport.cleanup()
