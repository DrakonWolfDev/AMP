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
    QMessageBox,
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
        legacy_repeat = str(self.store.value("repeat", "false")).lower() == "true"
        self.repeat_video = self._boolean("repeat_video", legacy_repeat)
        self.repeat_music = self._boolean("repeat_music", legacy_repeat)
        self.muted = str(self.store.value("muted", "false")).lower() == "true"
        self.volume = self._integer("default_volume", 100, 0, 100)
        self.banner_seconds = self._integer("banner_seconds", 3, 1, 10)
        self.wheel_navigation = str(self.store.value("wheel_navigation", "false")).lower() == "true"
        self.auto_updates = str(self.store.value("auto_updates", "false")).lower() == "true"
        self.update_last_successful_check = self.store.value("update_last_successful_check")
        self.update_dismissed_version = self.store.value("update_dismissed_version")

    def _integer(self, key, default, minimum, maximum):
        try:
            return max(minimum, min(maximum, int(self.store.value(key, default))))
        except (ValueError, TypeError, OverflowError):
            return default

    def _boolean(self, key, default=False):
        return str(self.store.value(key, str(default).lower())).lower() == "true"

    def save_mute(self, muted):
        self.store.setValue("muted", bool(muted))
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Mute preference could not be saved. Check the local settings folder.")
        self.muted = bool(muted)

    def save(
        self,
        repeat_video,
        repeat_music,
        volume,
        banner_seconds,
        wheel_navigation=None,
        auto_updates=None,
    ):
        self.store.setValue("repeat_video", bool(repeat_video))
        self.store.setValue("repeat_music", bool(repeat_music))
        self.store.setValue("default_volume", volume)
        self.store.setValue("banner_seconds", banner_seconds)
        if wheel_navigation is not None:
            self.store.setValue("wheel_navigation", bool(wheel_navigation))
        if auto_updates is not None:
            self.store.setValue("auto_updates", bool(auto_updates))
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Preferences could not be saved. Check the local settings folder.")
        self.repeat_video, self.repeat_music = bool(repeat_video), bool(repeat_music)
        self.volume, self.banner_seconds = volume, banner_seconds
        if wheel_navigation is not None:
            self.wheel_navigation = bool(wheel_navigation)
        if auto_updates is not None:
            self.auto_updates = bool(auto_updates)

    def save_update_state(self, last_successful_check, dismissed_version):
        self.store.setValue("update_last_successful_check", last_successful_check)
        self.store.setValue("update_dismissed_version", dismissed_version)
        self.store.sync()
        if self.store.status() != QSettings.Status.NoError:
            raise OSError("Update-check state could not be saved.")
        self.update_last_successful_check = last_successful_check
        self.update_dismissed_version = dismissed_version


class SettingsDialog(ProjectDialog):
    def __init__(self, preferences, parent):
        super().__init__("Settings", "Small preferences, stored only on this device.", parent)
        layout = QFormLayout()
        layout.setVerticalSpacing(18)
        self.content.addWidget(label("PLAYBACK", "dialogEyebrow"))
        self.content.addLayout(layout)
        self.repeat_video = QCheckBox("Repeat the current video")
        self.repeat_video.setChecked(preferences.repeat_video)
        layout.addRow(self.repeat_video)
        self.repeat_music = QCheckBox("Repeat the current music track")
        self.repeat_music.setChecked(preferences.repeat_music)
        layout.addRow(self.repeat_music)
        self.wheel_navigation = QCheckBox(
            "Use the mouse wheel for previous / next; middle-click toggles zoom"
        )
        self.wheel_navigation.setChecked(preferences.wheel_navigation)
        self.wheel_navigation.setToolTip(
            "When enabled, wheel down opens the next file and wheel up opens the previous file."
        )
        layout.addRow(self.wheel_navigation)
        self.auto_updates = QCheckBox("Automatically check GitHub for AMP updates")
        self.auto_updates.setChecked(preferences.auto_updates)
        self.auto_updates.setToolTip("Disabled by default; checks public release information only.")
        self.auto_updates.toggled.connect(self._confirm_auto_updates)
        layout.addRow(self.auto_updates)
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
            "Repeat choices apply to this window now and to new windows.\n"
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

    def _confirm_auto_updates(self, enabled):
        if not enabled:
            return
        answer = QMessageBox.question(
            self,
            "Enable automatic update checks?",
            "If enabled, AMP will contact GitHub after startup at most once every 24 hours "
            "to read public AMP release information. No media names, paths or usage data are "
            "sent. AMP will never download or install updates automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.No:
            self.auto_updates.setChecked(False)
