# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Shared AMP dialog furniture, with local Wolf Forge project attribution."""

from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .version import display_version


def label(text, name="", wrap=True):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return widget


class ProjectDialog(QDialog):
    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent)
        self.setObjectName("projectDialog")
        self.setWindowTitle(f"AMP · {title}")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumSize(400, 300)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        accent = QFrame()
        accent.setObjectName("dialogAccent")
        accent.setFixedHeight(3)
        outer.addWidget(accent)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 20)
        body_layout.setSpacing(12)
        brand = QHBoxLayout()
        brand.addWidget(label("AMP", "dialogBrand", False))
        brand.addStretch()
        brand.addWidget(label("LOCAL · PRIVATE · SIMPLE", "dialogEyebrow", False))
        body_layout.addLayout(brand)
        body_layout.addWidget(label(title, "dialogTitle"))
        body_layout.addWidget(label(subtitle, "dialogSubtitle"))
        body_layout.addSpacing(8)
        self.content = QVBoxLayout()
        self.content.setSpacing(14)
        body_layout.addLayout(self.content)
        body_layout.addStretch()
        scroll = QScrollArea()
        scroll.setObjectName("dialogScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        footer = QWidget()
        footer.setObjectName("dialogFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(28, 16, 28, 18)
        footer_layout.setSpacing(12)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        footer_layout.addWidget(self.buttons)
        self.footer_layout = footer_layout
        outer.addWidget(footer)
        screen = self.screen().availableGeometry()
        self.resize(min(560, screen.width() - 40), min(510, screen.height() - 70))


class AboutDialog(ProjectDialog):
    def __init__(self, parent=None):
        super().__init__(
            "Andy's Media Player", "A quiet home for local images, video and music.", parent
        )
        try:
            release = display_version(version("andy-media-player"))
        except PackageNotFoundError:
            release = "0.8.1b"
        self.content.addWidget(label(f"DEVELOPMENT PREVIEW  ·  {release}", "dialogEyebrow"))
        links = QHBoxLayout()
        links.setSpacing(24)
        for title, address in (
            ("Website", "https://wolf-forge.co.uk"),
            ("GitHub", "https://github.com/DrakonWolfDev/AMP"),
        ):
            link = QLabel(f'<a href="{address}" style="color: #d9b579;">{title} ↗</a>')
            link.setAccessibleName(f"{title} — opens in your browser")
            link.setToolTip(address)
            link.setTextInteractionFlags(
                Qt.TextInteractionFlag.LinksAccessibleByMouse
                | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
            )
            link.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            link.linkActivated.connect(lambda address: QDesktopServices.openUrl(QUrl(address)))
            links.addWidget(link)
        links.addStretch()
        self.content.addLayout(links)
        card = QFrame()
        card.setObjectName("dialogCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(label("Free and open source", "dialogSection"))
        layout.addWidget(
            label(
                "Licensed under the GNU Affero General Public License, version 3 only (AGPL-3.0-only). You may use, modify and redistribute AMP under that licence. AMP comes with no warranty."
            )
        )
        self.content.addWidget(card)
        self.content.addWidget(
            label(
                "Full terms: LICENSE\nDependency notices: THIRD_PARTY_NOTICES.md and LICENSES\nThese files accompany the source and Python distribution.",
                "dialogNote",
            )
        )
        self.content.addWidget(label("© 2026 Wolf Forge.", "dialogNote"))
        attribution = label("A Wolf Forge project 🐾", "dialogAttribution", False)
        attribution.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_layout.addWidget(attribution)
        self.resize(self.width(), min(550, self.screen().availableGeometry().height() - 70))


class HelpDialog(ProjectDialog):
    def __init__(self, parent=None):
        super().__init__("Keyboard shortcuts", "The essentials, always within reach.", parent)
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(12)
        for row, (keys, action) in enumerate(
            (
                ("Ctrl+O", "Choose a local file"),
                ("Ctrl+B", "Show or hide the folder browser"),
                ("Ctrl+N", "Open an independent window"),
                ("← / →", "Previous / next file"),
                ("Space", "Play, pause or replay"),
                ("CC button", "Show or hide available subtitles"),
                ("R", "Reset image or video fit"),
                ("Middle click", "Toggle wheel navigation / zoom when enabled in Settings"),
                ("S", "Save the visible image or video"),
                ("Delete", "Confirm and move the open file to Trash"),
                ("F / F11 / double click", "Toggle fullscreen"),
                ("Esc", "Leave fullscreen or close a dialog"),
                ("L", "Show or hide music lyrics"),
                ("PgUp / PgDn / Home", "Scroll plain lyrics"),
                ("Ctrl+,", "Open settings"),
                ("Tab", "Reveal controls and move focus"),
            )
        ):
            grid.addWidget(label(keys, "shortcutKey"), row, 0)
            grid.addWidget(label(action), row, 1)
        grid.setColumnStretch(1, 1)
        self.content.addLayout(grid)
        self.content.addWidget(
            label(
                "Wheel to zoom an image or video; drag to pan. Use the timeline or ±5-second buttons to seek. Plain music lyrics scroll with the wheel.",
                "dialogNote",
            )
        )
        self.resize(self.width(), min(710, self.screen().availableGeometry().height() - 70))
