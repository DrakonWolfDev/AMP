from PySide6.QtCore import QSettings

from amp.settings import Preferences


def test_preferences_default_and_round_trip(tmp_path):
    path = tmp_path / "settings.ini"
    preferences = Preferences(path)
    assert (preferences.repeat, preferences.volume, preferences.banner_seconds) == (False, 100, 3)
    assert not preferences.wheel_navigation
    assert not path.exists()
    preferences.save(True, 25, 5, True)
    restored = Preferences(path)
    assert (restored.repeat, restored.volume, restored.banner_seconds) == (True, 25, 5)
    assert restored.wheel_navigation


def test_preferences_handle_invalid_local_values(tmp_path):
    path = tmp_path / "settings.ini"
    store = QSettings(str(path), QSettings.Format.IniFormat)
    store.setValue("repeat", "unexpected")
    store.setValue("default_volume", "broken")
    store.setValue("banner_seconds", -500)
    store.sync()
    preferences = Preferences(path)
    assert not preferences.repeat
    assert preferences.volume == 100
    assert preferences.banner_seconds == 1


def test_mute_persists_without_overwriting_other_windows_settings(tmp_path):
    path = tmp_path / "settings.ini"
    first = Preferences(path)
    assert not first.muted
    second = Preferences(path)
    second.save(True, 25, 5)
    first.save_mute(True)
    restored = Preferences(path)
    assert restored.muted
    assert (restored.repeat, restored.volume, restored.banner_seconds) == (True, 25, 5)
    second.save(False, 50, 2)
    assert Preferences(path).muted
    first.save_mute(False)
    assert not Preferences(path).muted
