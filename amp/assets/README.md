# AMP icon

Original AMP artwork, copyright 2026 Wolf Forge, distributed under the project's
AGPL-3.0-only licence. No third-party icon artwork or fonts are used.

`amp.svg` is the editable source. `amp.png` is a transparent 512-pixel export
and `amp.ico` contains 16, 20, 24, 32, 40, 48, 64, 128 and 256-pixel images.
Regenerate the exports from the repository root with:

```powershell
.venv/Scripts/python.exe -m tools.build_icons
```

The generator uses the development Pillow dependency and Qt SVG renderer;
Pillow is not included in the standalone player.

The Qt application loads the ICO for its windows. PyInstaller embeds it into
AMP.exe, which supplies Windows shortcut, uninstall and media-association
icons. Inno Setup also embeds it into the installer. The SVG/PNG are available
for the future Linux icon installation (`Icon=amp` in the desktop entry).
