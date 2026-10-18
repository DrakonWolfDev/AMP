import pytest

from amp.mpv_backend import load_binding


def test_missing_runtime_is_actionable(monkeypatch):
    def missing(_name):
        raise OSError("missing DLL")

    monkeypatch.setattr("amp.mpv_backend.importlib.import_module", missing)
    with pytest.raises(RuntimeError, match="AMP_MPV_DIR"):
        load_binding()
