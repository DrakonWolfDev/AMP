import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from amp.controls import QuietSlider, VideoControls


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication(["amp-tests", "-platform", "offscreen"])
    yield app


@pytest.fixture
def controls(application):
    widget = VideoControls()
    widget.resize(600, 80)
    widget.update_property("duration", 120)
    widget.update_property("time-pos", 10)
    widget.show()
    application.processEvents()
    yield widget
    widget.close()


def point(slider, fraction, y=None):
    return QPoint(
        round(6 + fraction * (slider.width() - 13)), slider.height() // 2 if y is None else y
    )


def test_click_near_end_seeks_there_instead_of_one_small_page(controls):
    seeks = []
    controls.seek_requested.connect(lambda *args: seeks.append(args))
    QTest.mouseClick(
        controls.timeline, Qt.MouseButton.LeftButton, pos=point(controls.timeline, 0.95)
    )
    assert len(seeks) == 1
    assert seeks[0][0] == pytest.approx(114, abs=0.3)
    assert seeks[0][1] == "absolute"


def test_drag_uses_full_height_and_survives_clock_updates_and_outside_release(controls):
    slider = controls.timeline
    seeks = []
    controls.seek_requested.connect(lambda *args: seeks.append(args))
    QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.25, y=1))
    QTest.mouseMove(slider, point(slider, 0.9))
    expected = slider.value()
    controls.update_property("time-pos", 11)
    assert slider.isSliderDown() and slider.value() == expected
    assert not seeks
    QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(slider.width() + 30, 1))
    assert not slider.isSliderDown()
    assert seeks == [(120.0, "absolute")]


def test_keyboard_home_end_keep_absolute_seeking(controls):
    seeks = []
    controls.seek_requested.connect(lambda *args: seeks.append(args))
    QTest.keyClick(controls.timeline, Qt.Key.Key_End)
    QTest.keyClick(controls.timeline, Qt.Key.Key_Home)
    assert seeks == [(120.0, "absolute"), (0.0, "absolute")]


def test_volume_pointer_uses_the_same_absolute_rail(application):
    slider = QuietSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.resize(200, 24)
    slider.show()
    QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.5))
    assert slider.value() == 50
    QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=point(slider, 0.5))
    QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(-20, 1))
    assert slider.value() == 0
    slider.close()


def test_mute_hides_volume_without_changing_decoder_level(controls):
    volumes = []
    controls.volume_requested.connect(volumes.append)
    controls.volume.setValue(37)
    controls.mute.setChecked(True)
    assert controls.volume.value() == 0
    assert controls.volume_level == 37
    assert volumes == [37]
    controls.update_property("volume", 19)
    assert controls.volume.value() == 0
    controls.mute.setChecked(False)
    assert controls.volume.value() == 19
    assert volumes == [37]


def test_volume_drag_unmutes_and_observers_do_not_emit_requests(controls):
    requests = []
    controls.mute_requested.connect(requests.append)
    controls.update_property("mute", True)
    assert not requests
    controls.volume.setValue(42)
    assert requests == [False]
    assert controls.volume_level == controls.volume.value() == 42


def test_speed_slider_reset_and_observer_sync(controls):
    requests = []
    controls.speed_requested.connect(requests.append)
    controls.speed.setValue(30)
    assert requests == [1.5]
    assert controls.speed_label.text() == "1.5×"
    controls.speed_label.click()
    assert requests == [1.5, 1.0]
    controls.update_property("speed", 0.5)
    assert controls.speed.value() == 10
    assert controls.speed_label.text() == "0.5×"
    assert requests == [1.5, 1.0]


def test_cc_button_is_hidden_and_off_until_a_subtitle_track_exists(controls):
    requests = []
    controls.subtitles_requested.connect(requests.append)
    assert controls.subtitles.isHidden()
    assert not controls.subtitles.isChecked()

    controls.update_property("track-list", [{"type": "video"}, {"type": "sub"}])
    assert controls.subtitles.isVisible()
    controls.subtitles.click()
    assert requests == [True]

    controls.update_property("sub-visibility", False)
    assert not controls.subtitles.isChecked()
    assert requests == [True]
    controls.update_property("track-list", [{"type": "video"}])
    assert controls.subtitles.isHidden()
