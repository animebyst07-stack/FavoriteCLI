"""
favorite/ui/spinner.py
Animated gradient spinner — dark orange palette.
Used for blocking LLM calls where we need animated feedback.
"""
import threading
import time
import sys


# Dark orange gradient frames — bullet cycles through colours
_FRAMES  = ["◐", "◓", "◑", "◒"]
_COLORS  = [
    "\033[38;2;180;60;0m",    # очень тёмный оранжевый
    "\033[38;2;210;90;0m",    # тёмный оранжевый
    "\033[38;2;255;140;0m",   # оранжевый (#ff8c00)
    "\033[38;2;230;110;0m",   # средний
]
_RESET   = "\033[0m"
_DIM     = "\033[2m"
_BOLD    = "\033[1m"


class Spinner:
    """
    Animated ◐◓◑◒ gradient spinner with optional label.

    Usage:
        s = Spinner("Thinking")
        s.start()
        ...blocking work...
        s.stop()

    Renders: ◐ Thinking   (cycling dark-orange gradient on the bullet)
    All on one line, no newline, clears itself on stop().
    """

    def __init__(self, label: str = ""):
        self.label = label
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        # Clear the spinner line entirely
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _spin(self) -> None:
        label_part = f" {_DIM}{self.label}{_RESET}" if self.label else ""
        i = 0
        while not self._stop_event.is_set():
            color = _COLORS[i % len(_COLORS)]
            frame = _FRAMES[i % len(_FRAMES)]
            line = f"\r  {_BOLD}{color}{frame}{_RESET}{label_part}"
            sys.stdout.write(line)
            sys.stdout.flush()
            i += 1
            self._stop_event.wait(0.12)
