from pathlib import Path

from amp.folder_navigator import SUPPORTED_SUFFIXES
from tools.windows_associations import registry_entries


def test_checked_in_registration_matches_supported_media():
    root = Path(__file__).resolve().parents[1]
    text = (root / "packaging/windows/associations.iss").read_text(encoding="utf-8")
    assert text == registry_entries()
    for suffix in SUPPORTED_SUFFIXES:
        assert f'Classes\\{suffix}\\OpenWithProgids"' in text
        assert f'ValueName: "{suffix}"; ValueData: "WolfForge.AMP.Media"' in text


def test_registration_preserves_default_handlers_and_quotes_paths():
    text = registry_entries()
    rows = [line for line in text.splitlines() if line.startswith("Root:")]
    assert all(line.startswith("Root: HKCU;") for line in rows)
    assert all("Tasks: fileassociations" in line for line in rows)
    assert "UserChoice" not in "\n".join(rows)
    assert 'ValueData: """{app}\\AMP.exe"" ""%1"""' in text
    extension_rows = [line for line in rows if "\\OpenWithProgids" in line]
    assert all(
        "uninsdeletevalue" in line and "uninsdeletekey" not in line for line in extension_rows
    )
