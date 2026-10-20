from PIL import Image
from PySide6.QtWidgets import QApplication, QMessageBox

from amp import app as app_module
from amp.app import Window
from amp.settings import Preferences

APPLICATION = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])


def image(path, colour):
    Image.new("RGB", (20, 20), colour).save(path)


def fake_trash(path):
    path = app_module.Path(path)
    destination = path.with_suffix(".trashed")
    path.rename(destination)
    # This is the actual return shape from PySide on the supported Linux runtime.
    return True


def test_delete_confirmation_can_be_cancelled(tmp_path, monkeypatch):
    path = tmp_path / "keep.png"
    image(path, "red")
    window = Window(Preferences(tmp_path / "settings.ini"))
    assert window.open_path(path)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.No,
    )

    window.actions_by_name["Move to Trash"].trigger()

    assert path.exists()
    assert window.current_path == path
    window.close()


def test_delete_moves_to_trash_and_displays_next_file(tmp_path, monkeypatch):
    previous = tmp_path / "image1.png"
    current = tmp_path / "image2.png"
    following = tmp_path / "image10.png"
    image(previous, "green")
    image(current, "red")
    image(following, "blue")
    window = Window(Preferences(tmp_path / "settings.ini"))
    assert window.open_path(current)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(app_module.QFile, "moveToTrash", fake_trash)

    window.actions_by_name["Move to Trash"].trigger()

    assert not current.exists()
    assert window.current_path == following
    assert window.viewport.image.pixelColor(10, 10).blue() == 255
    assert window.statusBar().currentMessage() == "Moved image2.png to Trash"
    window.close()


def test_delete_last_file_returns_to_empty_state(tmp_path, monkeypatch):
    path = tmp_path / "only.png"
    image(path, "red")
    window = Window(Preferences(tmp_path / "settings.ini"))
    assert window.open_path(path)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(app_module.QFile, "moveToTrash", fake_trash)

    window.actions_by_name["Move to Trash"].trigger()

    assert window.current_path is None
    assert window.empty.isVisibleTo(window.centralWidget())
    assert not window.actions_by_name["Move to Trash"].isEnabled()
    assert window.actions_by_name["Move to Trash"].shortcut().toString() == "Del"
    window.close()
