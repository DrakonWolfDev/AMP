"""Standalone Linux entry point for the PyInstaller bundle."""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
    from tools.package_smoke import main

    del sys.argv[1]
else:
    from amp.app import main


if __name__ == "__main__":
    raise SystemExit(main())
