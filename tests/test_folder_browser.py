import pytest
from PySide6.QtWidgets import QApplication

from amp.folder_browser import FolderBrowser, folder_entries


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    yield app


def test_listing_is_one_level_folders_first_and_naturally_sorted(tmp_path):
    (tmp_path / "Album").mkdir()
    (tmp_path / "Album" / "nested.mp3").touch()
    for name in ("track10.mp3", "track2.mp3", "cover.PNG", "notes.txt", "lyrics.lrc"):
        (tmp_path / name).touch()
    assert [path.name for path, _ in folder_entries(tmp_path)] == [
        "Album",
        "cover.PNG",
        "track2.mp3",
        "track10.mp3",
    ]


def test_browsing_does_not_request_playback_and_marks_current(application, tmp_path):
    album = tmp_path / "Album"
    album.mkdir()
    song = album / "Song.mp3"
    song.touch()
    browser = FolderBrowser()
    requests = []
    browser.file_requested.connect(requests.append)
    browser.set_directory(tmp_path)
    browser.activate(album)
    assert browser.directory == album
    assert not requests
    browser.current_path = song
    browser.mark_current()
    assert browser.files.currentItem().font().bold()
    browser.activate(song)
    assert requests == [song]
    browser.parent_folder()
    assert browser.directory == tmp_path
    browser.close()


def test_unavailable_folder_preserves_previous_listing(application, tmp_path):
    browser = FolderBrowser()
    errors = []
    browser.failed.connect(errors.append)
    browser.set_directory(tmp_path)
    assert not browser.set_directory(tmp_path / "missing")
    assert browser.directory == tmp_path
    assert errors
    browser.close()


def test_closed_browser_follows_external_file_without_reading_folder(application, tmp_path):
    browser = FolderBrowser()
    browser.set_directory(tmp_path)
    browser.follow(tmp_path / "other" / "song.mp3")
    assert browser.directory is None
    assert browser.current_path == tmp_path / "other" / "song.mp3"
    assert browser.files.count() == 0
    browser.close()
