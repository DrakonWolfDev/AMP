from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtCore import QSize

from amp import viewport as viewport_module
from amp.viewport import MediaViewport


def test_mpv_render_is_bounded_before_subtitle_composition(monkeypatch):
    events = []

    class Painter:
        def __init__(self, target):
            assert target is viewport

        def beginNativePainting(self):
            events.append("begin-native")

        def endNativePainting(self):
            events.append("end-native")

        def end(self):
            events.append("end-painter")

    class Renderer:
        def update(self):
            events.append("mpv-update")

        def render(self, **options):
            events.append("mpv-render")
            assert options["opengl_fbo"] == {
                "fbo": 7,
                "w": 320,
                "h": 180,
                "internal_format": 8,
            }

    functions = SimpleNamespace(
        glViewport=Mock(),
        glClearColor=Mock(),
        glClear=Mock(),
    )
    viewport = SimpleNamespace(
        closed=False,
        context=lambda: SimpleNamespace(functions=lambda: functions),
        size=lambda: QSize(320, 180),
        devicePixelRatioF=lambda: 1.0,
        video=True,
        renderer=Renderer(),
        defaultFramebufferObject=lambda: 7,
        framebuffer_internal_format=lambda: 8,
        render_count=0,
        subtitle_visible=True,
        subtitle_text="Caption",
        _paint_subtitle=lambda painter: events.append("subtitle"),
        load_serial=4,
        rendered_serial=-1,
        rendered_size=None,
    )
    monkeypatch.setattr(viewport_module, "QPainter", Painter)

    MediaViewport.paintGL(viewport)

    assert events == [
        "begin-native",
        "mpv-update",
        "mpv-render",
        "end-native",
        "subtitle",
        "end-painter",
    ]
    assert viewport.render_count == 1
    assert viewport.rendered_serial == 4
    assert viewport.rendered_size == (320, 180)
