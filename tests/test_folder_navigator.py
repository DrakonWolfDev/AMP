from amp.folder_navigator import navigation_steps, neighbours


def test_natural_order_and_no_recursion(tmp_path):
    for name in ("clip10.mp4", "clip2.mp4", "clip1.mp4", "notes.txt", "clip02.mp4"):
        (tmp_path / name).touch()
    nested = tmp_path / "clip3.mp4"
    nested.mkdir()
    (nested / "nested.png").touch()
    assert [path.name for path in neighbours(tmp_path / "clip1.mp4", 1)] == [
        "clip02.mp4",
        "clip2.mp4",
        "clip10.mp4",
    ]


def test_deleted_anchor_and_wrapping(tmp_path):
    for name in ("image1.PNG", "image3.jpg"):
        (tmp_path / name).touch()
    assert [p.name for p in neighbours(tmp_path / "image2.png", 1)] == ["image3.jpg", "image1.PNG"]
    assert [p.name for p in neighbours(tmp_path / "image2.png", -1)] == ["image1.PNG", "image3.jpg"]
    assert list(navigation_steps(tmp_path / "image3.jpg", 1))[0].wrapped
    assert list(navigation_steps(tmp_path / "image1.PNG", -1))[0].wrapped


def test_music_and_wrap_flags_in_both_directions(tmp_path):
    for name in ("track1.mp3", "track2.flac", "track10.wav", "notes.txt"):
        (tmp_path / name).touch()
    steps = list(navigation_steps(tmp_path / "track2.flac", 1))
    assert [(s.path.name, s.wrapped) for s in steps] == [
        ("track10.wav", False),
        ("track1.mp3", True),
    ]
    steps = list(navigation_steps(tmp_path / "track2.flac", -1))
    assert [(s.path.name, s.wrapped) for s in steps] == [
        ("track1.mp3", False),
        ("track10.wav", True),
    ]


def test_single_file_does_not_restart_itself(tmp_path):
    path = tmp_path / "only.opus"
    path.touch()
    assert list(neighbours(path, 1)) == []
    assert list(neighbours(path, -1)) == []
