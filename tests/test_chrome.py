from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QToolButton, QWidget

from amp import app as app_module
from amp.app import Window
from amp.chrome import QuietControls
from amp.settings import Preferences


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    yield app


def test_visible_controls_do_not_reenable_effects_or_reset_cursor(application):
    window = QMainWindow()
    window.viewport = QWidget(window)
    window.current_path = Path("image.png")
    panels = [QWidget(window), QWidget(window)]
    chrome = QuietControls(window, panels)
    window.viewport.setCursor(Qt.CursorShape.CrossCursor)
    for _ in range(100):
        chrome.reveal()
    assert all(not effect.isEnabled() for effect in chrome.effects)
    assert all(effect.opacity() == 1 for effect in chrome.effects)
    assert window.viewport.cursor().shape() == Qt.CursorShape.CrossCursor
    chrome.hidden = True
    window.viewport.setCursor(Qt.CursorShape.BlankCursor)
    for effect in chrome.effects:
        effect.setEnabled(True)
        effect.setOpacity(0)
    chrome.reveal()
    assert not chrome.hidden
    assert window.viewport.cursor().shape() != Qt.CursorShape.BlankCursor
    assert all(not effect.isEnabled() and effect.opacity() == 1 for effect in chrome.effects)
    chrome.timer.stop()
    window.close()


def test_fullscreen_hover_hint_is_a_child_widget_not_a_native_popup(application, tmp_path):
    window = Window(Preferences(tmp_path / "settings.ini"))
    button = next(
        b
        for b in window.toolbar.findChildren(QToolButton)
        if b.defaultAction() is window.actions_by_name["Fullscreen"]
    )
    event = QHelpEvent(QEvent.Type.ToolTip, QPoint(8, 8), button.mapToGlobal(QPoint(8, 8)))
    QApplication.sendEvent(button, event)
    assert window.hover_hint.text() == "Fullscreen (F11)"
    assert not window.hover_hint.isWindow()
    assert window.hover_hint.parent() is window.centralWidget()
    assert not window.fullscreen_timer.isActive()
    assert not any(
        widget.isVisible() and widget.metaObject().className() == "QTipLabel"
        for widget in QApplication.topLevelWidgets()
    )
    QTest.mousePress(button, Qt.MouseButton.LeftButton)
    assert window.hover_hint.isHidden()
    # Release away from the button so this test never requests fullscreen.
    QTest.mouseRelease(button, Qt.MouseButton.LeftButton, pos=QPoint(-10, -10))
    window.close()


def test_fullscreen_applies_compositing_on_entry_and_after_settling(
    application, tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        app_module, "enable_fullscreen_compositing", lambda window: calls.append(window.isFullScreen())
    )
    window = Window(Preferences(tmp_path / "settings.ini"))
    window.set_fullscreen(True)
    assert calls == [True]
    window._finish_fullscreen()
    assert calls == [True, True]
    window.set_fullscreen(False)
    assert not window.isFullScreen()
    window.close()
