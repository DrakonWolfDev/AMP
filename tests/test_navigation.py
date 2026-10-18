from pathlib import Path

from amp.folder_navigator import NavigationStep
from amp.navigation import NavigationAttempt


def test_attempt_retains_wrap_and_skip_count_across_async_failures():
    attempt = NavigationAttempt(
        [
            NavigationStep(Path("bad.mp4"), True),
            NavigationStep(Path("good.png"), True),
        ],
        1,
    )
    assert attempt.next() == Path("bad.mp4")
    attempt.skipped += 1
    assert attempt.next() == Path("good.png")
    assert "beginning" in attempt.message() and "Skipped 1" in attempt.message()
    assert attempt.next() is None


def test_duplicate_candidates_are_attempted_only_once():
    attempt = NavigationAttempt(
        [
            NavigationStep(Path("bad.mp3"), False),
            NavigationStep(Path("bad.mp3"), True),
            NavigationStep(Path("last.png"), True),
        ],
        -1,
    )
    assert attempt.next() == Path("bad.mp3")
    assert attempt.next() == Path("last.png")
    assert "end" in attempt.message()
    assert attempt.next() is None
