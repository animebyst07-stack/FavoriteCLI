import threading
import time
import sys

THINKING_FRAMES = [
    "Shimmying\u2026 (thinking)",
    "Pondering\u2026   (thinking)",
    "Reasoning\u2026  (thinking)",
    "Processing\u2026 (thinking)",
]

class Spinner:
    def __init__(self, message: str = "Thinking"):
        self._message = message
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._frame_idx = 0

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
        while not self._stop_event.is_set():
            frame = THINKING_FRAMES[self._frame_idx % len(THINKING_FRAMES)]
            sys.stdout.write(f"\r\033[90m  \u23ce  {frame}\033[0m")
            sys.stdout.flush()
            self._frame_idx += 1
            time.sleep(0.5)
