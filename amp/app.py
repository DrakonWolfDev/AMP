# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Small application shell used while the renderer gate is under validation."""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QSurfaceFormat
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .capture import save_capture
from .controls import VideoControls
from .folder_navigator import AUDIO_SUFFIXES, IMAGE_SUFFIXES, VIDEO_SUFFIXES, navigation_steps
from .navigation import NavigationAttempt
from .viewport import MediaViewport


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMP — renderer preview")
        self.resize(960, 640)
        self.current_path = None
        self.pending_capture = None
        self.navigation_attempt = None
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.viewport = MediaViewport(self)
        body = QWidget(self)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.loop_notice = QLabel(self)
        self.loop_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loop_notice.setStyleSheet(
            "background: #f6ce73; color: #242018; padding: 10px; font-weight: bold;"
        )
        self.loop_notice.hide()
        layout.addWidget(self.loop_notice)
        self.loop_timer = QTimer(self)
        self.loop_timer.setSingleShot(True)
        self.loop_timer.timeout.connect(self.loop_notice.hide)
        layout.addWidget(self.viewport, 1)
        self.controls = VideoControls(self)
        self.controls.hide()
        self.controls.pause_requested.connect(self.pause)
        self.controls.seek_requested.connect(self.seek)
        self.controls.volume_requested.connect(lambda value: self.video_set("volume", value))
        self.controls.mute_requested.connect(lambda value: self.video_set("mute", value))
        self.viewport.video_changed.connect(self.controls.update_property)
        layout.addWidget(self.controls)
        self.setCentralWidget(body)
        self.viewport.failed.connect(self.notify)
        self.viewport.media_failed.connect(self.media_failed)
        self.viewport.fullscreen_requested.connect(self.toggle_fullscreen)
        toolbar = QToolBar("Media", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.menuBar().addMenu("Help").addAction("About AMP / licences", self.about)
        self.actions_by_name = {}
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
            action.triggered.connect(callback)
            toolbar.addAction(action)
            self.actions_by_name[text] = action
        self.statusBar().showMessage(
            "Open local images, videos or music · Left/Right browse the folder"
        )
        QApplication.instance().installEventFilter(self)

    def notify(self, message):
        self.statusBar().showMessage(message)

    def about(self):
        QMessageBox.about(
            self,
            "About AMP",
            "AMP — Andy's Media Player\n\n"
            "Copyright © 2026 Andrew Hodgson trading as Wolf Forge.\n\n"
            "AMP is free software under the GNU Affero General Public License, "
            "version 3 only (AGPL-3.0-only). You may use, modify and redistribute "
            "it under that licence. AMP comes with no warranty.\n\n"
            "See LICENSE for the full terms and THIRD_PARTY_NOTICES.md and "
            "LICENSES for the separate dependency licences. Copies of those "
            "files accompany the source and Python distribution.",
        )

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

    def open_path(self, path, *, navigating=False):
        if not navigating:
            self.navigation_attempt = None
        try:
            path = Path(path).expanduser().resolve()
            if not path.is_file():
                raise RuntimeError("The selected local file is unavailable.")
            if path.suffix.lower() in IMAGE_SUFFIXES:
                self.viewport.open_image(path)
            elif path.suffix.lower() in VIDEO_SUFFIXES:
                self.viewport.open_video(path)
            elif path.suffix.lower() in AUDIO_SUFFIXES:
                self.viewport.open_audio(path)
            else:
                raise RuntimeError("Choose a supported local image, video or music file.")
            self.setWindowTitle(f"{path.name} — AMP")
            self.current_path = path
            self.loop_timer.stop()
            self.loop_notice.hide()
            self.controls.setVisible(self.viewport.playable)
            self.actions_by_name["Screenshot"].setEnabled(not self.viewport.audio)
            self.actions_by_name["Reset fit"].setEnabled(not self.viewport.audio)
            self.controls.update_property("duration", 0)
            self.controls.update_property("time-pos", 0)
            self.controls.update_property("eof-reached", False)
            self.controls.update_property("pause", False)
            if self.viewport.playable:
                self.video_set("volume", self.controls.volume.value())
                self.video_set("mute", self.controls.mute.isChecked())
            self.notify(
                "Space play/pause · Left/Right browse the folder"
                if self.viewport.audio
                else "Wheel zoom · drag pan · R reset"
            )
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
                    self.loop_timer.start(3000)
                if attempt.message():
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
                        self.showNormal()
                    elif key == Qt.Key.Key_F:
                        self.toggle_fullscreen()
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def closeEvent(self, event):
        self.viewport.cleanup()
        event.accept()


def create_application():
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("AMP")
    app.setOrganizationName("AMP")
    app.amp_windows = []
    return app


def main():
    parser = argparse.ArgumentParser(description="AMP — local image, video and music player")
    parser.add_argument("path", nargs="?", help="local image, video or music file")
    args = parser.parse_args()
    app = create_application()
    window = Window()
    window.show()
    if args.path:
        QTimer.singleShot(100, lambda: window.open_path(args.path))
    return app.exec()
