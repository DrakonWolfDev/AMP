"""Exercise the real folder drawer, file replacement and idle/fullscreen hiding."""

import argparse
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QCursor, QImage, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp.app import Window, create_application
from amp.settings import Preferences
from tools.session_probe import wait
from tools.style_probe import compose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/browser"))
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    media = output / "media"
    media.mkdir(exist_ok=True)
    subfolder = media / "Another folder"
    subfolder.mkdir(exist_ok=True)
    for path, colour in (
        (media / "Image 2.png", "#426478"),
        (media / "Image 10.png", "#d9b579"),
        (subfolder / "Next.png", "#426478"),
    ):
        image = QImage(800, 500, QImage.Format.Format_RGB32)
        image.fill(QColor(colour))
        image.save(str(path))
    (media / "ignored.txt").write_text("not media", encoding="utf-8")
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30",
            "-t",
            "6",
            "-an",
            "-c:v",
            "libx264",
            str(media / "Clip.mp4"),
        ],
        check=True,
        capture_output=True,
    )
    app = create_application()
    app.setQuitOnLastWindowClosed(False)
    preferences = Preferences(output / "isolated.ini")
    preferences.volume = 0
    window = Window(preferences)
    report = {"checks": []}

    def check(condition, message):
        assert condition, message
        report["checks"].append(message)
        print(message, flush=True)

    def click(path):
        files = window.folder_browser.files
        for index in range(files.count()):
            item = files.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == str(path):
                files.scrollToItem(item)
                QTest.mouseClick(
                    files.viewport(),
                    Qt.MouseButton.LeftButton,
                    pos=files.visualItemRect(item).center(),
                )
                wait(100)
                return
        raise AssertionError(f"No listed item: {path}")

    def idle():
        window.viewport.setFocus()
        QCursor.setPos(window.viewport.mapToGlobal(QPoint(30, 120)))
        wait(100)
        window.chrome.fade()
        wait(350)

    try:
        window.show()
        wait(250)
        window.open_path(media / "Image 2.png")
        wait(100)
        check(
            window.open_media.x() > window.centralWidget().width() / 2, "Open media is on the right"
        )
        QTest.mouseClick(window.open_media_button, Qt.MouseButton.LeftButton)
        wait(100)
        browser = window.folder_browser
        check(
            browser.isVisible() and browser.directory == media,
            "Open media expands the current folder",
        )
        names = [browser.files.item(index).text() for index in range(browser.files.count())]
        check(
            names == ["Another folder", "Clip.mp4", "Image 2.png", "Image 10.png"],
            "Drawer lists folders first and supported files in natural order",
        )
        compose(window, output / "browser.png")
        before = window.viewport.capture()
        click(subfolder)
        check(
            browser.directory == subfolder and window.current_path == media / "Image 2.png",
            "Opening a folder preserves playing media",
        )
        click(subfolder / "Next.png")
        check(
            not browser.isVisible() and not window.open_media_button.isChecked(),
            "Choosing a file collapses the folder browser",
        )
        QTest.keyClick(window.viewport, Qt.Key.Key_Right)
        wait(100)
        check(not browser.isVisible(), "Arrow navigation leaves the folder browser collapsed")
        window.open_media_button.click()
        check(
            window.current_path == subfolder / "Next.png"
            and browser.files.currentItem().font().bold(),
            "Single click replaces media in this window and highlights the current file",
        )
        browser.parent_folder()
        click(media / "Image 10.png")
        QTest.keyClick(window.viewport, Qt.Key.Key_Left)
        wait(100)
        check(
            window.current_path == media / "Image 2.png" and not browser.isVisible(),
            "Left arrow changes files without restoring the browser",
        )
        window.navigate(1)
        window.open_media_button.click()
        wait(100)
        check(
            window.current_path == media / "Image 10.png",
            "Up returns to parent and another file opens",
        )
        before = window.viewport.capture()
        idle()
        check(
            window.chrome.hidden
            and all(
                panel.graphicsEffect().opacity() == 0
                for panel in window.chrome.panels
                if panel.isVisible()
            ),
            "Drawer, Open media and all normal controls fade completely",
        )
        check(
            window.viewport.capture() == before, "Fading the browser does not alter captured media"
        )
        point = browser.geometry().center()
        check(
            window.centralWidget().childAt(point) is window.viewport,
            "Invisible browser passes pointer input to media",
        )
        compose(window, output / "quiet.png")
        QApplication.sendEvent(
            window.viewport,
            QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(60, 140),
                QPointF(60, 140),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
        wait(100)
        check(
            not window.chrome.hidden and browser.graphicsEffect().opacity() == 1,
            "Pointer movement restores the expanded folder drawer",
        )
        window.set_fullscreen(True)
        wait(250)
        idle()
        check(
            window.chrome.hidden
            and window.open_media.graphicsEffect().opacity() == 0
            and browser.graphicsEffect().opacity() == 0,
            "Fullscreen image has no browser or Open media overlay at idle",
        )
        window.set_fullscreen(False)
        wait(250)
        window.resize(540, 400)
        window.chrome.reveal()
        wait(100)
        check(
            window.centralWidget().rect().contains(browser.geometry()),
            "Folder drawer fits a small player",
        )
        compose(window, output / "browser-small.png")
        window.resize(500, 260)
        wait(100)
        check(
            window.centralWidget().rect().contains(browser.geometry()),
            "Folder drawer stays inside the minimum player size",
        )
        window.resize(540, 400)
        wait(100)
        click(media / "Clip.mp4")
        window.open_media_button.click()
        wait(500)
        window.video_set("pause", True)
        wait(100)
        before = window.viewport.capture()
        idle()
        check(
            window.viewport.video
            and window.chrome.hidden
            and all(
                panel.graphicsEffect().opacity() == 0
                for panel in window.chrome.panels
                if panel.isVisible()
            ),
            "Video, browser and Open media leave no idle overlays",
        )
        check(
            window.viewport.capture() == before, "Browser fading preserves the paused video frame"
        )
        window.chrome.reveal()
        window.open_media_button.click()
        check(not browser.isVisible(), "Open media collapses the folder drawer")
        report["passed"] = True
        report["dpr"] = window.viewport.devicePixelRatioF()
    finally:
        window.close()
        wait(100)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
