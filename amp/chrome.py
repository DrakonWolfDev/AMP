# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Fade sibling overlays without resizing or painting into the media framebuffer."""

from PySide6.QtCore import QAbstractAnimation, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QSlider


class QuietControls(QObject):
    def __init__(self, window, panels, idle_ms=2200):
        super().__init__(window)
        self.window = window
        self.panels = panels
        self.effects = []
        self.animations = []
        self.hidden = False
        self.timer = QTimer(self)
        self.timer.setInterval(idle_ms)
        self.timer.timeout.connect(self.fade)
        for panel in panels:
            panel.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, bool(panel.property("passThrough"))
            )
            effect = QGraphicsOpacityEffect(panel)
            panel.setGraphicsEffect(effect)
            effect.setOpacity(1)
            effect.setEnabled(False)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(200)
            self.effects.append(effect)
            self.animations.append(animation)
        self.animations[0].finished.connect(self._finished)
        self.timer.start()

    def reveal(self):
        changing = self.hidden or any(
            animation.state() == QAbstractAnimation.State.Running for animation in self.animations
        )
        if not changing:
            self.timer.start()
            return
        self.window.viewport.unsetCursor()
        self.hidden = False
        for panel, effect, animation in zip(
            self.panels, self.effects, self.animations, strict=False
        ):
            animation.stop()
            effect.setOpacity(1)
            effect.setEnabled(False)
            panel.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, bool(panel.property("passThrough"))
            )
        self.timer.start()

    def busy(self):
        app = QApplication.instance()
        if app.activePopupWidget() or app.activeModalWidget():
            return True
        focused = app.focusWidget()
        for panel in self.panels:
            if not panel.isVisible():
                continue
            if panel is focused or (focused and panel.isAncestorOf(focused)):
                return True
            if not self.hidden and panel.rect().contains(panel.mapFromGlobal(QCursor.pos())):
                return True
            if any(slider.isSliderDown() for slider in panel.findChildren(QSlider)):
                return True
        return bool(QApplication.mouseButtons())

    def fade(self):
        if self.window.current_path is None or self.busy():
            self.timer.start()
            return
        self.timer.stop()
        hint = getattr(self.window, "hover_hint", None)
        if hint:
            hint.hide()
        for panel, effect, animation in zip(
            self.panels, self.effects, self.animations, strict=True
        ):
            if not panel.isVisible():
                effect.setOpacity(0)
                continue
            effect.setEnabled(True)
            animation.setStartValue(1)
            animation.setEndValue(0)
            animation.start()

    def _finished(self):
        if self.effects[0].opacity() == 0:
            self.hidden = True
            for panel in self.panels:
                panel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            if self.window.isFullScreen() and self.window.viewport.video:
                self.window.viewport.setCursor(Qt.CursorShape.BlankCursor)
