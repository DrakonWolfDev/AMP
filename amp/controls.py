from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget


def time_label(seconds):
    seconds = max(0, int(seconds or 0))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


class VideoControls(QWidget):
    pause_requested = Signal()
    seek_requested = Signal(float, str)
    volume_requested = Signal(int)
    mute_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0
        self.position = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self.play = QPushButton("Pause")
        self.play.clicked.connect(self.pause_requested)
        layout.addWidget(self.play)
        for label, seconds in (("−5 s", -5), ("+5 s", 5)):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, delta=seconds: self.seek_requested.emit(delta, "relative")
            )
            layout.addWidget(button)
        self.time = QLabel("0:00 / 0:00")
        layout.addWidget(self.time)
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 10000)
        self.timeline.setAccessibleName("Playback position")
        self.timeline.sliderReleased.connect(self.seek)
        self.timeline.actionTriggered.connect(self._timeline_action)
        layout.addWidget(self.timeline, 1)
        self.mute = QPushButton("Mute")
        self.mute.setCheckable(True)
        self.mute.toggled.connect(self.mute_requested)
        layout.addWidget(self.mute)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setMaximumWidth(100)
        self.volume.setAccessibleName("Volume")
        self.volume.valueChanged.connect(self.volume_requested)
        layout.addWidget(self.volume)

    def _timeline_action(self, _action):
        if not self.timeline.isSliderDown():
            self.seek_requested.emit(
                self.timeline.sliderPosition() / 10000 * self.duration, "absolute"
            )

    def seek(self):
        self.seek_requested.emit(self.timeline.value() / 10000 * self.duration, "absolute")

    def update_property(self, name, value):
        if name == "duration":
            self.duration = value or 0
        elif name == "time-pos":
            self.position = value or 0
        elif name == "pause":
            self.play.setText("Play" if value else "Pause")
        self.time.setText(f"{time_label(self.position)} / {time_label(self.duration)}")
        self.timeline.setEnabled(self.duration > 0)
        if not self.timeline.isSliderDown():
            self.timeline.setValue(
                round(self.position / self.duration * 10000) if self.duration else 0
            )
