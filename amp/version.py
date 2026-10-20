from packaging.version import Version

PUBLIC_VERSION = "0.8b"


def display_version(value):
    """Keep the chosen public label while retaining PEP 440 comparisons internally."""
    parsed = Version(str(value))
    if parsed == Version(PUBLIC_VERSION):
        return PUBLIC_VERSION
    return str(parsed)
