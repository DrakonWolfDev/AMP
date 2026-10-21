from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from amp.app import Window
from amp.network_drop import NetworkDropResolver

QtDBus = pytest.importorskip("PySide6.QtDBus")
QDBusConnection = QtDBus.QDBusConnection
QDBusMessage = QtDBus.QDBusMessage


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])


def test_smb_uses_async_kde_call_preserving_encoded_url(application, monkeypatch):
    monkeypatch.setattr("amp.network_drop.sys.platform", "linux")
    bus = Mock()
    monkeypatch.setattr(QDBusConnection, "sessionBus", lambda: bus)
    watcher = Mock()
    monkeypatch.setattr("PySide6.QtDBus.QDBusPendingCallWatcher", Mock(return_value=watcher))
    resolver = NetworkDropResolver()
    url = QUrl("smb://administrator@nas/share/%5B20%5D%20Music/song.mp3")
    resolver.resolve(url)
    message, timeout = bus.asyncCall.call_args.args
    assert message.service() == "org.kde.KIOFuse"
    assert message.interface() == "org.kde.KIOFuse.VFS"
    assert message.member() == "mountUrl"
    assert message.arguments() == [bytes(url.toEncoded()).decode("ascii")]
    assert timeout == 30000
    watcher.finished.connect.assert_called_once()


@pytest.mark.parametrize("path", ["/run/user/1000/kio-fuse-test/smb/nas/song.mp3", "relative"])
def test_reply_requires_absolute_path(application, path):
    resolver = NetworkDropResolver()
    paths, errors = [], []
    resolver.resolved.connect(paths.append)
    resolver.failed.connect(errors.append)
    reply = QDBusMessage.createMethodCall("a.b", "/", "a.b", "mountUrl").createReply()
    reply.setArguments([path])
    watcher = Mock()
    watcher.reply.return_value = reply
    resolver._finished(watcher, 0)
    assert paths == ([path] if path.startswith("/") else [])
    assert bool(errors) == (not path.startswith("/"))
    watcher.deleteLater.assert_called_once()


def test_error_does_not_expose_credentials_and_stale_reply_is_ignored(application):
    resolver = NetworkDropResolver()
    errors = []
    resolver.failed.connect(errors.append)
    watcher = Mock()
    watcher.reply.return_value = QDBusMessage.createError("a.b", "smb://user:secret@nas/file")
    resolver._finished(watcher, 0)
    assert len(errors) == 1
    assert "secret" not in errors[0]
    resolver.cancel()
    resolver._finished(watcher, 0)
    assert len(errors) == 1


@pytest.mark.parametrize(
    "address,remote", [("smb://nas/share/song.mp3", True), ("file:///tmp/song.mp3", False)]
)
def test_drop_routes_network_and_local_files(application, monkeypatch, address, remote):
    monkeypatch.setattr("amp.app.sys.platform", "linux")
    window = SimpleNamespace(network_drop=Mock(), open_path=Mock(), notify=Mock())
    event = Mock()
    event.mimeData.return_value.urls.return_value = [QUrl(address)]
    Window.dragEnterEvent(window, event)
    event.acceptProposedAction.assert_called_once()
    event.acceptProposedAction.reset_mock()
    Window.dropEvent(window, event)
    event.acceptProposedAction.assert_called_once()
    if remote:
        window.network_drop.resolve.assert_called_once_with(QUrl(address))
        window.open_path.assert_not_called()
    else:
        window.open_path.assert_called_once_with("/tmp/song.mp3")
        window.network_drop.cancel.assert_called_once()


def test_unsupported_scheme_never_contacts_kde(application, monkeypatch):
    session_bus = Mock()
    monkeypatch.setattr(QDBusConnection, "sessionBus", session_bus)
    resolver = NetworkDropResolver()
    errors = []
    resolver.failed.connect(errors.append)
    resolver.resolve(QUrl("https://example.com/song.mp3"))
    assert errors
    session_bus.assert_not_called()
