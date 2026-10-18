# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""A small, shared palette and hand-drawn controls; no icon/font dependency."""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QFrame

STYLE = """
QMainWindow { background: #08090b; }
QToolTip { color: #f0f1f3; background: #24272c; border: 1px solid #444951; padding: 6px; }
QLabel#hoverHint { color: #f0f1f3; background: #24272c; border: 1px solid #444951;
    border-radius: 5px; padding: 6px 9px; font-size: 12px; }
QLabel#filename { color: #c7cbd2; background: rgba(15, 17, 21, 225);
    border-radius: 6px; padding: 7px 10px; font-size: 12px; }
QLabel#time { color: #a7adb7; font-size: 11px; }
QListWidget#folderFiles { background: #14171c; color: #dce0e6; border: 0; outline: 0; }
QListWidget#folderFiles::item { padding: 7px 5px; border-radius: 4px; }
QListWidget#folderFiles::item:hover { background: #30353d; }
QListWidget#folderFiles::item:selected { background: #363d48; }
QToolButton { background: transparent; color: #dce0e6; border: 1px solid transparent;
    border-radius: 6px; padding: 0; }
QToolButton:hover { background: #30353d; }
QToolButton:pressed, QToolButton:checked { background: #3d444f; }
QToolButton:focus, QPushButton:focus, QSlider:focus {
    border: 1px solid #d9b579; border-radius: 5px;
}
QToolButton:disabled { color: #626873; }
QToolButton#play { background: #e0e3e9; border-radius: 18px; }
QToolButton#play:hover { background: #ffffff; }
QSlider { background: transparent; border: 1px solid transparent; }
QSlider::groove:horizontal { height: 3px; background: #444a54; border-radius: 1px; }
QSlider::sub-page:horizontal { background: #c6ccd7; border-radius: 1px; }
QSlider::handle:horizontal { background: #e0e3e9; width: 9px; margin: -3px 0;
    border-radius: 4px; }
QSlider:disabled::sub-page:horizontal { background: #626873; }
QMenu { background: #181c22; color: #e0e3e9; border: 1px solid #63543b;
    border-top: 2px solid #d9b579; padding: 8px; }
QMenu::item { padding: 10px 24px 10px 14px; border-radius: 5px; }
QMenu::item:selected { background: #353027; color: #f2d7a9; }
QMenu::item:disabled { color: #737a85; }
QMenu::separator { height: 1px; background: #363b43; margin: 5px 8px; }
QDialog, QMessageBox { background: #171a20; color: #e0e3e9; }
QDialog#projectDialog { background: #171b22; }
QFrame#dialogAccent { background: #d9b579; border: 0; }
QScrollArea#dialogScroll { border: 0; background: #171b22; }
QScrollArea#dialogScroll > QWidget > QWidget { background: #171b22; }
QLabel#dialogBrand { color: #e9d1a8; font-size: 27px; font-weight: 600; }
QLabel#dialogEyebrow { color: #bca780; font-size: 10px; }
QLabel#dialogTitle { color: #edf0f5; font-size: 23px; font-weight: 500; }
QLabel#dialogSubtitle { color: #aab3c0; font-size: 13px; }
QDialog#projectDialog QLabel#dialogNote { color: #9ca7b8; font-size: 12px; }
QDialog#projectDialog QLabel#dialogSection { color: #e9d1a8; font-size: 14px; font-weight: 500; }
QDialog#projectDialog QLabel#shortcutKey { color: #e9d1a8; font-size: 12px; }
QWidget#dialogFooter { background: #13171d; border-top: 1px solid #303744; }
QLabel#dialogAttribution { color: #bca780; font-size: 10px; }
QFrame#dialogCard { background: #1e242d; border: 1px solid #36404c; border-radius: 8px; }
QDialog#projectDialog QPushButton { min-width: 72px; padding: 8px 16px; }
QDialog#projectDialog QPushButton:default { background: #3d3427; color: #f2d7a9; border-color: #b89b6b; }
QDialog#projectDialog QCheckBox { spacing: 10px; padding: 4px 0; }
QDialog#projectDialog QCheckBox::indicator { width: 16px; height: 16px; }
QPushButton { color: #e0e3e9; background: #2a2f38; border: 1px solid #424955;
    padding: 8px 16px; border-radius: 5px; }
QPushButton:hover { background: #373e49; }
QSpinBox { padding: 6px; background: #222731; border: 1px solid #424955; border-radius: 4px; }
QLabel#emptyTitle { color: #e0e3e9; font-size: 36px; font-weight: 500; }
QLabel#emptySubtitle { color: #969eab; font-size: 13px; }
QLabel#emptyHint { color: #727b88; font-size: 11px; }
QLabel#notice { color: #dce0e6; background: #222731; border: 1px solid #424955;
    border-radius: 6px; padding: 9px 14px; }
QLabel#loopNotice { color: #f4d59f; background: #33291c; border: 1px solid #a27b42;
    border-radius: 6px; padding: 10px 16px; font-weight: 500; }
"""


class FloatingPanel(QFrame):
    """Paint a quiet backdrop with transparent corners above the GL surface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#353a42"), 1))
        painter.setBrush(QColor(20, 23, 28, 245))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        painter.end()


def apply_appearance(app):
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    app.setStyle("Fusion")
    palette = QPalette()
    for role, colour in (
        (QPalette.ColorRole.Window, "#171a20"),
        (QPalette.ColorRole.WindowText, "#e0e3e9"),
        (QPalette.ColorRole.Base, "#111419"),
        (QPalette.ColorRole.AlternateBase, "#222731"),
        (QPalette.ColorRole.Text, "#e0e3e9"),
        (QPalette.ColorRole.Button, "#2a2f38"),
        (QPalette.ColorRole.ButtonText, "#e0e3e9"),
        (QPalette.ColorRole.Highlight, "#545f70"),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
        (QPalette.ColorRole.PlaceholderText, "#969eab"),
    ):
        palette.setColor(role, QColor(colour))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#737a85"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#737a85"))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)


def icon(name, colour="#dce0e6"):
    # Render multiple resolutions so thin strokes remain crisp on high-DPI screens.
    result = QIcon()
    for scale in (1, 1.25, 1.5, 2, 3):
        pixmap = QPixmap(round(24 * scale), round(24 * scale))
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QPen(
                QColor(colour),
                1.6,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        if name in ("previous", "next"):
            direction = 1 if name == "previous" else -1
            x = 12
            painter.drawLine(QPointF(x + direction * 3, 6), QPointF(x - direction * 3, 12))
            painter.drawLine(QPointF(x - direction * 3, 12), QPointF(x + direction * 3, 18))
        elif name == "play":
            path = QPainterPath(QPointF(9, 6))
            path.lineTo(18, 12)
            path.lineTo(9, 18)
            path.closeSubpath()
            painter.fillPath(path, QColor(colour))
        elif name == "pause":
            painter.fillRect(8, 6, 3, 12, QColor(colour))
            painter.fillRect(14, 6, 3, 12, QColor(colour))
        elif name == "reset":
            painter.drawRect(6, 8, 12, 8)
            for x, y, dx, dy in ((3, 4, 1, 1), (21, 4, -1, 1), (3, 20, 1, -1), (21, 20, -1, -1)):
                painter.drawLine(x, y, x + dx * 4, y)
                painter.drawLine(x, y, x, y + dy * 3)
        elif name == "replay":
            painter.drawArc(5, 5, 14, 14, 35 * 16, 290 * 16)
            painter.drawLine(18, 3, 18, 8)
            painter.drawLine(13, 8, 18, 8)
        elif name == "open":
            path = QPainterPath(QPointF(3, 18))
            for point in ((3, 6), (9, 6), (11, 8), (21, 8), (21, 18), (3, 18)):
                path.lineTo(*point)
            painter.drawPath(path)
        elif name == "capture":
            painter.drawRoundedRect(3, 7, 18, 13, 2, 2)
            painter.drawEllipse(8, 10, 8, 7)
            painter.drawLine(8, 7, 10, 4)
            painter.drawLine(10, 4, 15, 4)
            painter.drawLine(15, 4, 17, 7)
        elif name == "fullscreen":
            for x, y, dx, dy in ((4, 4, 1, 1), (20, 4, -1, 1), (4, 20, 1, -1), (20, 20, -1, -1)):
                painter.drawLine(x, y, x + dx * 5, y)
                painter.drawLine(x, y, x, y + dy * 5)
        elif name in ("volume", "muted"):
            path = QPainterPath(QPointF(4, 10))
            for point in ((8, 10), (12, 6), (12, 18), (8, 14), (4, 14), (4, 10)):
                path.lineTo(*point)
            painter.drawPath(path)
            if name == "muted":
                painter.drawLine(17, 10, 21, 14)
                painter.drawLine(17, 14, 21, 10)
            else:
                painter.drawArc(11, 5, 10, 14, -65 * 16, 130 * 16)
        elif name == "more":
            for x in (5, 12, 19):
                painter.setBrush(QColor(colour))
                painter.drawEllipse(QPointF(x, 12), 1, 1)
        painter.end()
        result.addPixmap(pixmap)
    return result


def configure_button(button, text, symbol, shortcut=""):
    button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    button.setText(text)
    button.setAccessibleName(text)
    button.setToolTip(f"{text} ({shortcut})" if shortcut else text)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    button.setIcon(icon(symbol))
    button.setIconSize(QSize(20, 20))
    button.setFixedSize(32, 32)
