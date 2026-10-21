import hashlib
from pathlib import Path

import pytest

from tools.linux_formats import build_appimage, build_rpm


def test_rpm_preserves_payload_and_declares_external_runtime(tmp_path):
    payload = tmp_path / "package"
    payload.mkdir()

    def run(arguments, name):
        if name == "rpmbuild":
            spec = Path(arguments[-1]).read_text()
            assert "AutoReqProv: no" in spec
            assert "Requires: mpv-libs" in spec
            assert "/usr/share/applications/amp.desktop" in spec
            artifact = tmp_path / "rpmbuild/RPMS/x86_64/amp-media-player-0.8b-1.x86_64.rpm"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"validated payload")

    artifact = build_rpm(payload, tmp_path, "0.8b", run)
    assert artifact.name == "amp-media-player-0.8b-1.x86_64.rpm"
    assert artifact.read_bytes() == b"validated payload"


def test_appimage_refuses_unverified_tool_before_execution(tmp_path, monkeypatch):
    payload = tmp_path / "package"
    for relative in (
        "usr/share/applications/amp.desktop",
        "usr/share/icons/hicolor/256x256/apps/amp.png",
    ):
        path = payload / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"payload")

    def download(url, target):
        target.write_bytes(b"wrong tool")

    def run(*args):
        pytest.fail("Unverified tooling must never execute")

    monkeypatch.setattr("tools.linux_formats.urllib.request.urlretrieve", download)
    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        build_appimage(
            payload, tmp_path, "0.8b", run, lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        )
