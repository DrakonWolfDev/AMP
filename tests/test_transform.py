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


def test_resize_keeps_zoomed_media_point_at_centre():
    view = ViewTransform(800, 600, 1200, 800)
    view.zoom_at(400, 300, 3)
    view.pan(100, -80)
    x, y, w, h = view.rect
    normalized = ((400 - x) / w, (300 - y) / h)
    view.resize(1000, 700)
    x, y, w, h = view.rect
    assert ((500 - x) / w, (350 - y) / h) == pytest.approx(normalized)
    assert view.zoom == 3


@pytest.mark.parametrize("media", [(300, 1200), (2400, 300), (800, 600)])
def test_letterboxed_media_clamps_and_reset_after_resize(media):
    view = ViewTransform(800, 600, *media)
    view.zoom_at(400, 300, 2)
    view.pan(1e6, -1e6)
    view.resize(500, 900)
    x, y, w, h = view.rect
    assert (x <= 0 and x + w >= 500) if w >= 500 else (0 <= x <= 500 - w)
    assert (y <= 0 and y + h >= 900) if h >= 900 else (0 <= y <= 900 - h)
    view.zoom_at(250, 450, 0.0001)
    assert view.zoom == 1
    assert view.pan_x == view.pan_y == 0


@pytest.mark.parametrize("media,point", [((300, 1200), (450, 200)), ((2400, 300), (300, 320))])
def test_cursor_anchor_survives_letterboxing_at_small_zoom_steps(media, point):
    view = ViewTransform(800, 600, *media)
    x, y, w, h = view.rect
    detail = ((point[0] - x) / w, (point[1] - y) / h)
    view.zoom_at(*point, 1.2)
    x, y, w, h = view.rect
    assert (x + detail[0] * w, y + detail[1] * h) == pytest.approx(point)
