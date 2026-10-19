from unittest.mock import Mock

import pytest

from amp import windows


@pytest.mark.parametrize("platform, fullscreen", [("linux", True), ("win32", False)])
def test_compositing_workaround_only_touches_windows_fullscreen(monkeypatch, platform, fullscreen):
    monkeypatch.setattr(windows.sys, "platform", platform)
    window = Mock()
    window.isFullScreen.return_value = fullscreen
    windows.enable_fullscreen_compositing(window)
    window.winId.assert_not_called()


@pytest.mark.parametrize("style", [0x90000000, 0x90800000])
def test_compositing_preserves_native_style_and_pointer_sized_handle(monkeypatch, style):
    monkeypatch.setattr(windows.sys, "platform", "win32")
    user32 = Mock()
    user32.GetWindowLongW.return_value = style
    monkeypatch.setattr(windows.ctypes, "windll", Mock(user32=user32), raising=False)
    window = Mock()
    window.isFullScreen.return_value = True
    window.winId.return_value = 0x123456789

    windows.enable_fullscreen_compositing(window)

    user32.GetWindowLongW.assert_called_once_with(0x123456789, -16)
    if style & 0x00800000:
        user32.SetWindowLongW.assert_not_called()
    else:
        user32.SetWindowLongW.assert_called_once_with(0x123456789, -16, style | 0x00800000)
