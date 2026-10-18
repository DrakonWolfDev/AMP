# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

from PySide6.QtCore import QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .appearance import FloatingPanel, configure_button, icon


def time_label(seconds):
    seconds = max(0, int(seconds or 0))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


class QuietSlider(QSlider):
    """A thin rail with a full-height pointer target and Qt keyboard behaviour."""

    def _track(self):
        return 6, max(7, self.width() - 7)

    def _upside_down(self):
        return self.invertedAppearance() != (
            self.layoutDirection() == Qt.LayoutDirection.RightToLeft
        )

    def _move_to(self, x):
        start, end = self._track()
        value = QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            round(max(start, min(end, x)) - start),
            end - start,
            self._upside_down(),
        )
        self.setSliderPosition(value)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.setSliderDown(True)
            self._move_to(event.position().x())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self._move_to(event.position().x())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            self._move_to(event.position().x())
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        y = self.height() / 2
        start, end = self._track()
        position = start + QStyle.sliderPositionFromValue(
            self.minimum(), self.maximum(), self.sliderPosition(), end - start, self._upside_down()
        )
        painter.setBrush(QColor("#444a54"))
        painter.drawRoundedRect(QRectF(start, y - 1, end - start, 2), 1, 1)
        painter.setBrush(QColor("#c6ccd7" if self.isEnabled() else "#626873"))
        painter.drawRoundedRect(QRectF(start, y - 1, position - start, 2), 1, 1)
        radius = 4 if self.isEnabled() else 3
        painter.drawEllipse(QRectF(position - radius, y - radius, radius * 2, radius * 2))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#d9b579"), 1))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)
        painter.end()


class VideoControls(FloatingPanel):
    pause_requested = Signal()
    seek_requested = Signal(float, str)
    volume_requested = Signal(int)
    mute_requested = Signal(bool)
    speed_requested = Signal(float)
    previous_requested = Signal()
    next_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0
        self.position = 0
        self.paused = False
        self.ended = False
        self.seekable = True
        self.seek_buttons = []
        self.volume_level = 100
        self.setMaximumWidth(760)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(3)
        self.timeline = QuietSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 10000)
        self.timeline.setAccessibleName("Playback position")
        self.timeline.sliderReleased.connect(self.seek)
        self.timeline.actionTriggered.connect(self._timeline_action)
        self.timeline.setFixedHeight(16)
        layout.addWidget(self.timeline)
        row = QHBoxLayout()
        row.setSpacing(4)
        layout.addLayout(row)
        self.time = QLabel("0:00 / 0:00")
        self.time.setObjectName("time")
        self.time.setMinimumWidth(105)
        left = QVBoxLayout()
        left.setSpacing(0)
        left.addWidget(self.time)
        self.speed_panel = QWidget()
        speed_row = QHBoxLayout(self.speed_panel)
        speed_row.setContentsMargins(0, 0, 0, 0)
        speed_row.setSpacing(2)
        self.speed = QuietSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(5, 40)
        self.speed.setValue(20)
        self.speed.setFixedSize(70, 20)
        self.speed.setAccessibleName("Video playback speed")
        self.speed.setToolTip("Video speed · 0.25× to 2×")
        self.speed.valueChanged.connect(self._speed_changed)
        speed_row.addWidget(self.speed)
        self.speed_label = QToolButton()
        self.speed_label.setText("1×")
        self.speed_label.setFixedSize(38, 22)
        self.speed_label.setToolTip("Reset playback speed to 1×")
        self.speed_label.setAccessibleName("Reset playback speed to normal")
        self.speed_label.clicked.connect(lambda: self.speed.setValue(20))
        speed_row.addWidget(self.speed_label)
        left.addWidget(self.speed_panel)
        row.addLayout(left)
        row.addStretch()
        self.previous = QToolButton()
        configure_button(self.previous, "Previous file", "previous", "Left")
        self.previous.clicked.connect(self.previous_requested)
        row.addWidget(self.previous)
        self.play = QToolButton()
        self.play.setObjectName("play")
        configure_button(self.play, "Pause", "pause", "Space")
        self.play.setFixedSize(36, 36)
        self.play.clicked.connect(self.pause_requested)
        self.play_icons = {
            name: icon(name.lower(), "#171a20") for name in ("Play", "Pause", "Replay")
        }
        self.play.setIcon(self.play_icons["Pause"])
        for label, seconds in (("−5", -5), ("+5", 5)):
            button = QToolButton()
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setText(label)
            button.setAccessibleName(f"Seek {'back' if seconds < 0 else 'forward'} five seconds")
            button.setToolTip(button.accessibleName())
            button.setFixedSize(30, 30)
            button.clicked.connect(
                lambda _checked=False, delta=seconds: self.seek_requested.emit(delta, "relative")
            )
            row.addWidget(button)
            if seconds < 0:
                row.addWidget(self.play)
            self.seek_buttons.append(button)
        self.next = QToolButton()
        configure_button(self.next, "Next file", "next", "Right")
        self.next.clicked.connect(self.next_requested)
        row.addWidget(self.next)
        row.addStretch()
        self.mute = QToolButton()
        configure_button(self.mute, "Mute", "volume")
        self.mute.setCheckable(True)
        self.mute.toggled.connect(self.mute_requested)
        self.mute.toggled.connect(self._mute_icon)
        row.addWidget(self.mute)
        self.volume = QuietSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setFixedWidth(70)
        self.volume.setAccessibleName("Volume")
        self.volume.valueChanged.connect(self._volume_changed)
        row.addWidget(self.volume)

    def _speed_changed(self, value):
        self.speed_label.setText(f"{value / 20:g}×")
        self.speed_requested.emit(value / 20)

    def _volume_changed(self, value):
        self.volume_level = value
        self.volume_requested.emit(value)
        if value > 0 and self.mute.isChecked():
            self.mute.setChecked(False)

    def _mute_icon(self, muted):
        self.mute.setIcon(icon("muted" if muted else "volume"))
        self.mute.setToolTip("Unmute" if muted else "Mute")
        self.mute.setAccessibleName("Unmute" if muted else "Mute")
        with QSignalBlocker(self.volume):
            self.volume.setValue(0 if muted else self.volume_level)

    def _timeline_action(self, _action):
        if not self.timeline.isSliderDown():
            self.seek_requested.emit(
                self.timeline.sliderPosition() / 10000 * self.duration, "absolute"
            )

    def seek(self):
        self.seek_requested.emit(self.timeline.value() / 10000 * self.duration, "absolute")

    def update_property(self, name, value):
        if name == "duration":
            self.duration = value or 0
        elif name == "time-pos":
            self.position = value or 0
        elif name == "pause":
            self.paused = bool(value)
        elif name == "eof-reached":
            self.ended = bool(value)
        elif name == "seekable":
            self.seekable = bool(value)
        elif name == "volume" and value is not None:
            self.volume_level = max(0, min(100, round(value)))
            self._mute_icon(self.mute.isChecked())
        elif name == "speed" and value is not None:
            if not self.speed.isSliderDown():
                with QSignalBlocker(self.speed):
                    self.speed.setValue(round(value * 20))
                self.speed_label.setText(f"{value:g}×")
        elif name == "mute" and value is not None:
            with QSignalBlocker(self.mute):
                self.mute.setChecked(bool(value))
            self._mute_icon(bool(value))
        text = "Replay" if self.ended else "Play" if self.paused else "Pause"
        if self.play.text() != text:
            self.play.setText(text)
            self.play.setAccessibleName(text)
            self.play.setToolTip(f"{text} (Space)")
            self.play.setIcon(self.play_icons[text])
        self.time.setText(f"{time_label(self.position)} / {time_label(self.duration)}")
        self.timeline.setEnabled(self.duration > 0 and self.seekable)
        for button in self.seek_buttons:
            button.setEnabled(self.duration > 0 and self.seekable)
        if not self.timeline.isSliderDown():
            self.timeline.setValue(
                round(self.position / self.duration * 10000) if self.duration else 0
            )
