import pytest

from amp.playback import seek_target


@pytest.mark.parametrize(
    "seconds,mode,position,duration,expected",
    [
        (-5, "relative", 2, 30, 0),
        (5, "relative", 28, 30, 30),
        (12.5, "absolute", 2, 30, 12.5),
        (-1, "absolute", 20, 30, 0),
        (5, "relative", None, 30, 5),
        (5, "absolute", 2, None, None),
        (5, "relative", 2, 0, None),
        (float("nan"), "absolute", 2, 30, None),
        (5, "absolute", 2, float("inf"), None),
    ],
)
def test_seek_respects_media_bounds_and_unavailable_duration(
    seconds, mode, position, duration, expected
):
    assert seek_target(seconds, mode, position, duration) == expected
