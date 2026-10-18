from datetime import datetime

import pytest
from PySide6.QtGui import QColor, QImage

from amp.capture import pictures_directory, save_capture


def test_collision_safe_png_without_overwriting(tmp_path):
    image = QImage(80, 40, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    timestamp = datetime(2026, 10, 18, 12, 30, 40, 123000)
    first = save_capture(image, tmp_path / "AMP", timestamp)
    image.fill(QColor("blue"))
    second = save_capture(image, tmp_path / "AMP", timestamp)
    assert first.name == "AMP_20261018_123040_123.png"
    assert second.name == "AMP_20261018_123040_123_1.png"
    assert QImage(str(first)).pixelColor(0, 0) == QColor("red")
    assert QImage(str(second)).pixelColor(0, 0) == QColor("blue")
    assert QImage(str(second)).size() == image.size()


def test_null_capture_leaves_no_png(tmp_path):
    with pytest.raises(OSError, match="encoded"):
        save_capture(QImage(), tmp_path)
    assert not list(tmp_path.glob("*.png"))


def test_unavailable_output_directory_is_reported(tmp_path):
    blocked = tmp_path / "file"
    blocked.touch()
    image = QImage(10, 10, QImage.Format.Format_RGB32)
    with pytest.raises(OSError):
        save_capture(image, blocked / "AMP")


def test_native_pictures_location_and_missing_location(monkeypatch, tmp_path):
    monkeypatch.setattr("amp.capture.QStandardPaths.writableLocation", lambda _kind: str(tmp_path))
    assert pictures_directory() == tmp_path / "AMP"
    monkeypatch.setattr("amp.capture.QStandardPaths.writableLocation", lambda _kind: "")
    with pytest.raises(OSError, match="Pictures folder is unavailable"):
        pictures_directory()
