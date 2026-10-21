import hashlib

import pytest

from tools.linux_formats import build_appimage


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
