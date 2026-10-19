"""Non-blocking PySide6 adapter with bounded shutdown."""

from __future__ import annotations

from threading import Event, Thread

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot


class _Signals(QObject):
    finished = Signal(int, object, bool)


class _Runnable(QRunnable):
    def __init__(self, service, manual, signals, generation, cancelled):
        super().__init__()
        self.service = service
        self.manual = manual
        self.signals = signals
        self.generation = generation
        self.cancelled = cancelled

    def run(self) -> None:
        completed = Event()
        result = []

        def check():
            try:
                result.append(
                    self.service.check(manual=self.manual, cancelled=self.cancelled.is_set)
                )
            finally:
                completed.set()

        Thread(target=check, name="WolfUpdateTransport", daemon=True).start()
        while not completed.wait(0.05):
            if self.cancelled.is_set():
                return
        if not self.cancelled.is_set() and result:
            self.signals.finished.emit(self.generation, result[0], self.manual)


class QtUpdateChecker(QObject):
    result_ready = Signal(object, bool)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.signals = _Signals(self)
        self.signals.finished.connect(self._finish, Qt.ConnectionType.QueuedConnection)
        self.running = False
        self.generation = 0
        self.cancelled = None

    def check(self, *, manual=False):
        if self.running:
            return False
        self.generation += 1
        self.cancelled = Event()
        self.running = True
        self.pool.start(
            _Runnable(self.service, manual, self.signals, self.generation, self.cancelled)
        )
        return True

    @Slot(int, object, bool)
    def _finish(self, generation, result, manual):
        if generation != self.generation or not self.running:
            return
        self.running = False
        self.cancelled = None
        self.result_ready.emit(result, manual)

    def requestInterruption(self):
        if self.cancelled is not None:
            self.cancelled.set()
        self.cancelled = None
        self.generation += 1
        self.running = False

    def wait(self, timeout_ms):
        return self.pool.waitForDone(timeout_ms)
