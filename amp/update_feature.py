"""AMP presentation for notification-only Wolf Update checks."""

from importlib.metadata import PackageNotFoundError, version

from PySide6.QtWidgets import QMessageBox

from wolf_update import (
    CheckStatus,
    GitHubReleaseSource,
    MemoryStateStore,
    UpdateApplication,
    UpdateService,
    UpdateState,
)
from wolf_update.qt import QtUpdateChecker

from .version import display_version

UPDATE_REPOSITORY = "DrakonWolfDev/AMP"
UPDATE_DESTINATION = "https://github.com/DrakonWolfDev/AMP/releases"
UPDATE_CHANNEL = "experimental"


def current_version():
    try:
        return version("andy-media-player")
    except PackageNotFoundError:
        return "0.8.1b"


class UpdateFeatureMixin:
    def setup_update_feature(self):
        state = UpdateState(
            last_successful_check=self.preferences.update_last_successful_check,
            dismissed_version=self.preferences.update_dismissed_version,
        )
        self.update_state_store = MemoryStateStore(state)
        application = UpdateApplication(
            current_version=current_version(),
            repository=UPDATE_REPOSITORY,
            update_url=UPDATE_DESTINATION,
            channel=UPDATE_CHANNEL,
        )
        source = GitHubReleaseSource(
            application.repository,
            user_agent=f"AMP/{application.current_version}",
        )
        self.update_service = UpdateService(application, self.update_state_store, source=source)
        self.update_checker = QtUpdateChecker(self.update_service, self)
        self.update_checker.result_ready.connect(self.handle_update_result)

    def check_for_updates(self):
        if self.update_checker.check(manual=True):
            self.notify("Checking GitHub for AMP updates…")
        else:
            self.notify("An update check is already running.")

    def start_automatic_update_check(self):
        if self.preferences.auto_updates:
            self.update_checker.check(manual=False)

    def handle_update_result(self, result, manual):
        self._persist_update_state()
        if result.status is CheckStatus.AVAILABLE:
            self._show_available_update(result.release)
        elif manual and result.status is CheckStatus.UP_TO_DATE:
            QMessageBox.information(
                self,
                "AMP is up to date",
                f"Version {display_version(current_version())} is the newest applicable release.",
            )
        elif manual and result.status is CheckStatus.FAILED:
            QMessageBox.warning(
                self,
                "Could not check for updates",
                result.message or "AMP could not reach GitHub. Please try again later.",
            )

    def _persist_update_state(self):
        state = self.update_state_store.load()
        try:
            self.preferences.save_update_state(state.last_successful_check, state.dismissed_version)
        except OSError as error:
            self.notify(str(error))

    def _show_available_update(self, release):
        message = QMessageBox(self)
        message.setWindowTitle("AMP update available")
        message.setIcon(QMessageBox.Icon.Information)
        message.setText(f"AMP {display_version(release.version)} is available.")
        message.setInformativeText(
            "AMP will open the official GitHub download page. It will not download or install "
            "anything automatically."
        )
        if release.notes:
            message.setDetailedText(release.notes)
        download = message.addButton("Open download page", QMessageBox.ButtonRole.AcceptRole)
        dismiss = message.addButton("Dismiss this version", QMessageBox.ButtonRole.DestructiveRole)
        message.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        message.exec()
        if message.clickedButton() is download:
            if not self.update_service.view_update():
                self.notify("The AMP download page could not be opened.")
        elif message.clickedButton() is dismiss:
            self.update_service.dismiss(release)
            self._persist_update_state()

    def stop_update_check(self):
        self.update_checker.requestInterruption()
        self.update_checker.wait(250)
