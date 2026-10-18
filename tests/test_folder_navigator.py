from amp.folder_navigator import neighbours


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


def test_deleted_anchor_and_no_wrapping(tmp_path):
    for name in ("image1.PNG", "image3.jpg"):
        (tmp_path / name).touch()
    assert [p.name for p in neighbours(tmp_path / "image2.png", 1)] == ["image3.jpg"]
    assert [p.name for p in neighbours(tmp_path / "image2.png", -1)] == ["image1.PNG"]
    assert list(neighbours(tmp_path / "image3.jpg", 1)) == []
    assert list(neighbours(tmp_path / "image1.PNG", -1)) == []
