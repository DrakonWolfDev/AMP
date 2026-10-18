"""Render actual Qt controls over the media FBO for design review and layout QA.

These composition previews exclude native window decorations. They use the real
widgets, not a screenshot API that could repaint the GL viewport unexpectedly.
"""

import argparse
import json
import shutil
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QCursor, QImage, QLinearGradient, QPainter, QPolygonF
from PySide6.QtWidgets import QWidget

from amp.app import Window, create_application
from amp.settings import Preferences
from tools.session_probe import wait


def compose(window, destination):
    viewport = window.viewport
    dpr = viewport.devicePixelRatioF()
    if viewport.audio:
        canvas = viewport.grabFramebuffer()
    elif window.current_path:
        canvas = viewport.capture()
    else:
        canvas = QImage(viewport.size() * dpr, QImage.Format.Format_RGBA8888)
        canvas.fill(Qt.GlobalColor.black)
    canvas.setDevicePixelRatio(dpr)
    painter = QPainter(canvas)
    panels = [
        window.empty,
        window.filename,
        window.open_media,
        window.toolbar,
        window.controls,
        window.image_dock,
        window.folder_browser,
        window.loop_notice,
        window.notice,
        window.hover_hint,
    ]
    for panel in panels:
        if not panel.isVisible():
            continue
        effect = panel.graphicsEffect()
        if effect and effect.opacity() == 0:
            continue
        enabled = effect.isEnabled() if effect else False
        if enabled:
            effect.setEnabled(False)
        painter.drawPixmap(viewport.mapFromGlobal(panel.mapToGlobal(QPoint())), panel.grab())
        if enabled:
            effect.setEnabled(True)
    painter.end()
    canvas.save(str(destination))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/style"))
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    # A small code-drawn landscape is synthetic test media, not an app asset.
    image = QImage(1400, 900, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    gradient = QLinearGradient(0, 0, 0, 900)
    for position, colour in ((0, "#142034"), (0.6, "#8999a4"), (1, "#d8a580")):
        gradient.setColorAt(position, QColor(colour))
    painter.fillRect(image.rect(), gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#edcfaa"))
    painter.drawEllipse(1000, 220, 56, 56)
    for colour, points in (
        ("#516174", [(0, 610), (330, 320), (670, 620), (1060, 400), (1400, 640)]),
        ("#2f4056", [(0, 730), (360, 560), (650, 710), (1000, 540), (1400, 740)]),
        ("#182638", [(0, 780), (400, 720), (800, 810), (1150, 680), (1400, 770)]),
    ):
        painter.setBrush(QColor(colour))
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in [*points, (1400, 900), (0, 900)]]))
    painter.end()
    image_path = output / "Quiet evenings.png"
    image.save(str(image_path))
    shutil.copyfile("artifacts/playback/tone.wav", output / "Night drive.wav")
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "unused.ini")
    preferences.volume = 0
    window = Window(preferences)
    report = {"checks": []}

    def check(condition, description):
        assert condition, description
        report["checks"].append(description)
        print(description, flush=True)

    def preview(name):
        window.chrome.reveal()
        wait(150)
        compose(window, output / f"{name}.png")

    try:
        window.show()
        wait(300)
        check(
            not window.statusBar().isVisible() and window.menuWidget() is None,
            "No permanent menu or status bars reserve media space",
        )
        preview("empty")
        window.open_path(image_path)
        wait(200)
        check(
            window.image_dock.isVisible() and not window.controls.isVisible(),
            "Images expose only the small image action dock",
        )
        size = window.viewport.size()
        preview("image")
        check(
            window.centralWidget().childAt(QPoint(400, 30)) is window.viewport
            and window.centralWidget().childAt(window.filename.geometry().center())
            is window.viewport,
            "Empty corner space and filename let pointer input reach the media",
        )
        window.viewport.setFocus()
        QCursor.setPos(window.viewport.mapToGlobal(window.viewport.rect().center()))
        window.chrome.fade()
        wait(300)
        if window.chrome.hidden:
            compose(window, output / "image-quiet.png")
        check(window.chrome.hidden, "Image controls and filename disappear at idle")
        window.open_path("artifacts/playback/av.mp4")
        wait(500)
        window.pause()
        wait(150)
        preview("video")
        check(
            window.controls.width() <= 760 and window.viewport.size() == size,
            "Floating transport stays compact without shrinking or shifting the media",
        )
        check(
            window.controls.play.accessibleName() == "Play"
            and window.controls.play.toolTip() == "Play (Space)",
            "Icon controls expose meaningful accessible names and shortcut hints",
        )
        window.toggle_fullscreen()
        wait(150)
        window.viewport.setFocus()
        QCursor.setPos(window.viewport.mapToGlobal(window.viewport.rect().center()))
        window.chrome.fade()
        wait(250)
        check(
            window.viewport.cursor().shape() == Qt.CursorShape.BlankCursor,
            "Idle fullscreen video also hides the pointer",
        )
        window.toggle_fullscreen()
        wait(150)
        check(
            window.viewport.cursor().shape() != Qt.CursorShape.BlankCursor,
            "Leaving fullscreen restores the pointer and controls",
        )
        window.resize(540, 380)
        wait(200)
        preview("video-small")
        check(
            all(
                window.controls.rect().contains(
                    child.mapTo(window.controls, child.rect().bottomRight())
                )
                for child in window.controls.findChildren(QWidget)
                if child.isVisible()
            ),
            "Transport fits a small 540-pixel window",
        )
        window.resize(960, 640)
        window.open_path(output / "Night drive.wav")
        wait(400)
        preview("music")
        window.notify("Saved AMP_20261018_180000_001.png in Pictures/AMP")
        preview("notice")
        window.media_menu.popup(window.menu_button.mapToGlobal(QPoint(-180, 36)))
        wait(150)
        window.media_menu.grab().save(str(output / "menu.png"))
        window.media_menu.close()
        report["passed"] = True
        report["dpr"] = window.viewport.devicePixelRatioF()
    finally:
        window.close()
        wait(100)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
