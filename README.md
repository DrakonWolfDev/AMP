# AMP — Andy’s Media Player

A small, private-by-design desktop viewer for local images and videos on Linux Mint and Windows.

AMP will fit media to the viewport, offer cursor-focused zoom and drag-pan, browse neighbouring files, and save the visible media viewport as a PNG. Video playback and each window's state remain independent. No accounts, telemetry, cloud services, or media library scans.

## Project status

Initial repository setup and specification review. There is no runnable application yet.

- [Product roadmap](AMP_ROADMAP.md): behaviour and milestone acceptance criteria.
- [Implementation prompt](CODEX_PROMPT.md): engineering requirements supplied with the project.
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): build order and validation.
- [Progress](docs/PROGRESS.md): verified status and environment.
- [Technical risks](docs/TECHNICAL_RISKS.md): renderer gate and open decisions.
- [Test matrix](docs/TEST_MATRIX.md): planned platform checks.

The proposed stack is Python, PySide6/Qt 6, and libmpv's OpenGL Render API. The first development task is a real renderer/capture probe. Installation and launch instructions will be added when that probe exists and has been exercised.

No licence has been selected for AMP. Third-party runtime redistribution requires an audit of the exact binaries before packaging.
