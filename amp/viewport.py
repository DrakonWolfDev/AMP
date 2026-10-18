# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Andrew Hodgson trading as Wolf Forge.

"""One media-only GL surface; no toolbar children are included in capture."""

import ctypes

from OpenGL import GL
from OpenGL.error import GLError
from PySide6.QtCore import QRectF, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPainter
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from .image_backend import read_image
from .mpv_backend import MpvBackend
from .view_transform import ViewTransform


class MediaViewport(QOpenGLWidget):
    failed = Signal(str)
    ready = Signal()
    render_requested = Signal()
    fullscreen_requested = Signal()
    video_changed = Signal(str, object)
    media_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.transform = ViewTransform()
        self.image = QImage()
        self.backend = None
        self.renderer = None
        self.video = False
        self.audio = False
        self.audio_name = ""
        self.initialized = False
        self.closed = False
        self.drag_position = None
        self.render_count = 0
        self.load_serial = 0
        self.setMinimumSize(160, 100)
        # Keep the last composited framebuffer available for capture between frames.
        self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.PartialUpdate)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.render_requested.connect(self.update, Qt.ConnectionType.QueuedConnection)

    def initializeGL(self):
        self.initialized = True
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.ready.emit()

    def ensure_video(self):
        if self.renderer:
            return
        if not self.initialized:
            raise RuntimeError("The OpenGL viewport is not ready yet. Try opening again.")
        backend = MpvBackend(self)
        backend.changed.connect(self._property)
        backend.failed.connect(self.failed)
        backend.load_failed.connect(self._load_failed)
        self.makeCurrent()
        try:
            # Keep this ctypes callback alive for the entire render context lifetime.
            self.get_proc = backend.binding.MpvGlGetProcAddressFn(
                lambda _ctx, name: self.context().getProcAddress(name)
            )
            self.renderer = backend.binding.MpvRenderContext(
                backend.player, "opengl", opengl_init_params={"get_proc_address": self.get_proc}
            )
            self.renderer.update_cb = self.render_requested.emit
            self.backend = backend
        except Exception:
            if self.renderer:
                self.renderer.free()
                self.renderer = None
            backend.shutdown()
            raise
        finally:
            self.doneCurrent()

    @Slot(str, object)
    def _property(self, name, value):
        if self.closed:
            return
        if name == "video-out-params" and value and self.video:
            self.transform.media_width = value.get("dw", value.get("w", 1))
            self.transform.media_height = value.get("dh", value.get("h", 1))
            self.apply_transform()
        self.video_changed.emit(name, value)

    @Slot(int, str)
    def _load_failed(self, token, message):
        if not self.closed and token == self.load_serial and self.playable:
            self.media_failed.emit(message)

    def open_image(self, path):
        image = read_image(path)
        self.load_serial += 1
        if self.backend:
            self.backend.command("stop")
        self.video = False
        self.audio = False
        self.image = image
        self.transform.media_width, self.transform.media_height = image.width(), image.height()
        self.reset()

    def open_video(self, path):
        self.ensure_video()
        self.load_serial += 1
        self.image = QImage()
        self.video = True
        self.audio = False
        self.backend.set("vid", "auto")
        self.transform.media_width, self.transform.media_height = 1, 1
        self.reset()
        self.backend.set("pause", False)
        self.backend.load(path, self.load_serial)

    @property
    def playable(self):
        return self.video or self.audio

    def open_audio(self, path):
        self.ensure_video()
        self.load_serial += 1
        self.image = QImage()
        self.video, self.audio = False, True
        self.audio_name = path.name
        self.reset()
        # Ignore attached cover-art video streams; audio has a calm, explicit state.
        self.backend.set("vid", "no")
        self.backend.set("pause", False)
        self.backend.load(path, self.load_serial)
        self.update()

    def paintGL(self):
        if self.closed:
            return
        functions = self.context().functions()
        physical = self.size() * self.devicePixelRatioF()
        width, height = physical.width(), physical.height()
        functions.glViewport(0, 0, width, height)
        functions.glClearColor(0, 0, 0, 1)
        functions.glClear(0x00004000)
        if self.video and self.renderer:
            self.renderer.update()
            self.renderer.render(
                flip_y=True,
                opengl_fbo={"fbo": self.defaultFramebufferObject(), "w": width, "h": height},
            )
            self.render_count += 1
        elif not self.image.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(QRectF(*self.transform.rect), self.image)
            painter.end()
        elif self.audio:
            painter = QPainter(self)
            painter.setPen(Qt.GlobalColor.lightGray)
            font = painter.font()
            font.setPointSize(16)
            painter.setFont(font)
            painter.drawText(
                self.rect().adjusted(24, 24, -24, -24),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                f"Music\n\n{self.audio_name}",
            )
            painter.end()

    def resizeGL(self, width, height):
        self.transform.resize(self.width(), self.height())
        self.apply_transform()

    def apply_transform(self):
        if self.video and self.backend:
            zoom, x, y = self.transform.mpv_options
            self.backend.set("video-zoom", zoom)
            self.backend.set("video-pan-x", x)
            self.backend.set("video-pan-y", y)
        self.update()

    def reset(self):
        self.transform.reset()
        self.apply_transform()

    def wheelEvent(self, event):
        if self.audio:
            event.ignore()
            return
        self.transform.zoom_at(
            event.position().x(), event.position().y(), 1.2 ** (event.angleDelta().y() / 120)
        )
        self.apply_transform()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.reset()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.position()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            delta = event.position() - self.drag_position
            self.drag_position = event.position()
            self.transform.pan(delta.x(), delta.y())
            self.apply_transform()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def mouseDoubleClickEvent(self, event):
        self.fullscreen_requested.emit()

    def capture(self):
        if self.audio:
            raise RuntimeError("Screenshots are available for images and videos, not music.")
        if self.closed or not self.isValid():
            raise RuntimeError("The graphics viewport is unavailable. Open a new AMP window.")
        if self.image.isNull() and not self.video:
            raise RuntimeError("Open an image or video before taking a screenshot.")
        # QSize uses Qt's rounding (half up), unlike Python's round (ties to even).
        physical = self.size() * self.devicePixelRatioF()
        expected = (physical.width(), physical.height())
        # grabFramebuffer() may call paintGL, advancing a playing video. Read the
        # existing Qt FBO instead: no decode/render command and no UI composition.
        width, height = expected
        self.makeCurrent()
        try:
            # Qt/mpv can leave an error flag from capability probing. Drain it
            # before checking errors for this separate readback operation.
            for _attempt in range(16):
                if not self.context().functions().glGetError():
                    break
            else:
                raise RuntimeError("The graphics context has failed. Open a new AMP window.")
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.defaultFramebufferObject())
            GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)
            pixels = ctypes.create_string_buffer(width * height * 4)
            GL.glReadPixels(0, 0, width, height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixels)
            return QImage(
                pixels.raw, width, height, width * 4, QImage.Format.Format_RGBA8888
            ).flipped(Qt.Orientation.Vertical)
        except GLError as error:
            raise RuntimeError(
                "The viewport could not be read from the graphics device."
            ) from error
        finally:
            self.doneCurrent()

    @Slot()
    def cleanup(self):
        if self.closed:
            return
        self.closed = True
        if self.backend:
            # Freeing a live render context intentionally disables its VO; do
            # not turn that shutdown event into a spurious decoder error.
            self.backend.closed = True
        if self.renderer:
            self.makeCurrent()
            self.renderer.update_cb = None
            self.renderer.free()
            self.renderer = None
            self.doneCurrent()
        if self.backend:
            self.backend.shutdown()
            self.backend = None
