# Release readiness

The source tree and packaging definitions are suitable for public development. Binary
publication still requires platform-specific validation and completion of the dependency
redistribution review described in `docs/LICENSING.md`.

## Final 0.8b validation pass

The release candidate includes the Linux subtitle compositing fix, deferred Windows EOF
handoff, and separate Windows/Linux source environments. The documented privacy boundary is
in `PRIVACY.md`; the system-codec packaging choice and patent limits are in `CODEC_AUDIT.md`.
Both documents accompany the frozen applications. This wording does not assert patent clearance.

The Package previews workflow builds both platforms from the selected commit, prepares the
hash-verified corresponding-source set, and exercises the extracted Linux package under Xvfb.
Its packaged smoke test checks subtitle composition and natural music advancement as well as
images, two-window video, screenshots and shutdown. The exact frozen Windows runtime is also
retained for desktop smoke testing after download. These checks do not replace clean-target
installer, association, audible-output or physical Mint/Windows desktop acceptance.

The 21 October Windows privacy observation concerns the previously installed development
build, not automatically the new candidate. No AMP-attributed internet connection or DNS request
was identified; network-share music reads were observed. Windows diagnostics were stopped in
the before/after snapshots, so no claim about all Windows diagnostic configurations is made.

## Linux

- The amd64 Debian builder runs tests and static checks, freezes AMP, rejects accidentally
  bundled Qt Multimedia/PDF and FFmpeg libraries, then creates a `.deb`.
- The package installs the command, icon and MIME-aware desktop entry needed for Open With.
- Mint testing has confirmed install, uninstall/reinstall, images, animated GIFs, video/music,
  audible PipeWire output, fullscreen, monitor/scaling transitions and Trash navigation.
- Still validate the GitHub-built package's command-line launch, Open With registration and
  dependency resolution on a clean supported Mint/Ubuntu installation.

## Windows

- PyInstaller and Inno Setup definitions are present and the installer registers optional,
  per-user Open With handlers without taking over defaults.
- Build on 64-bit Windows with the pinned requirements. Playback uses the native Media Foundation
  Qt backend; the bundle gate rejects libmpv and FFmpeg payloads.
- The earlier libmpv build passed audible playback, fullscreen and monitor/scaling tests. Repeat
  those tests against the replacement Media Foundation build.
- The earlier preview installer was reported working for installation and uninstall. Re-test the
  rebuilt package because its multimedia runtime has changed.
- Validate the GitHub-built installer on a clean Windows system: install, upgrade, optional
  Open With registration, playback, uninstall and preservation of unrelated file handlers.

## GitHub package previews

- `.github/workflows/package-previews.yml` is manually triggered and builds Linux amd64 and
  Windows x64 artifacts from the same commit without publishing them.
- [Run 39440380398](https://github.com/DrakonWolfDev/AMP/actions/runs/39440380398) passed both
  packaging jobs at commit `ae41331`. Its inventories were inspected and the Debian package was
  extracted: the forbidden development/media payloads are absent. The two artifacts await
  clean-target installation and interactive acceptance.
- The builders run unit tests, lint, formatting, freeze/inventory checks and package assembly.
- Hosted Windows CI is not treated as a native interactive GL/audio test. Its report explicitly
  records the skipped standalone smoke test; the downloaded installer requires desktop testing.

## Automated release path

- Pushing a version-matched tag such as `v0.8b` runs `.github/workflows/release.yml`.
- Publication is deliberately blocked unless the repository variable
  `AMP_BINARY_RELEASE_APPROVED` is set to `true` after the checks below are complete.
- The workflow builds Windows and Linux from the same tag, verifies both artifacts, publishes one
  GitHub prerelease, and then dispatches a manifest update to the Wolf Forge website.
- The repository secret `WOLF_FORGE_SITE_TOKEN` must contain a fine-grained token limited to the
  `DrakonWolfDev/wolf-forge-static` repository with Contents read/write permission. A missing token
  stops publication during preflight.
- The website keeps its previous release links if its validation or update workflow fails.

## Before publishing binaries

- Verify the exact generated inventory contains the native Windows Qt multimedia plugin and no
  libmpv or FFmpeg payload; see `CODEC_AUDIT.md` and `SOURCE_DELIVERY.md`.
- Exercise the final GitHub artifacts' supported formats and GPU rendering on each clean target.
- Version 0.8b will remain unsigned by decision. Label it clearly, publish SHA-256 hashes and
  retain build logs for the released artifacts.
- Keep generated packages, machine reports, local media and credentials out of Git.
