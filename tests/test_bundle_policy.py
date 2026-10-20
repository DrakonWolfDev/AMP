from pathlib import Path

from tools.bundle_policy import forbidden_runtime_file


def test_rejects_unused_pyopengl_native_helpers_on_both_path_styles():
    assert forbidden_runtime_file(Path("_internal/OpenGL/DLLS/freeglut64.vc14.dll"))
    assert forbidden_runtime_file("_internal\\OpenGL\\DLLS\\gle32.vc9.dll")


def test_rejects_unused_media_and_development_payloads():
    assert forbidden_runtime_file("_internal/PySide6/Qt6Multimedia.dll")
    assert forbidden_runtime_file("_internal/PySide6/plugins/ffmpegmediaplugin.dll")
    assert forbidden_runtime_file("runtime/libbluray-j2se.jar")


def test_allows_required_amp_opengl_and_mpv_files():
    assert not forbidden_runtime_file("_internal/PySide6/Qt6OpenGL.dll")
    assert not forbidden_runtime_file("_internal/amp_runtime/libmpv-2.dll")
