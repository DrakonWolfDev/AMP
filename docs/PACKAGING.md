# Local package build and handover

These steps build private development artifacts. They do not upload, tag or publish anything. AMP still requires Python 3.12+, a working OpenGL 3.3 driver and separately installed libmpv. A wheel is an installable Python package, not a standalone executable or installer.

## Windows build

Use the existing development environment from README.md. Run `tools.render_probe` and `tools.playback_probe` first to generate synthetic validation fixtures. Cache the exact build and runtime wheels once (this preparation step uses the network):

```powershell
.\.venv\Scripts\python -m pip download --only-binary=:all: --dest artifacts/packaging/wheelhouse -r requirements-build.txt PySide6-Essentials==6.12.0 python-mpv==1.0.8 PyOpenGL==3.1.10 mutagen==1.47.0
$env:AMP_MPV_DIR = (Resolve-Path artifacts/runtime/libmpv).Path
.\.venv\Scripts\python -m tools.package_preview --wheelhouse artifacts/packaging/wheelhouse
```

The builder itself works offline. It runs the unit tests and source checks, creates an isolated build environment, builds an sdist and then a wheel from that sdist using pinned tooling, verifies all licence/notice bytes, and copies just the five runtime dependency wheels into a new output directory. It generates a SHA-256 requirements lock and installs it with `--no-index --require-hashes` in a fresh virtual environment. That environment contains neither the editable checkout nor Qt Addons, test tools or fixture generators. A standalone smoke test runs outside the checkout and exercises blank launch, image/video/music, independent windows, fullscreen/resize, viewport capture and clean shutdown. The package module path is checked to prove the installed copy was used.

Results go into a new `artifacts/packaging/preview-<UTC timestamp>` directory. `--output <new directory>` selects another location; existing builds are never overwritten. Keep the wheelhouse if later offline builds are needed. Files of interest:

- `dist/`: AMP source archive and wheel. The source archive contains tests, tools, docs, licence texts and product requirements; it excludes local media, virtual environments and Git internals.
- `wheelhouse/` and `requirements-runtime.txt`: the exact platform-specific wheels and SHA-256 pins for offline installation.
- `report.json`: artifact hashes, package licence metadata and embedded-notice inventory, smoke results and exact native runtime metadata/hash when available.
- `smoke/`: synthetic image, captured PNG and standalone install report.
- `build-env/` and `install-env/`: disposable local validation environments. They are not portable application bundles.

Use `python -m venv <new environment>` and that environment's Python to install with `-m pip install --no-index --find-links <build>/wheelhouse --require-hashes -r <build>/requirements-runtime.txt`. Then set `AMP_MPV_DIR` to the separately installed DLL directory and launch with `python -m amp <local file>`. Keep the original dependency wheels with their embedded notices intact. Requirements include hashes for this wheelhouse/platform only; prepare and validate separate wheels on Linux.

Build commands and dependency versions are repeatable. Per-build hashes identify the exact outputs; bit-for-bit reproducibility of all source archives is not claimed. The build requires the pinned wheel versions to remain available or be retained locally. No updater or package-download feature is added to AMP itself.

## Remaining release gates

- Validate the actual Mint 22.3 desktop renderer and system libmpv build, then repeat source installation and functional checks there. Ubuntu unit-test CI does not cover this.
- Validate a clean Windows machine without development runtimes; the fresh venv still uses this machine's Python, drivers and libmpv.
- Complete exact native/transitive dependency and corresponding-source/build-configuration collection. Wheel licence metadata and an LGPL-labelled libmpv asset are inventory evidence, not a completed redistribution audit. No native runtime is copied into the package.
- Resolve any packaging-specific driver/runtime discovery problems before choosing a frozen executable/installer. Include CPython notices if Python is embedded later.
- Complete manual listening, native file-manager/picker/association and multi-monitor checks in TEST_MATRIX.md. Context-loss recovery remains unavailable; closing and opening another window is required if the GL context is destroyed.

The existing runtime provenance and selected codecs are recorded in RENDERER_AND_PACKAGING.md and THIRD_PARTY_NOTICES.md. M9 remains partly implemented until its platform and distribution gates pass. See LICENSING.md for the existing release audit checklist. No release permission is implied by a successful local package build.

Packaging method references: [PyPA build tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/), [pip download](https://pip.pypa.io/en/stable/cli/pip_download/), [pip hash checking](https://pip.pypa.io/en/stable/topics/secure-installs/).


## Standalone Windows / Inno preview

The user selected a no-Python-setup standalone v1. A tested private PyInstaller one-folder bundle and Inno Setup installer now exist; use [RELEASE_READINESS.md](RELEASE_READINESS.md) for build commands, exact results and remaining release gates. The earlier wheel workflow above remains useful for source-package verification, but is not the final user installation experience. Linux standalone packaging must be built and validated on Linux.
