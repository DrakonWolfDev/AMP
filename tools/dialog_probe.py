"""Render and exercise branded dialogs using actual Qt widgets and controls."""

import argparse
import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QScrollArea

from amp.app import Window, create_application
from amp.dialogs import AboutDialog, HelpDialog
from amp.settings import Preferences, SettingsDialog
from tools.session_probe import wait


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/dialogs"))
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "isolated.ini")
    preferences.repeat, preferences.volume, preferences.banner_seconds = False, 0, 3
    window = Window(preferences)
    report = {"checks": []}

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    try:
        window.show()
        wait(150)
        for name, dialog in (
            ("about", AboutDialog(window)),
            ("help", HelpDialog(window)),
            ("settings", SettingsDialog(preferences, window)),
        ):
            dialog.show()
            wait(100)
            dialog.grab().save(str(output / f"{name}.png"))
            check(
                dialog.rect().contains(
                    dialog.buttons.geometry().translated(dialog.buttons.parentWidget().pos())
                ),
                f"{name} footer buttons remain inside the dialog",
            )
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
            check(not dialog.isVisible(), f"Escape closes {name}")
        about = AboutDialog(window)
        about.resize(420, 340)
        about.show()
        wait(100)
        about.grab().save(str(output / "about-small.png"))
        scroll = about.findChild(QScrollArea)
        check(
            scroll.verticalScrollBar().maximum() > 0,
            "Small dialog scrolls its content instead of clipping it",
        )
        about.close()

        def save_settings():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, SettingsDialog)
            dialog.repeat.setChecked(True)
            dialog.volume.setValue(21)
            dialog.banner.setValue(5)
            dialog.buttons.button(QDialogButtonBox.StandardButton.Save).click()

        QTimer.singleShot(100, save_settings)
        window.settings()
        check(
            (preferences.repeat, preferences.volume, preferences.banner_seconds) == (True, 21, 5),
            "Styled Save button applies settings",
        )
        check(Preferences(preferences.path).volume == 21, "Settings still persist locally")

        def cancel_settings():
            dialog = QApplication.activeModalWidget()
            dialog.volume.setValue(79)
            dialog.buttons.button(QDialogButtonBox.StandardButton.Cancel).click()

        QTimer.singleShot(100, cancel_settings)
        window.settings()
        check(
            preferences.volume == 21 and Preferences(preferences.path).volume == 21,
            "Cancel preserves saved preferences",
        )
        window.media_menu.popup(
            window.menu_button.mapToGlobal(window.menu_button.rect().bottomLeft())
        )
        wait(100)
        window.media_menu.grab().save(str(output / "menu.png"))
        window.media_menu.setActiveAction(window.media_menu.actions()[0])
        wait(50)
        window.media_menu.grab().save(str(output / "menu-selected.png"))
        window.media_menu.close()
        report["passed"] = True
        report["dpr"] = window.devicePixelRatioF()
    finally:
        window.close()
        wait(100)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
