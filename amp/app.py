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
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .capture import save_capture
from .controls import VideoControls
from .folder_navigator import AUDIO_SUFFIXES, IMAGE_SUFFIXES, VIDEO_SUFFIXES, navigation_steps
from .viewport import MediaViewport


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMP — renderer preview")
        self.resize(960, 640)
        self.current_path = None
        self.pending_capture = None
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
        self.viewport.fullscreen_requested.connect(self.toggle_fullscreen)
        toolbar = QToolBar("Media", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
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

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open local media")
        if path:
            self.open_path(path)

    def open_path(self, path):
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
            if self.viewport.playable:
                self.video_set("volume", self.controls.volume.value())
                self.video_set("mute", self.controls.mute.isChecked())
            self.notify(
                "Space play/pause · Left/Right browse the folder"
                if self.viewport.audio
                else "Wheel zoom · drag pan · R reset"
            )
            return True
        except (RuntimeError, OSError, ValueError) as error:
            self.notify(str(error))
            return False

    def navigate(self, direction):
        if self.current_path is None:
            return
        skipped = 0
        try:
            for step in navigation_steps(self.current_path, direction):
                if self.open_path(step.path):
                    message = f"Skipped {skipped} unreadable file(s)." if skipped else ""
                    if step.wrapped:
                        boundary = "beginning" if direction > 0 else "end"
                        clue = f"↻ Folder looped — back to the {boundary}"
                        self.loop_notice.setText(clue)
                        self.loop_notice.show()
                        self.loop_timer.start(6000)
                        message = f"{clue}. {message}".strip()
                    if message:
                        self.notify(message)
                    return
                skipped += 1
            self.notify("No other readable supported files in this folder.")
        except OSError:
            self.notify("This folder is unavailable. Open another local file.")

    def video_set(self, name, value):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.set(name, value)

    def pause(self):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.command("cycle", "pause")

    def seek(self, seconds, mode):
        if self.viewport.playable and self.viewport.backend:
            self.viewport.backend.command("seek", seconds, mode)

    def screenshot(self):
        try:
            if self.pending_capture is None:
                self.pending_capture = self.viewport.capture()
            path = save_capture(self.pending_capture)
            self.pending_capture = None
            self.notify(f"Saved {path.name} in Pictures/AMP")
        except (RuntimeError, OSError) as error:
            self.notify(f"Screenshot failed: {error} · S retries the retained capture")

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
