from pathlib import Path

from tools.bundle_policy import forbidden_runtime_file


def test_rejects_unused_pyopengl_native_helpers_on_both_path_styles():
    assert forbidden_runtime_file(Path("_internal/OpenGL/DLLS/freeglut64.vc14.dll"))
    assert forbidden_runtime_file("_internal\\OpenGL\\DLLS\\gle32.vc9.dll")


def test_rejects_unused_media_and_development_payloads():
    assert forbidden_runtime_file("_internal/PySide6/plugins/ffmpegmediaplugin.dll")
    assert forbidden_runtime_file("_internal/amp_runtime/libmpv-2.dll")
    assert not forbidden_runtime_file("_internal/LICENSES/libmpv-LICENSE.LGPL")
    assert forbidden_runtime_file("_internal/PySide6/avutil-61.dll")
    assert forbidden_runtime_file("_internal/PySide6/swresample-6.dll")
    assert forbidden_runtime_file("_internal/PySide6/swscale-10.dll")
    assert forbidden_runtime_file("runtime/libbluray-j2se.jar")


def test_rejects_unused_qt_virtual_keyboard_and_its_qml_quick_dependencies():
    for filename in (
        "Qt6Qml.dll",
        "Qt6QmlMeta.dll",
        "Qt6Quick.dll",
        "Qt6VirtualKeyboard.dll",
        "qtvirtualkeyboardplugin.dll",
        "libQt6Qml.so.6",
        "libQt6Quick.so.6",
        "libQt6VirtualKeyboard.so.6",
        "libqtvirtualkeyboardplugin.so",
    ):
        assert forbidden_runtime_file(filename)


def test_allows_required_amp_opengl_and_media_foundation_files():
    assert not forbidden_runtime_file("_internal/PySide6/Qt6OpenGL.dll")
    assert not forbidden_runtime_file("_internal/PySide6/Qt6Multimedia.dll")
    assert not forbidden_runtime_file("_internal/PySide6/plugins/multimedia/windowsmediaplugin.dll")


def test_rejects_versioned_linux_decoder_libraries():
    for name in ("libmpv.so", "libmpv.so.2", "libmpv.so.2.5.0", "libavcodec.so.62"):
        assert forbidden_runtime_file(f"_internal/{name}")
    assert not forbidden_runtime_file("_internal/LICENSES/libmpv-Copyright.txt")
