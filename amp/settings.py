# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Small local preferences; no media paths or playback state are persisted."""

from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
)

from .dialogs import ProjectDialog, label


class Preferences:
    def __init__(self, path=None):
        self.path = (
            Path(path)
            if path
            else Path(
                QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
            )
            / "preferences.ini"
        )
        self.store = QSettings(str(self.path), QSettings.Format.IniFormat)
        self.repeat = str(self.store.value("repeat", "false")).lower() == "true"
        self.muted = str(self.store.value("muted", "false")).lower() == "true"
        self.volume = self._integer("default_volume", 100, 0, 100)
        self.banner_seconds = self._integer("banner_seconds", 3, 1, 10)

    def _integer(self, key, default, minimum, maximum):
        try:
            return max(minimum, min(maximum, int(self.store.value(key, default))))
        except (ValueError, TypeError, OverflowError):
            return default

    def save_mute(self, muted):
        self.store.setValue("muted", bool(muted))
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Mute preference could not be saved. Check the local settings folder.")
        self.muted = bool(muted)

    def save(self, repeat, volume, banner_seconds):
        self.store.setValue("repeat", bool(repeat))
        self.store.setValue("default_volume", volume)
        self.store.setValue("banner_seconds", banner_seconds)
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Preferences could not be saved. Check the local settings folder.")
        self.repeat, self.volume, self.banner_seconds = repeat, volume, banner_seconds


class SettingsDialog(ProjectDialog):
    def __init__(self, preferences, parent):
        super().__init__("Settings", "Small preferences, stored only on this device.", parent)
        layout = QFormLayout()
        layout.setVerticalSpacing(18)
        self.content.addWidget(label("PLAYBACK", "dialogEyebrow"))
        self.content.addLayout(layout)
        self.repeat = QCheckBox("Repeat the current video or music file")
        self.repeat.setChecked(preferences.repeat)
        layout.addRow(self.repeat)
        self.volume = QSpinBox()
        self.volume.setRange(0, 100)
        self.volume.setSuffix(" %")
        self.volume.setValue(preferences.volume)
        self.volume.setFixedWidth(110)
        self.volume.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        layout.addRow("Default volume for new windows", self.volume)
        self.banner = QSpinBox()
        self.banner.setRange(1, 10)
        self.banner.setSuffix(" s")
        self.banner.setValue(preferences.banner_seconds)
        self.banner.setFixedWidth(110)
        self.banner.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        layout.addRow("Folder wrap notice", self.banner)
        note = label(
            "Repeat applies to this window now and to new windows.\n"
            "Other open windows keep their current playback and preferences.",
            "dialogNote",
        )
        note.setWordWrap(True)
        self.content.addWidget(note)
        self.buttons.setStandardButtons(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setDefault(True)
        self.resize(self.width(), min(510, self.screen().availableGeometry().height() - 70))
