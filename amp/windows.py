# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Native Windows workarounds for the OpenGL application window."""

import ctypes
import sys
from ctypes import wintypes


def enable_fullscreen_compositing(window):
    """Keep menus and dialogs above a fullscreen OpenGL window on Windows."""
    if sys.platform != "win32" or not window.isFullScreen():
        return
    # Qt documents WS_BORDER as the workaround for Windows DWM bypassing
    # composition of fullscreen OpenGL surfaces (including QOpenGLWidget):
    # https://doc.qt.io/qt-6/windows-issues.html#fullscreen-opengl-based-windows
    # GWL_STYLE is a 32-bit value even on 64-bit Windows; HWND is pointer-sized.
    user32 = ctypes.windll.user32
    get_style = user32.GetWindowLongW
    get_style.argtypes = [wintypes.HWND, ctypes.c_int]
    get_style.restype = wintypes.LONG
    set_style = user32.SetWindowLongW
    set_style.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    set_style.restype = wintypes.LONG
    handle = int(window.winId())
    style = get_style(handle, -16)  # GWL_STYLE
    if not style & 0x00800000:  # WS_BORDER
        set_style(handle, -16, style | 0x00800000)
