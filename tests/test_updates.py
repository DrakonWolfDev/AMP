from datetime import datetime, timedelta, timezone

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
