# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Quiet, local music presentation, painted into the existing media canvas."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QLinearGradient,
    QPalette,
    QPen,
    QTextDocument,
)

from .music import Music


class MusicView:
    def __init__(self):
        self.music = Music()
        self.position = 0
        self.show_lyrics = True
        self.scroll = 0
        self.scroll_max = 0
        self.document = QTextDocument()
        self.document.setDocumentMargin(0)
        self.scale = 1.0

    def set_music(self, music):
        self.music = music
        self.position = self.scroll = 0
        self.document.setPlainText("\n".join(music.lyrics.lines))

    def paint(self, painter, width, height):
        self.scale = max(0.8, min(1.6, width / 960, height / 640))
        painter.setRenderHints(
            painter.RenderHint.Antialiasing | painter.RenderHint.SmoothPixmapTransform
        )
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#171e29"))
        gradient.setColorAt(1, QColor("#090c12"))
        painter.fillRect(QRectF(0, 0, width, height), gradient)
        area = QRectF(36, 78, max(1, width - 72), max(1, height - 190))
        has_lyrics = self.show_lyrics and bool(self.music.lyrics.lines)
        has_art = not self.music.artwork.isNull()
        # Side by side on a wide canvas; a compact header leaves lyrics room on small windows.
        split = has_lyrics and has_art and width >= 760 and area.height() >= 180
        if split:
            left = QRectF(area.left(), area.top(), area.width() * 0.38, area.height())
            lyric_area = QRectF(
                left.right() + 40, area.top(), area.width() - left.width() - 40, area.height()
            )
        else:
            left = QRectF(area)
            lyric_area = QRectF(area)
        if not has_lyrics or split:
            title_height = min(78 * self.scale, left.height() * 0.45)
            gap = 20 * self.scale
            art_size = max(0, min(left.width() - 24, left.height() - title_height - gap))
            if has_art and art_size >= 24:
                top = left.center().y() - (art_size + gap + title_height) / 2
                box = QRectF(left.center().x() - art_size / 2, top, art_size, art_size)
                size = self.music.artwork.size().scaled(
                    box.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio
                )
                target = QRectF(QPointF(), size)
                target.moveCenter(box.center())
                painter.drawImage(target, self.music.artwork)
                title_y = box.bottom() + gap
            else:
                # A restrained record motif gives untagged files an intentional home.
                radius_scale = min(self.scale, max(0.2, (left.height() - title_height - gap) / 98))
                center = QPointF(left.center().x(), left.center().y() - title_height / 2 - gap / 2)
                painter.setPen(QPen(QColor("#303947"), 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for radius in (33, 41, 49):
                    painter.drawEllipse(center, radius * radius_scale, radius * radius_scale)
                painter.setBrush(QColor("#d9b579"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, 5 * radius_scale, 5 * radius_scale)
                title_y = center.y() + 49 * radius_scale + gap
            self._title(painter, QRectF(left.left(), title_y, left.width(), title_height))
        elif has_lyrics:
            title_area = QRectF(area.left(), area.top(), area.width(), 65)
            if has_art:
                title_area.setRight(area.right() - 64)
            self._title(painter, title_area, compact=True)
            lyric_area.setTop(area.top() + 80)
            if has_art:
                box = QRectF(area.right() - 48, area.top(), 48, 48)
                size = self.music.artwork.size().scaled(
                    box.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio
                )
                target = QRectF(QPointF(), size)
                target.moveCenter(box.center())
                painter.drawImage(target, self.music.artwork)
        if has_lyrics:
            self._lyrics(painter, lyric_area)
            if not self.music.lyrics.times and self.scroll_max > 0:
                font = QFont(painter.font())
                font.setPointSize(8)
                painter.setFont(font)
                painter.setPen(QColor("#8691a2"))
                painter.drawText(
                    QRectF(lyric_area.left(), lyric_area.bottom() + 4, lyric_area.width(), 18),
                    Qt.AlignmentFlag.AlignRight,
                    "Scroll lyrics · PgUp / PgDn",
                )

    def _title(self, painter, area, compact=False):
        font = QFont(painter.font())
        font.setPointSizeF(min((14 if compact else 19) * self.scale, max(10, area.height() * 0.32)))
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor("#e0e3e9"))
        title = painter.fontMetrics().elidedText(
            self.music.title, Qt.TextElideMode.ElideMiddle, int(area.width())
        )
        painter.drawText(
            QRectF(area.left(), area.top(), area.width(), area.height() * 0.48),
            Qt.AlignmentFlag.AlignCenter,
            title,
        )
        font.setPointSizeF(max(8, min(10 * self.scale, area.height() * 0.22)))
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#9ca6b6"))
        subtitle = (
            " · ".join(value for value in (self.music.artist, self.music.album) if value)
            or "LOCAL AUDIO"
        )
        subtitle = painter.fontMetrics().elidedText(
            subtitle, Qt.TextElideMode.ElideMiddle, int(area.width())
        )
        painter.drawText(
            QRectF(
                area.left(), area.top() + area.height() * 0.54, area.width(), area.height() * 0.4
            ),
            Qt.AlignmentFlag.AlignCenter,
            subtitle,
        )

    def _lyrics(self, painter, area):
        if area.height() < 30:
            return
        font = QFont(painter.font())
        font.setPointSizeF(14 * self.scale)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.save()
        painter.setClipRect(area)
        lyrics = self.music.lyrics
        if lyrics.times:
            index = lyrics.current(self.position)
            row_height = min(92 * self.scale, area.height() / 3)
            for row, line_index in enumerate((index - 1, index, index + 1)):
                if 0 <= line_index < len(lyrics.lines):
                    painter.setPen(QColor("#e9d1a8" if row == 1 else "#8691a2"))
                    rect = QRectF(
                        area.left(),
                        area.center().y() + (row - 1.5) * row_height,
                        area.width(),
                        row_height,
                    )
                    painter.drawText(
                        rect,
                        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                        lyrics.lines[line_index],
                    )
        else:
            self.document.setDefaultFont(font)
            self.document.setTextWidth(area.width())
            self.scroll_max = max(0, self.document.size().height() - area.height())
            self.scroll = max(0, min(self.scroll, self.scroll_max))
            painter.translate(area.left(), area.top() - self.scroll)
            context = QAbstractTextDocumentLayout.PaintContext()
            context.palette.setColor(QPalette.ColorRole.Text, QColor("#cbd2dd"))
            self.document.documentLayout().draw(painter, context)
        painter.restore()
