import threading
import time
import sys


class Spinner:
    _STATES = ["\033[90m●\033[0m", "\033[97m●\033[0m"]  # серый, белый

    def __init__(self, message: str = ""):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _spin(self):
        i = 0
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r  {self._STATES[i % 2]}")
            sys.stdout.flush()
            i += 1
            self._stop_event.wait(0.4)
