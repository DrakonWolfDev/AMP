"""Standalone entry point; an explicit self-test reuses the local smoke harness."""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
    from tools.package_smoke import main

    del sys.argv[1]
else:
    from amp.app import main

raise SystemExit(main())
