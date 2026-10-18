# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""An explicit, single-folder browser. No index, watchers or recursive reads."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from .appearance import FloatingPanel, icon
from .folder_navigator import IMAGE_SUFFIXES, SUPPORTED_SUFFIXES, natural_key


def folder_entries(directory):
    entries = []
    for path in Path(directory).iterdir():
        try:
            directory_entry = path.is_dir()
            if directory_entry or (path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES):
                entries.append((path, directory_entry))
        except OSError:
            continue
    return sorted(entries, key=lambda entry: (not entry[1], natural_key(entry[0])))


class FolderList(QListWidget):
    activated_path = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.itemClicked.connect(self._activate)
        self.setAccessibleName("Folders and media files")

    def _activate(self, item):
        if item:
            self.activated_path.emit(Path(item.data(Qt.ItemDataRole.UserRole)))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._activate(self.currentItem())
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()  # A single click already opens the item.


class FolderBrowser(FloatingPanel):
    file_requested = Signal(object)
    picker_requested = Signal()
    close_requested = Signal()
    failed = Signal(str)
    interacted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.directory = None
        self.current_path = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 10)
        layout.setSpacing(6)
        header = QHBoxLayout()
        self.title = QLabel("Folder")
        self.title.setMinimumWidth(0)
        header.addWidget(self.title, 1)
        close = QToolButton()
        close.setText("×")
        close.setAccessibleName("Close folder browser")
        close.setFixedSize(28, 28)
        close.clicked.connect(self.close_requested)
        header.addWidget(close)
        layout.addLayout(header)
        navigation = QHBoxLayout()
        self.up = QPushButton("Up")
        self.up.setAccessibleName("Parent folder")
        self.up.clicked.connect(self.parent_folder)
        navigation.addWidget(self.up)
        choose = QPushButton("Choose folder…")
        choose.clicked.connect(self.choose_folder)
        navigation.addWidget(choose)
        refresh = QToolButton()
        refresh.setText("↻")
        refresh.setAccessibleName("Refresh this folder")
        refresh.setToolTip("Refresh this folder")
        refresh.setFixedSize(28, 28)
        refresh.clicked.connect(lambda: self.set_directory(self.directory))
        navigation.addWidget(refresh)
        layout.addLayout(navigation)
        self.files = FolderList()
        self.files.setObjectName("folderFiles")
        self.files.activated_path.connect(self.activate)
        layout.addWidget(self.files, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.picker = QPushButton("Choose a file…  (Ctrl+O)")
        self.picker.clicked.connect(self.picker_requested)
        layout.addWidget(self.picker)
        for button in self.findChildren(QPushButton) + self.findChildren(QToolButton):
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "picker"):
            self.status.setVisible(self.height() >= 220)
            self.picker.setVisible(self.height() >= 220)

    def set_directory(self, directory):
        if directory is None:
            return False
        try:
            directory = Path(directory).expanduser().resolve()
            entries = folder_entries(directory)
        except (OSError, RuntimeError):
            self.failed.emit("This folder is unavailable. Choose another folder.")
            return False
        self.directory = directory
        self.title.setText(directory.name or str(directory))
        self.title.setToolTip(str(directory))
        self.up.setEnabled(directory.parent != directory)
        self.files.clear()
        for path, is_directory in entries:
            symbol = (
                "open"
                if is_directory
                else "capture"
                if path.suffix.lower() in IMAGE_SUFFIXES
                else "play"
            )
            item = QListWidgetItem(icon(symbol), path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.files.addItem(item)
        self.status.setText(
            "Click to open · folders first" if entries else "No supported media or subfolders here."
        )
        self.mark_current()
        return True

    def mark_current(self):
        for index in range(self.files.count()):
            item = self.files.item(index)
            current = self.current_path == Path(item.data(Qt.ItemDataRole.UserRole))
            font = item.font()
            font.setBold(current)
            item.setFont(font)
            item.setForeground(QColor("#e9d1a8" if current else "#dce0e6"))
            if current:
                self.files.setCurrentItem(item)

    def follow(self, path):
        self.current_path = Path(path)
        if not self.isVisible() and self.directory != self.current_path.parent:
            self.directory = None
            return
        if self.isVisible() and self.directory != self.current_path.parent:
            self.set_directory(self.current_path.parent)
        else:
            self.mark_current()

    def activate(self, path):
        try:
            if path.is_dir():
                self.set_directory(path)
            else:
                self.file_requested.emit(path)
        except OSError:
            self.failed.emit("This item is unavailable. Refresh or choose another folder.")
        self.interacted.emit()

    def parent_folder(self):
        if self.directory:
            self.set_directory(self.directory.parent)
            self.interacted.emit()

    def choose_folder(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Choose a media folder", str(self.directory or Path.home())
        )
        if directory:
            self.set_directory(directory)
        self.interacted.emit()
