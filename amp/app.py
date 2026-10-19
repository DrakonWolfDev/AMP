# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Small application shell used while the renderer gate is under validation."""

import argparse
import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QSurfaceFormat
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .appearance import FloatingPanel, apply_appearance, configure_button, icon
from .capture import save_capture
from .chrome import QuietControls
from .controls import VideoControls
from .dialogs import AboutDialog, HelpDialog
from .folder_browser import FolderBrowser
from .folder_navigator import AUDIO_SUFFIXES, IMAGE_SUFFIXES, VIDEO_SUFFIXES, navigation_steps
from .navigation import NavigationAttempt
from .settings import Preferences, SettingsDialog
from .update_feature import UpdateFeatureMixin
from .viewport import MediaViewport


class MediaCanvas(QWidget):
    """The GL surface always fills the canvas; floating siblings never resize it."""

    def __init__(self, viewport, parent):
        super().__init__(parent)
        self.viewport = viewport
        viewport.setParent(self)
        viewport.lower()

    def resizeEvent(self, event):
        self.viewport.setGeometry(self.rect())
        self.window().position_overlays()
        super().resizeEvent(event)


class Window(UpdateFeatureMixin, QMainWindow):
    def __init__(self, preferences=None):
        super().__init__()
        self.setWindowTitle("AMP")
        self.resize(960, 640)
        self.current_path = None
        self.pending_capture = None
        self.navigation_attempt = None
        self.fullscreen_timer = QTimer(self)
        self.fullscreen_timer.setSingleShot(True)
        self.fullscreen_timer.setInterval(60)
        self.fullscreen_timer.timeout.connect(self._finish_fullscreen)
        self.fullscreen_was_maximized = False
        self.preferences = preferences or Preferences()
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.viewport = MediaViewport(self)
        body = MediaCanvas(self.viewport, self)
        self.setMinimumSize(500, 260)
        self.setCentralWidget(body)
        self.viewport.failed.connect(self.notify)
        self.viewport.media_failed.connect(self.media_failed)
        self.viewport.fullscreen_requested.connect(self.toggle_fullscreen)
        self.viewport.navigation_requested.connect(self.navigate)
        self.viewport.wheel_mode_changed.connect(self.wheel_mode_changed)
        self.viewport.set_wheel_navigation(self.preferences.wheel_navigation)

        self.actions_by_name = {}
        self.media_menu = QMenu(self)
        for text, shortcut, callback in (
            ("Open file", "Ctrl+O", self.choose),
            ("New window", "Ctrl+N", self.new_window),
            ("Previous", "", lambda: self.navigate(-1)),
            ("Next", "", lambda: self.navigate(1)),
            ("Reset fit", "R", self.viewport.reset),
            ("Screenshot", "S", self.screenshot),
            ("Fullscreen", "F11", self.toggle_fullscreen),
            ("Play / pause", "Space", self.pause),
        ):
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.setToolTip(f"{text} ({shortcut})" if shortcut else text)
            action.triggered.connect(callback)
            self.addAction(action)
            if text == "New window":
                self.media_menu.addAction(action)
            self.actions_by_name[text] = action
        self.actions_by_name["Play / pause"].setVisible(False)
        self.actions_by_name["Fullscreen"].setAutoRepeat(False)
        self.actions_by_name["Screenshot"].setEnabled(False)
        self.actions_by_name["Reset fit"].setEnabled(False)
        self.lyrics_action = self.media_menu.addAction("Show lyrics")
        self.lyrics_action.setCheckable(True)
        self.lyrics_action.setChecked(True)
        self.lyrics_action.setShortcut("L")
        self.lyrics_action.setVisible(False)
        self.lyrics_action.toggled.connect(self.viewport.toggle_lyrics)
        self.addAction(self.lyrics_action)
        self.media_menu.addSeparator()
        settings_action = self.media_menu.addAction("Settings", self.settings)
        settings_action.setShortcut("Ctrl+,")
        self.addAction(settings_action)
        self.media_menu.addAction("Keyboard shortcuts", self.help)
        self.media_menu.addAction("Check for updates", self.check_for_updates)
        self.media_menu.addAction("About AMP / licences", self.about)
        self.setup_update_feature()
        self.viewport.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.viewport.customContextMenuRequested.connect(
            lambda point: self.media_menu.popup(self.viewport.mapToGlobal(point))
        )

        def action_button(parent, action_name, symbol):
            button = QToolButton(parent)
            self.actions_by_name[action_name].setIcon(icon(symbol))
            self.actions_by_name[action_name].setIconVisibleInMenu(False)
            button.setDefaultAction(self.actions_by_name[action_name])
            configure_button(
                button, action_name, symbol, self.actions_by_name[action_name].shortcut().toString()
            )
            return button

        self.filename = QLabel(body)
        self.filename.setObjectName("filename")
        self.filename.setMaximumWidth(260)
        self.filename.hide()
        self.open_media = FloatingPanel(body)
        open_layout = QHBoxLayout(self.open_media)
        open_layout.setContentsMargins(4, 3, 6, 3)
        self.open_media_button = QToolButton(self.open_media)
        configure_button(self.open_media_button, "Open media", "open", "Ctrl+B")
        self.open_media_button.setCheckable(True)
        self.open_media_button.toggled.connect(self.toggle_browser)
        self.open_media_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.open_media_button.setFixedWidth(112)
        self.open_media_button.setToolTip("Show or hide folders and media (Ctrl+B)")
        open_layout.addWidget(self.open_media_button)
        self.folder_browser = FolderBrowser(body)
        self.folder_browser.file_requested.connect(self.open_path)
        self.folder_browser.picker_requested.connect(self.choose)
        self.folder_browser.close_requested.connect(
            lambda: self.open_media_button.setChecked(False)
        )
        self.folder_browser.failed.connect(self.notify)
        self.folder_browser.interacted.connect(self.viewport.setFocus)
        browser_action = QAction("Show / hide folder browser", self)
        browser_action.setShortcut("Ctrl+B")
        browser_action.triggered.connect(self.open_media_button.toggle)
        self.addAction(browser_action)
        self.toolbar = FloatingPanel(body)
        self.toolbar.setObjectName("toolDock")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(4, 3, 4, 3)
        toolbar_layout.setSpacing(2)
        toolbar_layout.addWidget(action_button(self.toolbar, "Fullscreen", "fullscreen"))
        self.menu_button = QToolButton(self.toolbar)
        configure_button(self.menu_button, "Menu", "more")
        self.menu_button.setMenu(self.media_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        toolbar_layout.addWidget(self.menu_button)

        self.loop_notice = QLabel(body)
        self.loop_notice.setObjectName("loopNotice")
        self.loop_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loop_notice.setWordWrap(True)
        self.loop_notice.hide()
        self.loop_timer = QTimer(self)
        self.loop_timer.setSingleShot(True)
        self.loop_timer.timeout.connect(self.loop_notice.hide)
        self.notice = QLabel(body)
        self.notice.setObjectName("notice")
        self.notice.setWordWrap(True)
        self.notice.setMaximumWidth(620)
        self.notice.hide()
        self.notice_timer = QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self.notice.hide)
        self.hover_hint = QLabel(body)
        self.hover_hint.setObjectName("hoverHint")
        self.hover_hint.setTextFormat(Qt.TextFormat.PlainText)
        self.hover_hint.setWordWrap(True)
        self.hover_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hover_hint.hide()
        self.hover_widget = None
        # Keep status text available to diagnostics, without reserving any canvas.
        self.statusBar().hide()

        self.controls = VideoControls(body)
        self.controls.volume.setValue(self.preferences.volume)
        self.controls.update_property("mute", self.preferences.muted)
        self.controls.hide()
        self.controls.pause_requested.connect(self.pause)
        self.controls.previous_requested.connect(lambda: self.navigate(-1))
        self.controls.next_requested.connect(lambda: self.navigate(1))
        self.controls.seek_requested.connect(self.seek)
        self.controls.volume_requested.connect(lambda value: self.video_set("volume", value))
        self.controls.mute_requested.connect(self.set_muted)
        self.controls.subtitles_requested.connect(
            lambda visible: self.video_set("sub-visibility", visible)
        )
        self.controls.speed_requested.connect(lambda value: self.video_set("speed", value))
        self.viewport.video_changed.connect(self.controls.update_property)
        # Navigation stays in one physical location for every media type.
        self.controls.previous.hide()
        self.controls.next.hide()
        self.previous_button = action_button(body, "Previous", "previous")
        self.next_button = action_button(body, "Next", "next")
        self.previous_button.hide()
        self.next_button.hide()
        self.image_dock = FloatingPanel(body)
        self.image_dock.setObjectName("imageDock")
        image_layout = QHBoxLayout(self.image_dock)
        image_layout.setContentsMargins(7, 5, 7, 5)
        image_layout.setSpacing(5)
        for name, symbol in (("Reset fit", "reset"), ("Screenshot", "capture")):
            image_layout.addWidget(action_button(self.image_dock, name, symbol))
        self.image_dock.hide()

        self.empty = QWidget(body)
        self.empty.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        empty_layout = QVBoxLayout(self.empty)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(12)
        title = QLabel("AMP")
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(title)
        subtitle = QLabel("Images  \u00b7  video  \u00b7  music")
        subtitle.setObjectName("emptySubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(subtitle)
        empty_layout.addSpacing(10)
        open_button = QPushButton("Open a file")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(self.choose)
        empty_layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        hint = QLabel("or drop it here  \u00b7  Ctrl+O")
        hint.setObjectName("emptyHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint)
        panels = [
            self.filename,
            self.toolbar,
            self.controls,
            self.image_dock,
            self.previous_button,
            self.next_button,
            self.open_media,
            self.folder_browser,
        ]
        self.filename.setProperty("passThrough", True)
        self.chrome = QuietControls(self, panels)
        for label in (self.notice, self.loop_notice):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        for widget in self.findChildren(QWidget):
            widget.setMouseTracking(True)
        self.viewport.setFocus()
        QApplication.instance().installEventFilter(self)
        self.position_overlays()

    def notify(self, message):
        self.statusBar().showMessage(message)
        self.notice.setText(message)
        self.notice.show()
        self.notice_timer.start(6000)
        self.position_overlays()

    def position_overlays(self):
        if not hasattr(self, "chrome"):
            return
        width, height = self.centralWidget().width(), self.centralWidget().height()
        self.toolbar.adjustSize()
        self.toolbar.move(width - 16 - self.toolbar.width(), 16)
        self.open_media.adjustSize()
        self.open_media.move(self.toolbar.x() - self.open_media.width() - 6, 16)
        self.filename.adjustSize()
        self.filename.move(16, 18)
        self.folder_browser.setGeometry(
            max(16, width - 356), 64, min(340, width - 32), max(140, height - 176)
        )
        self.controls.resize(min(760, width - 32), self.controls.sizeHint().height())
        self.controls.move(
            (width - self.controls.width()) // 2, height - self.controls.height() - 16
        )
        self.image_dock.adjustSize()
        self.image_dock.move(
            (width - self.image_dock.width()) // 2, height - self.image_dock.height() - 16
        )
        self.previous_button.move(16, (height - self.previous_button.height()) // 2)
        self.next_button.move(
            width - self.next_button.width() - 16,
            (height - self.next_button.height()) // 2,
        )
        self.empty.adjustSize()
        self.empty.move((width - self.empty.width()) // 2, (height - self.empty.height()) // 2)
        dock = self.controls if self.controls.isVisible() else self.image_dock
        bottom = dock.y() - 12 if dock.isVisible() else height - 24
        for notice in (self.notice, self.loop_notice):
            if notice.isVisible():
                notice.adjustSize()
                notice.move((width - notice.width()) // 2, bottom - notice.height())
                bottom = notice.y() - 8

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fullscreen_timer.isActive():
            self.fullscreen_timer.start()
        if hasattr(self, "filename"):
            width = min(260, max(80, self.width() - 320))
            self.filename.setMaximumWidth(width)
            if self.current_path:
                self.filename.setText(
                    self.fontMetrics().elidedText(
                        self.current_path.name, Qt.TextElideMode.ElideMiddle, width - 20
                    )
                )
            self.notice.setMaximumWidth(max(200, min(620, self.width() - 48)))
            self.loop_notice.setMaximumWidth(max(200, self.width() - 48))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.fullscreen_timer.isActive():
            # Keep input/capture guarded until native state and geometry settle.
            # Rendering must continue throughout the transition.
            self.fullscreen_timer.start()

    def help(self):
        HelpDialog(self).exec()

    def settings(self):
        automatic_updates_were_enabled = self.preferences.auto_updates
        dialog = SettingsDialog(self.preferences, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.preferences.save(
                    dialog.repeat.isChecked(),
                    dialog.volume.value(),
                    dialog.banner.value(),
                    dialog.wheel_navigation.isChecked(),
                    dialog.auto_updates.isChecked(),
                )
                self.viewport.set_wheel_navigation(self.preferences.wheel_navigation)
                self.video_set("loop-file", "inf" if self.preferences.repeat else "no")
                if self.loop_timer.isActive():
                    self.loop_timer.start(self.preferences.banner_seconds * 1000)
                self.notify("Settings saved locally.")
                if self.preferences.auto_updates and not automatic_updates_were_enabled:
                    self.start_automatic_update_check()
            except OSError as error:
                self.notify(str(error))
        self.chrome.reveal()

    def wheel_mode_changed(self, zoom_mode):
        if self.viewport.audio and zoom_mode:
            self.notify("Wheel zoom is unavailable for music; middle-click returns to navigation.")
        else:
            self.notify(
                "Mouse wheel: zoom · middle-click returns to previous / next"
                if zoom_mode
                else "Mouse wheel: previous / next · middle-click switches to zoom"
            )

    def about(self):
        AboutDialog(self).exec()

    def choose(self):
        suffixes = sorted(IMAGE_SUFFIXES | VIDEO_SUFFIXES | AUDIO_SUFFIXES)
        patterns = " ".join(f"*{suffix}" for suffix in suffixes)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open local media",
            str(self.current_path.parent) if self.current_path else "",
            f"Supported media ({patterns});;All files (*)",
        )
        if path:
            self.open_path(path)

    def toggle_browser(self, visible):
        browser = self.folder_browser
        if visible:
            directory = browser.directory or (
                self.current_path.parent if self.current_path else Path.home()
            )
            browser.set_directory(directory)
        browser.setVisible(visible)
        self.viewport.setFocus()
        self.chrome.reveal()
        self.position_overlays()

    def open_path(self, path, *, navigating=False):
        if not navigating:
            self.navigation_attempt = None
        try:
            path = Path(path).expanduser().resolve()
            if not path.is_file():
                raise RuntimeError("The selected local file is unavailable.")
            playback_options = {
                "volume": self.controls.volume_level,
                "mute": self.controls.mute.isChecked(),
                "loop-file": "inf" if self.preferences.repeat else "no",
                "speed": 1.0,
            }
            if path.suffix.lower() in IMAGE_SUFFIXES:
                self.viewport.open_image(path)
            elif path.suffix.lower() in VIDEO_SUFFIXES:
                self.viewport.open_video(path, playback_options=playback_options)
            elif path.suffix.lower() in AUDIO_SUFFIXES:
                self.viewport.open_audio(path, playback_options=playback_options)
            else:
                raise RuntimeError("Choose a supported local image, video or music file.")
            self.setWindowTitle(f"{path.name} — AMP")
            self.current_path = path
            self.folder_browser.follow(path)
            self.empty.hide()
            self.filename.show()
            self.notice_timer.stop()
            self.notice.hide()
            self.statusBar().clearMessage()
            self.filename.setText(
                self.fontMetrics().elidedText(path.name, Qt.TextElideMode.ElideMiddle, 210)
            )
            self.filename.setToolTip(path.name)
            self.loop_timer.stop()
            self.loop_notice.hide()
            self.controls.setVisible(self.viewport.playable)
            self.lyrics_action.setVisible(self.viewport.audio)
            self.controls.speed_panel.setVisible(self.viewport.playable and not self.viewport.audio)
            self.controls.update_property("speed", 1.0)
            self.image_dock.setVisible(not self.viewport.playable)
            self.previous_button.show()
            self.next_button.show()
            self.actions_by_name["Play / pause"].setVisible(self.viewport.playable)
            self.actions_by_name["Screenshot"].setEnabled(not self.viewport.audio)
            self.actions_by_name["Reset fit"].setEnabled(not self.viewport.audio)
            self.controls.update_property("duration", 0)
            self.controls.update_property("time-pos", 0)
            self.controls.update_property("eof-reached", False)
            self.controls.update_property("pause", False)
            self.controls.update_property("track-list", [])
            self.controls.update_property("sub-visibility", False)
            self.open_media_button.setChecked(False)
            self.chrome.reveal()
            self.position_overlays()
            if path.suffix.lower() in {".gif", ".tif", ".tiff"}:
                self.notify("Showing the first frame/page · wheel zoom · drag pan · R reset")
            return True
        except (RuntimeError, OSError, ValueError) as error:
            self.notify(str(error))
            return False

    def navigate(self, direction):
        if self.current_path is None:
            return
        try:
            self.navigation_attempt = NavigationAttempt(
                list(navigation_steps(self.current_path, direction)), direction
            )
            self._continue_navigation()
        except OSError:
            self.navigation_attempt = None
            self.notify("This folder is unavailable. Open another local file.")

    def _continue_navigation(self):
        attempt = self.navigation_attempt
        while attempt is not None:
            path = attempt.next()
            if path is None:
                self.navigation_attempt = None
                self.notify("No other readable supported files in this folder.")
                return
            if self.open_path(path, navigating=True):
                if attempt.wrapped:
                    self.loop_notice.setText(attempt.message())
                    self.loop_notice.show()
                    self.position_overlays()
                    self.loop_timer.start(self.preferences.banner_seconds * 1000)
                if attempt.message():
                    if attempt.wrapped:
                        self.statusBar().showMessage(attempt.message())
                    else:
                        self.notify(attempt.message())
                # Retain the remaining candidates for asynchronous decoder errors.
                if not self.viewport.playable:
                    self.navigation_attempt = None
                return
            attempt.skipped += 1

    def media_failed(self, message):
        if self.navigation_attempt is not None:
            self.navigation_attempt.skipped += 1
            self._continue_navigation()
        else:
            self.notify(f"{message} Use Left/Right or open another local file.")

    def set_muted(self, muted):
        self.video_set("mute", muted)
        try:
            self.preferences.save_mute(muted)
        except OSError as error:
            self.notify(str(error))

    def video_set(self, name, value):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.set(name, value)

    def pause(self):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.toggle_playback()

    def seek(self, seconds, mode):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.seek(seconds, mode)

    def screenshot(self):
        try:
            if self.pending_capture is None:
                if self.fullscreen_timer.isActive():
                    raise RuntimeError("The media view is updating. Try again in a moment.")
                self.pending_capture = self.viewport.capture()
            path = save_capture(self.pending_capture)
            self.pending_capture = None
            self.notify(f"Saved {path.name} in Pictures/AMP")
        except (RuntimeError, OSError) as error:
            retry = (
                "S retries the retained capture"
                if self.pending_capture is not None
                else "Try S again when the media view is ready"
            )
            self.notify(f"Screenshot failed: {error} · {retry}")
        except MemoryError:
            self.notify("Screenshot failed: not enough memory. Try a smaller window.")

    def new_window(self):
        window = Window()
        # The QApplication keeps no Python ownership of top-level widgets.
        windows = QApplication.instance().amp_windows
        windows.append(window)
        window.destroyed.connect(lambda: windows.remove(window) if window in windows else None)
        window.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.open_path(url.toLocalFile())
                event.acceptProposedAction()
                break

    def eventFilter(self, watched, event):
        if isinstance(watched, QWidget) and watched.window() is self:
            if event.type() == QEvent.Type.ToolTip:
                text = watched.toolTip()
                if watched is self.folder_browser.files.viewport():
                    item = self.folder_browser.files.itemAt(event.pos())
                    text = item.toolTip() if item else ""
                if text:
                    self.hover_widget = watched
                    self.hover_hint.setMaximumWidth(min(360, self.centralWidget().width() - 32))
                    self.hover_hint.setText(text)
                    self.hover_hint.adjustSize()
                    point = watched.mapTo(self.centralWidget(), QPoint(0, watched.height() + 8))
                    x = max(
                        16,
                        min(point.x(), self.centralWidget().width() - self.hover_hint.width() - 16),
                    )
                    y = point.y()
                    if y + self.hover_hint.height() > self.centralWidget().height() - 16:
                        y = (
                            watched.mapTo(self.centralWidget(), QPoint()).y()
                            - self.hover_hint.height()
                            - 8
                        )
                    self.hover_hint.move(x, max(16, y))
                    self.hover_hint.show()
                    self.hover_hint.raise_()
                event.accept()
                return True
            if event.type() in (
                QEvent.Type.MouseButtonPress,
                QEvent.Type.KeyPress,
                QEvent.Type.WindowDeactivate,
            ) or (event.type() == QEvent.Type.Leave and watched is self.hover_widget):
                self.hover_hint.hide()
        if (
            isinstance(watched, QWidget)
            and watched.window() is self
            and event.type()
            in (
                QEvent.Type.MouseMove,
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.Wheel,
                QEvent.Type.KeyPress,
                QEvent.Type.FocusIn,
            )
        ):
            self.chrome.reveal()
        if (
            isinstance(watched, QWidget)
            and watched.window() is self
            and event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress)
        ):
            key = event.key()
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Escape, Qt.Key.Key_F):
                if event.type() == QEvent.Type.KeyPress:
                    if key == Qt.Key.Key_Left:
                        self.navigate(-1)
                    elif key == Qt.Key.Key_Right:
                        self.navigate(1)
                    elif key == Qt.Key.Key_Escape and self.isFullScreen():
                        self.set_fullscreen(False)
                    elif key == Qt.Key.Key_F and not event.isAutoRepeat():
                        self.toggle_fullscreen()
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def toggle_fullscreen(self):
        if not self.fullscreen_timer.isActive():
            self.set_fullscreen(not self.isFullScreen())

    def set_fullscreen(self, fullscreen):
        if fullscreen == self.isFullScreen():
            return
        self.hover_hint.hide()
        # Never suspend the top-level backing store here. QOpenGLWidget needs
        # to repaint each native resize; withholding those frames exposes stale
        # or blank surfaces while Windows changes the window decorations.
        self.fullscreen_timer.start()
        if fullscreen:
            self.fullscreen_was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self.fullscreen_was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.chrome.reveal()

    def _finish_fullscreen(self):
        self.position_overlays()
        self.viewport.update()

    def closeEvent(self, event):
        self.fullscreen_timer.stop()
        self.stop_update_check()
        self.viewport.cleanup()
        event.accept()


def create_application():
    if sys.platform == "win32":
        # Give source and standalone windows the same Windows taskbar identity.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WolfForge.AMP")
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("AMP")
    app.setOrganizationName("AMP")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "assets/amp.ico")))
    apply_appearance(app)
    app.amp_windows = []
    return app


def main():
    parser = argparse.ArgumentParser(description="AMP — local image, video and music player")
    parser.add_argument("path", nargs="?", help="local image, video or music file")
    args = parser.parse_args()
    app = create_application()
    window = Window()
    window.show()
    QTimer.singleShot(2000, window.start_automatic_update_check)
    if args.path:
        QTimer.singleShot(100, lambda: window.open_path(args.path))
    return app.exec()
