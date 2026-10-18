import pytest

from amp.view_transform import ViewTransform


@pytest.mark.parametrize(
    "media,expected", [((400, 800), (250, 0, 300, 600)), ((1600, 400), (0, 200, 800, 200))]
)
def test_fit_preserves_aspect(media, expected):
    view = ViewTransform(800, 600, *media)
    assert view.rect == pytest.approx(expected)


def test_cursor_detail_stays_under_cursor():
    view = ViewTransform(800, 600, 800, 600)
    before = view.rect
    point = (250, 240)
    normalized = ((point[0] - before[0]) / before[2], (point[1] - before[1]) / before[3])
    view.zoom_at(*point, 2)
    x, y, w, h = view.rect
    assert (x + normalized[0] * w, y + normalized[1] * h) == pytest.approx(point)


def test_limits_pan_and_reset():
    view = ViewTransform(800, 600, 800, 600)
    view.zoom_at(400, 300, 1000)
    assert view.zoom == 32
    view.pan(1e6, -1e6)
    x, y, w, h = view.rect
    assert x <= 0 and y <= 0 and x + w >= 800 and y + h >= 600
    view.reset()
    assert view.rect == (0, 0, 800, 600)


def test_sessions_do_not_share_transform():
    first, second = ViewTransform(), ViewTransform()
    first.zoom_at(0.5, 0.5, 2)
    assert second.zoom == 1


def test_mpv_pan_uses_scaled_media_dimensions():
    view = ViewTransform(800, 600, 800, 600)
    view.zoom_at(400, 300, 2)
    view.pan(80, -60)
    assert view.mpv_options == pytest.approx((1, 0.05, -0.05))
