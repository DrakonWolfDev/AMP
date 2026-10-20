import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

from amp import mpv_backend
from amp.viewport import MediaViewport


def test_windows_selects_media_foundation_without_loading_mpv(monkeypatch):
    module = ModuleType("amp.media_foundation_backend")
    backend = object()
    factory = Mock(return_value=backend)
    module.MediaFoundationBackend = factory
    monkeypatch.setitem(sys.modules, "amp.media_foundation_backend", module)
    monkeypatch.setattr(mpv_backend.os, "name", "nt")

    assert mpv_backend.create_backend("parent") is backend
    factory.assert_called_once_with("parent")


def test_existing_non_mpv_backend_is_reused():
    viewport = SimpleNamespace(backend=object())
    MediaViewport.ensure_video(viewport)
