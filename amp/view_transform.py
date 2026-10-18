# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""Logical-pixel fit/zoom/pan math shared by both renderers."""

from dataclasses import dataclass
from math import log2


@dataclass
class ViewTransform:
    width: float = 1
    height: float = 1
    media_width: float = 1
    media_height: float = 1
    zoom: float = 1
    pan_x: float = 0
    pan_y: float = 0

    @property
    def fitted_size(self):
        scale = min(self.width / self.media_width, self.height / self.media_height)
        return self.media_width * scale, self.media_height * scale

    @property
    def rect(self):
        w, h = self.fitted_size
        w, h = w * self.zoom, h * self.zoom
        return (self.width - w) / 2 + self.pan_x, (self.height - h) / 2 + self.pan_y, w, h

    def reset(self):
        self.zoom, self.pan_x, self.pan_y = 1, 0, 0

    def clamp(self):
        _, _, w, h = self.rect
        # Keep the viewport covered along enlarged axes and centre smaller axes.
        self.pan_x = max(
            -max(0, (w - self.width) / 2), min(max(0, (w - self.width) / 2), self.pan_x)
        )
        self.pan_y = max(
            -max(0, (h - self.height) / 2), min(max(0, (h - self.height) / 2), self.pan_y)
        )

    def zoom_at(self, x, y, factor):
        previous = self.zoom
        self.zoom = max(1, min(32, previous * factor))
        ratio = self.zoom / previous
        self.pan_x = (x - self.width / 2) * (1 - ratio) + self.pan_x * ratio
        self.pan_y = (y - self.height / 2) * (1 - ratio) + self.pan_y * ratio
        self.clamp()

    def pan(self, dx, dy):
        self.pan_x += dx
        self.pan_y += dy
        self.clamp()

    def resize(self, width, height):
        self.width, self.height = max(1, width), max(1, height)
        self.clamp()

    @property
    def mpv_options(self):
        _, _, w, h = self.rect
        return log2(self.zoom), self.pan_x / w, self.pan_y / h
