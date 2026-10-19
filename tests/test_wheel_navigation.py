from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp.viewport import MediaViewport


def wheel_event(delta):
    return QWheelEvent(
        QPointF(40, 40),
        QPointF(40, 40),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )


def test_opt_in_wheel_navigation_and_middle_click_toggle():
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    viewport = MediaViewport()
    requested = []
    modes = []
    viewport.navigation_requested.connect(requested.append)
    viewport.wheel_mode_changed.connect(modes.append)
    viewport.set_wheel_navigation(True)

    QApplication.sendEvent(viewport, wheel_event(-120))
    QApplication.sendEvent(viewport, wheel_event(120))
    assert requested == [1, -1]

    QTest.mouseClick(viewport, Qt.MouseButton.MiddleButton, pos=QPoint(40, 40))
    assert modes == [True]
    previous_zoom = viewport.transform.zoom
    QApplication.sendEvent(viewport, wheel_event(120))
    assert viewport.transform.zoom > previous_zoom
    assert requested == [1, -1]

    QTest.mouseClick(viewport, Qt.MouseButton.MiddleButton, pos=QPoint(40, 40))
    assert modes == [True, False]
    viewport.close()
    app.processEvents()
