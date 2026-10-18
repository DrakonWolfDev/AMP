from types import SimpleNamespace
from unittest.mock import Mock

from amp.viewport import MediaViewport


def viewport_state():
    return SimpleNamespace(
        closed=False,
        load_serial=2,
        playable=True,
        video=True,
        transform=SimpleNamespace(media_width=400, media_height=800),
        backend=Mock(),
        apply_transform=Mock(),
        video_changed=Mock(),
    )


def test_late_observer_dimensions_request_current_state_instead_of_overwriting():
    viewport = viewport_state()
    MediaViewport._property(viewport, "video-out-params", {"dw": 800, "dh": 400})
    viewport.backend.refresh_video.assert_called_once_with(2)
    assert (viewport.transform.media_width, viewport.transform.media_height) == (400, 800)
    viewport.apply_transform.assert_not_called()


def test_dimensions_accept_only_current_load_snapshot():
    viewport = viewport_state()
    MediaViewport._load_ready(viewport, 1, {"video-out-params": {"dw": 800, "dh": 400}})
    assert (viewport.transform.media_width, viewport.transform.media_height) == (400, 800)
    MediaViewport._load_ready(viewport, 2, {"video-out-params": {"dw": 600, "dh": 900}})
    assert (viewport.transform.media_width, viewport.transform.media_height) == (600, 900)
    viewport.apply_transform.assert_called_once()
