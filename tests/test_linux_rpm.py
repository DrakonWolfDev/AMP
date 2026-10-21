import re

import pytest

from tools.build_linux_rpm import private_requires_pattern, rpm_version


@pytest.mark.parametrize(
    "source,expected", [("0.8b", "0.8~b0"), ("1.0rc2", "1.0~rc2"), ("1.0", "1.0")]
)
def test_rpm_prerelease_version(source, expected):
    assert rpm_version(source) == expected


@pytest.mark.parametrize("source", ["1!1.0", "1.0.dev1", "1.0.post1", "1.0+local"])
def test_rpm_rejects_unmapped_versions(source):
    with pytest.raises(ValueError):
        rpm_version(source)


def test_private_libraries_do_not_hide_system_abi_requirements(tmp_path):
    (tmp_path / "libQt6Core.so.6").touch()
    (tmp_path / "libpython3.14.so.1.0").touch()
    pattern = private_requires_pattern(tmp_path)
    assert re.search(pattern, "libQt6Core.so.6(Qt_6)(64bit)")
    assert re.search(pattern, "libpython3.14.so.1.0()(64bit)")
    assert not re.search(pattern, "libc.so.6(GLIBC_2.43)(64bit)")
    assert not re.search(pattern, "libQt6Core.so.60()(64bit)")
