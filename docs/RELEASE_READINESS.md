# Release readiness

The source tree and packaging definitions are suitable for public development. Binary
publication still requires platform-specific validation and completion of the dependency
redistribution review described in `docs/LICENSING.md`.

## Linux

- The amd64 Debian builder runs tests and static checks, freezes AMP, rejects accidentally
  bundled Qt Multimedia/PDF and FFmpeg libraries, then creates a `.deb`.
- The package installs the command, icon and MIME-aware desktop entry needed for Open With.
- Validate install, playback, Open With and uninstall on a clean supported Mint/Ubuntu system.

## Windows

- PyInstaller and Inno Setup definitions are present and the installer registers optional,
  per-user Open With handlers without taking over defaults.
- Build on 64-bit Windows with the pinned requirements and a validated libmpv runtime.
- Validate clean install, upgrade, file associations, playback and uninstall before release.

## Before publishing binaries

- Complete the exact native/transitive dependency, notice and corresponding-source inventory.
- Exercise audible playback, supported formats and GPU rendering on each target platform.
- Confirm installer signatures/hashes and retain build logs for the released artifacts.
- Keep generated packages, machine reports, local media and credentials out of Git.
