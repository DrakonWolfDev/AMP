# AMP v1 release readiness - 2026-10-18

The feature set is close to a release candidate. **v1 is not approved for publication yet.** The user selected a standalone app with no Python setup, using Inno Setup for Windows as in WolfLauncher. Version remains 0.0.1 while validation is incomplete. The original v0.1 milestone wording below is historical; it does not override this delivery decision.

## Windows checks completed in this review

| Check | Result |
| --- | --- |
| Unit tests, Ruff lint/format | 90 current tests pass (including OS-registration and hover checks); static checks pass. |
| UI, shortcuts, settings, repeat and fade | 35 live checks pass. Updated the probe to include all six overlay panels. |
| Independent windows and repeated shutdown | 21 live resilience checks pass. |
| Separately launched processes | Six checks pass, including independent playback and capture. |
| Image/video capture composition and dimensions | 62 checks pass at each of DPR 1.25 and effective 1.5. |
| Current Python wheel/sdist | Offline source/wheel build and fresh minimal-venv installation pass; 13 media/GL smoke checks pass outside the checkout. This is supporting package evidence, not the chosen final installation experience. |
| Standalone AMP.exe | PyInstaller 6.22.3 one-folder bundle built. All 13 smoke checks pass with PATH restricted to Windows System32 and AMP_MPV_DIR/PYTHONPATH/PYTHONHOME removed. Bundled Python and libmpv work without the development environment. |
| Inno installer | WolfLauncher's verified Inno Setup 6.7.3 compiler builds a per-user x64 installer. Andy reports install and uninstall worked correctly on his Windows machine. Clean-machine installation, upgrade and association cleanup still need validation. |
| Private bundle contents | 246 files, 254,454,802 bytes. Includes embedded Python, libmpv and preserved Python/PyInstaller notices. Unused Qt PDF/Multimedia/extra FFmpeg DLLs, Java JARs and development FFmpeg executable are excluded. Full transitive notice/source audit remains open. |

Private artifacts (ignored by Git):

- `artifacts/windows-v1-preview/dist/AMP/AMP.exe`: portable folder preview; keep its `_internal` folder beside it.
- `artifacts/windows-v1-preview/installer/AMP-0.0.1-private-preview-setup.exe`: 76,484,877 bytes, SHA-256 `2f8e4c7e814270d14df893ff667a64fc83ebe596a581784684a7079d8b75532f`.
- `artifacts/windows-v1-preview/report.json`: exact file/hash inventory and frozen smoke result; explicitly marks `release_ready: false`.

## Required before v1

- [ ] **Mint 22.3 desktop validation.** Test real GL rendering, capture, sound, fullscreen, input and independent processes on the target desktop. Ubuntu unit CI and offscreen tests do not satisfy this.
- [ ] **Standalone Linux delivery.** Build on Linux, with embedded Python and a validated native runtime/dependency strategy. A source/venv installation is useful for diagnosis but does not meet the selected no-Python-setup experience. A portable folder/AppImage is a candidate, not a validated artifact yet.
- [ ] **Clean Windows install/upgrade/uninstall.** Test the Inno installer on a machine or VM without Python, libmpv or the development checkout. Verify standard-user install, shortcuts, launching media paths containing spaces/non-ASCII characters, multiple instances, uninstall and reinstall. Uninstall must preserve source media, screenshots and unrelated files. Test the actual downloaded unsigned/signed artifact and record Windows warnings.
- [ ] **OS file associations on both platforms.** Windows installer registration is implemented as an optional unchecked Open with task, using per-user ProgIDs, SupportedTypes and Default apps capabilities. It never writes UserChoice or extension defaults. Verify native discovery, explicit default selection, quoted/non-ASCII paths and uninstall cleanup without removing other handlers. A Linux desktop/MIME entry is prepared; integrate and validate it with the Linux package and desktop database.
- [ ] **Finish distribution compliance.** Fix the final file inventory, corresponding source/build recipes/patches, complete dependency notices and source delivery/relinking arrangements. Check the applicable codec-patent position separately. See [CODEC_AUDIT.md](CODEC_AUDIT.md); no binary release clearance is implied by a successful build.
- [ ] **Human playback and desktop checks on both systems.** Listen to music and audio-bearing video, mute/unmute, seek/replay, speed and shutdown. Check native file/folder dialogs, file-manager drag/drop, sleep/resume, minimise/restore, monitor/DPI moves where hardware allows and at least one longer mixed-media session. Automated probes deliberately use muted/zero output.
- [ ] **Release-candidate handover.** Resolve defects or document accepted limits, rebuild from a reviewed source revision, record final hashes, prepare release notes and user installation instructions, then obtain explicit publication approval. No version bump, Git tag, upload or repository visibility change was made here.

An installer is now available for private review, not a finished compliance-cleared release. OS file-association integration is now required for v1; a bespoke icon and signing remain release decisions; the installer does not silently take over media associations. Automatic GL context-loss recovery is not implemented; reopening the window remains the documented recovery path and should be assessed during platform testing.

## Mint validation session

1. Record Mint version, desktop/session (X11 or Wayland), GPU/driver, display scaling, Python/Qt versions and the exact system or bundled libmpv/FFmpeg build. Verify licence/build flags for that runtime separately from Windows.
2. Follow the Linux development setup in README on the actual desktop. Run unit/static checks, then `tools.render_probe`, `tools.playback_probe`, `tools.image_probe`, `tools.interaction_probe`, `tools.browser_probe`, `tools.dialog_probe`, `tools.music_presentation_probe`, `tools.capture_probe`, `tools.resilience_probe` and `tools.process_probe`. Inspect results; Windows-specific assumptions in a harness may need adapting before drawing conclusions.
3. Exercise a normal-DPI and high-DPI desktop configuration. Compare actual saved image/video crop and letterboxing with the screen; verify physical output dimensions. Test two independent windows/processes and closing either while the other plays.
4. Complete the listening, native dialogs/drop, permission/storage-error, resize/fullscreen, sleep/resume and longer-session checks above. Keep machine-readable reports and manual results with the exact runtime versions.
5. Build and test the chosen standalone Linux artifact on a clean target. Do not claim Linux support solely from a Windows-created bundle or CI unit results.

## Rebuild the Windows preview

Install the application/development dependencies and `requirements-windows-build.txt`. Generate media fixtures with `tools.render_probe` and `tools.playback_probe` first. Use a new output directory each time:

```powershell
$env:AMP_MPV_DIR = (Resolve-Path artifacts/runtime/libmpv).Path
.\.venv\Scripts\python -m tools.build_windows_preview --output artifacts/windows-next-preview --iscc "C:\path\to\inno-setup-6.7.3\ISCC.exe"
```

The helper verifies the known compiler hash, runs unit/static checks before building, freezes the app, adds interpreter/freezer notices, checks excluded files, executes a real frozen smoke test with the development paths removed, compiles Inno and records hashes. It neither installs the result nor publishes it. Without `--iscc`, it validates only the portable folder. See [PyInstaller one-folder packaging](https://pyinstaller.org/en/stable/operating-mode.html) and [Inno Setup](https://jrsoftware.org/isinfo.php).


## Latest association-enabled installer

The newer private installer is `artifacts/windows-associations-review/installer/AMP-0.0.1-private-preview-setup.exe` (76,485,642 bytes, SHA-256 `27242887b4e407b06d5b9079086024863ef0ef12da933532fd21e9e5c9d6f501`). It adds the optional per-user Open with task using the same previously tested standalone payload. Inno compilation passes; no registry changes or installation were performed. See evidence/windows-file-associations-installer.json. The older installer above predates this registration change.


## Latest hover-fix preview

The historical hover-only build is artifacts/windows-hover-fix/installer/AMP-0.0.1-private-preview-setup.exe. In-window hints and idempotent control revealing replace the native tooltip/always-enabled opacity-effect path. Unit checks (90), hover tests at both DPIs, fullscreen/browser/style/UI regressions and the frozen smoke test pass. Exact build/hash inventory: evidence/windows-hover-fix-installer.json. Andy confirms hover improved; fullscreen entry still flickers. See the fullscreen follow-up below; this does not close the remaining v1 release gates.

## Fullscreen follow-up

Andy confirms the hover behavior is better, but entering fullscreen still flickers. Removed top-level painting suspension during native window changes: rendering stays enabled, while the short timer guards duplicate input and screenshot capture and restarts on resize/state changes. The interaction probe now inspects frames during the transition as well as after settling: 46 checks pass at DPR 1.25 and 1.5; 21 hover checks pass at 1.5. Windows compositor visual confirmation remains pending. The new private installer is under artifacts/windows-fullscreen-fix and supersedes the hover-only preview. Exact build inventory: evidence/windows-fullscreen-fix-installer.json. Remaining v1 release gates are unchanged.

AMP icon follow-up: original dark/amber play-and-frame SVG artwork with PNG and nine-size Windows ICO is in amp/assets. Qt windows, PyInstaller executable and Inno installer use it; Windows shortcuts/uninstall/file associations inherit the executable icon. Application taskbar identity is WolfForge.AMP. Private installer: artifacts/windows-icon-preview/installer/AMP-0.0.1-private-preview-setup.exe. All 90 tests, static checks, 13 frozen smoke checks and Inno compilation pass; executable/installer group-icon resources and frozen icon asset verified. Evidence: docs/evidence/windows-icon-installer.json. No installation or publication performed; Linux icon installation remains part of Linux packaging validation.

User acceptance (2026-10-18): Andy accepted the current fullscreen behavior as the baseline and approved the AMP icon. Install/uninstall worked on his Windows machine. These confirmations do not replace the remaining Linux, clean-machine and release-compliance gates.
