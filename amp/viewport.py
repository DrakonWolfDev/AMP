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
from .mpv_backend import MpvBackend, companion_subtitles
from .music import Music
from .music_view import MusicView
from .view_transform import ViewTransform


class MediaViewport(QOpenGLWidget):
    failed = Signal(str)
    ready = Signal()
    render_requested = Signal()
    fullscreen_requested = Signal()
    navigation_requested = Signal(int)
    wheel_mode_changed = Signal(bool)
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
        self.music_view = MusicView()
        self.initialized = False
        self.closed = False
        self.drag_position = None
        self.wheel_navigation_enabled = False
        self.wheel_zoom_mode = False
        self.render_count = 0
        self.load_serial = 0
        self.rendered_serial = -1
        self.rendered_size = None
        self.framebuffer_format_cache = None
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
        backend.load_ready.connect(self._load_ready)
        backend.music_ready.connect(self._music_ready)
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
        if name == "video-out-params":
            # Observer deliveries can lag behind a file switch. Re-read on the
            # core worker and correlate the result with this load instead of
            # applying dimensions carried by an earlier queued notification.
            if self.video and self.backend:
                self.backend.refresh_video(self.load_serial)
            return
        self.video_changed.emit(name, value)
        if name == "time-pos" and self.audio:
            previous = self.music_view.music.lyrics.current(self.music_view.position)
            self.music_view.position = value or 0
            if previous != self.music_view.music.lyrics.current(self.music_view.position):
                self.update()

    @Slot(int, object)
    def _music_ready(self, token, music):
        if not self.closed and self.audio and token == self.load_serial:
            position = self.music_view.position
            self.music_view.set_music(music)
            self.music_view.position = position
            self.setAccessibleName(" · ".join(filter(None, (music.title, music.artist))))
            self.update()

    @Slot(int, str)
    def _load_failed(self, token, message):
        if not self.closed and token == self.load_serial and self.playable:
            self.media_failed.emit(message)

    @Slot(int, object)
    def _load_ready(self, token, values):
        # Refresh even unchanged properties (e.g. consecutive files with the
        # same duration) after resetting controls, without reviving stale loads.
        if not self.closed and token == self.load_serial and self.playable:
            for name, value in values.items():
                if name == "video-out-params":
                    if value and self.video:
                        self.transform.media_width = value.get("dw", value.get("w", 1))
                        self.transform.media_height = value.get("dh", value.get("h", 1))
                        self.apply_transform()
                    self.video_changed.emit(name, value)
                else:
                    self._property(name, value)

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

    def open_video(self, path, *, playback_options=None):
        self.ensure_video()
        for name, value in (playback_options or {}).items():
            self.backend.set(name, value)
        self.load_serial += 1
        self.image = QImage()
        self.video = True
        self.audio = False
        self.backend.set("vid", "auto")
        self.transform.media_width, self.transform.media_height = 1, 1
        self.reset()
        self.backend.set("pause", False)
        self.backend.load(
            path,
            self.load_serial,
            subtitles=companion_subtitles(path),
        )

    @property
    def playable(self):
        return self.video or self.audio

    def open_audio(self, path, *, playback_options=None):
        self.ensure_video()
        for name, value in (playback_options or {}).items():
            self.backend.set(name, value)
        self.load_serial += 1
        self.image = QImage()
        self.video, self.audio = False, True
        self.audio_name = path.name
        self.music_view.set_music(Music(title=path.stem))
        self.reset()
        # Decode embedded artwork as a bounded still image, never as video playback.
        self.backend.set("vid", "no")
        self.backend.set("pause", False)
        self.backend.load(path, self.load_serial)
        self.backend.read_music(path, self.load_serial)
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
                opengl_fbo={
                    "fbo": self.defaultFramebufferObject(),
                    "w": width,
                    "h": height,
                    "internal_format": self.framebuffer_internal_format(),
                },
            )
            self.render_count += 1
        elif not self.image.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(QRectF(*self.transform.rect), self.image)
            painter.end()

        elif self.audio:
            painter = QPainter(self)
            self.music_view.paint(painter, self.width(), self.height())
            painter.end()

        self.rendered_serial = self.load_serial
        self.rendered_size = (width, height)

    def framebuffer_internal_format(self):
        """Describe Qt's current colour attachment accurately to libmpv."""
        try:
            kind = GL.glGetFramebufferAttachmentParameteriv(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE,
            )
            name = GL.glGetFramebufferAttachmentParameteriv(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME,
            )
            key = (self.defaultFramebufferObject(), int(kind), int(name))
            if self.framebuffer_format_cache and self.framebuffer_format_cache[0] == key:
                return self.framebuffer_format_cache[1]
            if kind == GL.GL_TEXTURE:
                previous = GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D)
                try:
                    GL.glBindTexture(GL.GL_TEXTURE_2D, name)
                    internal_format = GL.glGetTexLevelParameteriv(
                        GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_INTERNAL_FORMAT
                    )
                finally:
                    GL.glBindTexture(GL.GL_TEXTURE_2D, previous)
            elif kind == GL.GL_RENDERBUFFER:
                previous = GL.glGetIntegerv(GL.GL_RENDERBUFFER_BINDING)
                try:
                    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, name)
                    internal_format = GL.glGetRenderbufferParameteriv(
                        GL.GL_RENDERBUFFER, GL.GL_RENDERBUFFER_INTERNAL_FORMAT
                    )
                finally:
                    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, previous)
            else:
                internal_format = 0
            internal_format = int(internal_format)
            self.framebuffer_format_cache = (key, internal_format)
            return internal_format
        except (GLError, TypeError, ValueError):
            return 0

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
        if self.wheel_navigation_enabled and not self.wheel_zoom_mode:
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta:
                self.navigation_requested.emit(-1 if delta > 0 else 1)
            event.accept()
            return
        if self.audio:
            if self.music_view.show_lyrics and not self.music_view.music.lyrics.times:
                self.music_view.scroll -= event.angleDelta().y() / 2
                self.update()
            event.accept()
            return
        self.transform.zoom_at(
            event.position().x(), event.position().y(), 1.2 ** (event.angleDelta().y() / 120)
        )
        self.apply_transform()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            if self.wheel_navigation_enabled:
                self.wheel_zoom_mode = not self.wheel_zoom_mode
                self.wheel_mode_changed.emit(self.wheel_zoom_mode)
                event.accept()
                return
            if self.audio:
                return
            self.reset()
        elif self.audio:
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.position()

    def set_wheel_navigation(self, enabled):
        self.wheel_navigation_enabled = bool(enabled)
        self.wheel_zoom_mode = False

    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            delta = event.position() - self.drag_position
            self.drag_position = event.position()
            self.transform.pan(delta.x(), delta.y())
            self.apply_transform()

    def keyPressEvent(self, event):
        if self.audio and event.key() in (Qt.Key.Key_PageDown, Qt.Key.Key_PageUp, Qt.Key.Key_Home):
            if event.key() == Qt.Key.Key_Home:
                self.music_view.scroll = 0
            else:
                direction = 1 if event.key() == Qt.Key.Key_PageDown else -1
                self.music_view.scroll += direction * max(40, self.height() - 240)
            self.update()
            event.accept()
        else:
            super().keyPressEvent(event)

    def toggle_lyrics(self, visible):
        self.music_view.show_lyrics = visible
        self.update()

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
        if self.rendered_serial != self.load_serial or self.rendered_size != expected:
            raise RuntimeError("The media view is updating. Try the screenshot again in a moment.")
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
            image = QImage(
                pixels.raw, width, height, width * 4, QImage.Format.Format_RGBA8888
            ).flipped(Qt.Orientation.Vertical)
            if image.isNull():
                raise RuntimeError("There is not enough memory to copy the viewport pixels.")
            return image
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
