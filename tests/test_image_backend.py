import pytest
from PIL import Image

from amp.image_backend import read_image
from tools.image_fixtures import COLORS, ORIENTED_CORNERS, oriented_jpeg, quadrants


@pytest.mark.parametrize("orientation", range(1, 9))
def test_all_exif_rotations_and_mirrors(tmp_path, orientation):
    path = tmp_path / "orientation.jpg"
    oriented_jpeg(path, orientation)
    image = read_image(path)
    assert (image.width(), image.height()) == ((120, 80) if orientation < 5 else (80, 120))
    for (x, y), index in zip(
        ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)),
        ORIENTED_CORNERS[orientation],
        strict=True,
    ):
        pixel = image.pixelColor(int(x * image.width()), int(y * image.height()))
        assert pixel.getRgb()[:3] == pytest.approx(COLORS[index], abs=12)


@pytest.mark.parametrize(
    "suffix,format",
    [
        ("png", "PNG"),
        ("jpeg", "JPEG"),
        ("jfif", "JPEG"),
        ("bmp", "BMP"),
        ("webp", "WEBP"),
        ("gif", "GIF"),
        ("tif", "TIFF"),
        ("tiff", "TIFF"),
    ],
)
def test_image_formats_are_readable(tmp_path, suffix, format):
    path = tmp_path / f"sample.{suffix}"
    quadrants().save(path, format=format)
    image = read_image(path)
    assert (image.width(), image.height()) == (120, 80)
    assert image.pixelColor(20, 20).red() > 200


def test_multiframe_image_decoder_returns_first_frame(tmp_path):
    path = tmp_path / "sequence.tiff"
    Image.new("RGB", (40, 30), "red").save(
        path,
        format="TIFF",
        save_all=True,
        append_images=[Image.new("RGB", (40, 30), "blue")],
    )
    assert read_image(path).pixelColor(20, 15).red() == 255


def test_media_filename_does_not_inherit_icon_dpi(tmp_path):
    path = tmp_path / "photo@2x.png"
    quadrants().save(path)
    image = read_image(path)
    assert image.devicePixelRatio() == 1
    assert image.width() == 120


def test_corrupt_image_has_actionable_error(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="image.*(damaged|unavailable)"):
        read_image(path)


def test_large_image_budget_rejected_before_decode(tmp_path, monkeypatch):
    path = tmp_path / "image.png"
    quadrants((800, 600)).save(path)
    monkeypatch.setattr("amp.image_backend.QImageReader.allocationLimit", lambda: 1)
    with pytest.raises(RuntimeError, match="too large.*800.*600.*1 MiB"):
        read_image(path)
