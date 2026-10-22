from datetime import datetime, timedelta, timezone

from amp.update_feature import UPDATE_CHANNEL, UPDATE_DESTINATION
from amp.version import display_version
from wolf_update import CheckStatus, MemoryStateStore, UpdateApplication, UpdateService
from wolf_update.state import UpdateState


def release(tag, *, prerelease=False, draft=False, body="notes"):
    return {"tag_name": tag, "prerelease": prerelease, "draft": draft, "body": body}


class Source:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def releases(self):
        self.calls += 1
        return self.payload


def application():
    return UpdateApplication(
        current_version="1.0.0",
        repository="DrakonWolfDev/AMP",
        update_url="https://github.com/DrakonWolfDev/AMP/releases",
    )


def test_public_beta_version_keeps_its_short_label():
    assert display_version("0.8.1b0") == "0.8.1b"
    assert display_version("0.8.1b") == "0.8.1b"
    assert display_version("0.8.1b1") == "0.8.1b1"


def test_amp_accepts_beta_update_notifications():
    assert UPDATE_CHANNEL == "experimental"


def test_amp_updates_open_the_official_project_page():
    assert UPDATE_DESTINATION == "https://wolf-forge.co.uk/codename-amp.html"


def test_update_service_selects_stable_release_and_never_has_download_api():
    source = Source([release("v1.1.0"), release("v2.0.0b1", prerelease=True)])
    service = UpdateService(application(), MemoryStateStore(), source=source)
    result = service.check(manual=True)
    assert result.status is CheckStatus.AVAILABLE
    assert str(result.release.version) == "1.1.0"
    assert not hasattr(service, "download")
    assert not hasattr(source, "download")


def test_automatic_checks_are_throttled_and_dismissible():
    now = datetime(2026, 10, 19, tzinfo=timezone.utc)
    source = Source([release("v1.1.0")])
    store = MemoryStateStore()
    service = UpdateService(application(), store, source=source, clock=lambda: now)
    available = service.check()
    service.dismiss(available.release)
    assert service.check().status is CheckStatus.THROTTLED
    later = UpdateService(
        application(), store, source=source, clock=lambda: now + timedelta(days=1)
    )
    assert later.check().status is CheckStatus.DISMISSED


def test_cancelled_check_does_not_contact_github_or_save_state():
    source = Source([release("v1.1.0")])
    store = MemoryStateStore(UpdateState())
    result = UpdateService(application(), store, source=source).check(cancelled=lambda: True)
    assert result.status is CheckStatus.CANCELLED
    assert source.calls == 0
    assert store.load().last_successful_check is None
