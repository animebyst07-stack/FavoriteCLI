"""
favorite/ui/chat.py
Claude Code-style terminal UI.
Thinking → compact animated status.
Shell → compact command output.
Response → proper markdown rendering.
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.text import Text
import itertools
import threading
import time
from .theme import ORANGE, WHITE, GRAY, DIM

console = Console()


# ─── Agent response ────────────────────────────────────────────────────────────

def print_agent_message(text: str, agent_name: str = "") -> None:
    """
    Render AI response. Orange bullet inline with first line, rest as Markdown.
    For system messages (agent_name="system") renders as plain styled text.
    """
    text = text.strip()
    if not text:
        return
    console.print()

    # Split into first line and remainder
    lines = text.split("\n", 1)
    first_line = lines[0].strip()
    rest = lines[1].strip() if len(lines) > 1 else ""

    # Build "● [agent_name] first_line" all on one line
    header = Text()
    header.append("● ", style=f"bold {ORANGE}")
    if agent_name:
        header.append(agent_name + "  ", style=f"dim {GRAY}")
    header.append(first_line)
    console.print(header)

    # Render remainder as Markdown if any
    if rest:
        console.print(Markdown(rest))

    console.print()


def print_status_line(label: str, detail: str = "", color: str = ORANGE) -> None:
    detail = detail.strip()
    if detail:
        console.print(f"[bold {color}]●[/bold {color}] [dim {GRAY}]{escape(label)}[/dim {GRAY}] [dim #666666]{escape(detail)}[/dim #666666]")
    else:
        console.print(f"[bold {color}]●[/bold {color}] [dim {GRAY}]{escape(label)}[/dim {GRAY}]")


# ─── Thinking / STEP block ────────────────────────────────────────────────────

def print_step(text: str) -> None:
    """STEP/THINK blocks are internal reasoning — rendered as compact status."""
    print_status_line("Thinking", text, color="#666666")


def print_step_block(text: str) -> None:
    """Backward-compat alias for print_step."""
    print_step(text)


def render_status_line(label: str, text: str = "", color: str = ORANGE) -> str:
    body = text.strip()
    if body:
        return f"[bold {color}]●[/bold {color}] [dim {GRAY}]{escape(label)}[/dim {GRAY}] [dim #666666]{escape(body)}[/dim #666666]"
    return f"[bold {color}]●[/bold {color}] [dim {GRAY}]{escape(label)}[/dim {GRAY}]"


def print_status(label: str, text: str = "", color: str = ORANGE) -> None:
    print_status_line(label, text, color=color)


class StatusSpinner:
    """
    Animated gradient spinner via Rich markup.
    Cycles dark-orange bullet frames with label.
    Wraps the core Spinner to reuse logic.
    """
    def __init__(self, label: str, detail: str = ""):
        self.label = label
        self.detail = detail
        self._stop = threading.Event()
        self._thread = None

    def start(self) -> None:
        import sys as _sys
        _FRAMES  = ["◐", "◓", "◑", "◒"]
        _ANSI_COLORS = [
            "\033[38;2;180;60;0m",
            "\033[38;2;210;90;0m",
            "\033[38;2;255;140;0m",
            "\033[38;2;230;110;0m",
        ]
        _RST  = "\033[0m"
        _DIM  = "\033[2m"
        _BOLD = "\033[1m"
        label = self.label
        detail = self.detail
        stop_ev = self._stop

        def _run():
            i = 0
            while not stop_ev.is_set():
                color = _ANSI_COLORS[i % len(_ANSI_COLORS)]
                frame = _FRAMES[i % len(_ANSI_COLORS)]
                label_part = f" {_DIM}{label}{_RST}" if label else ""
                detail_part = f" {_DIM}{detail}{_RST}" if detail else ""
                _sys.stdout.write(f"\r  {_BOLD}{color}{frame}{_RST}{label_part}{detail_part}")
                _sys.stdout.flush()
                i += 1
                stop_ev.wait(0.12)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        import sys as _sys
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        _sys.stdout.write("\r\033[K")
        _sys.stdout.flush()


# ─── Shell / tool execution ───────────────────────────────────────────────────

def print_shell_cmd(cmd: str) -> None:
    """
    Show shell command about to run.
      > command (up to 90 chars)
    """
    short = cmd.strip()
    if len(short) > 90:
        short = short[:87] + "..."
    console.print(f"  [bold {ORANGE}]>[/bold {ORANGE}] [dim]{escape(short)}[/dim]")


def print_shell_output(out: str, err: str, max_lines: int = 6) -> None:
    """
    Show shell output compactly — max max_lines lines, excess summarized.
    stdout = dim gray, stderr = dim red.
    """
    out_lines = out.strip().splitlines() if out.strip() else []
    err_lines = err.strip().splitlines() if err.strip() else []
    all_lines: list[tuple[str, str]] = (
        [(l, "out") for l in out_lines] +
        [(l, "err") for l in err_lines]
    )
    if not all_lines:
        return
    shown = all_lines[:max_lines]
    for line, kind in shown:
        text = escape(line[:130])
        if kind == "err":
            console.print(f"  [dim #995555]{text}[/dim #995555]")
        else:
            console.print(f"  [dim #666666]{text}[/dim #666666]")
    extra = len(all_lines) - max_lines
    if extra > 0:
        console.print(f"  [dim #444444]... +{extra} lines[/dim #444444]")


def print_skill_header(skill_name: str, query: str = "") -> None:
    """Show skill invocation — compact single line."""
    q_part = f" [dim #666666]{escape(query[:60])}[/dim #666666]" if query else ""
    console.print(
        f"  [bold {ORANGE}]~[/bold {ORANGE}] "
        f"[dim {GRAY}]{escape(skill_name)}[/dim {GRAY}]{q_part}"
    )


# ─── System / separator ────────────────────────────────────────────────────────

def print_separator() -> None:
    console.print("─" * 54, style=f"dim {GRAY}")


def print_thinking(frame: str) -> None:
    """Legacy — kept for spinner compat."""
    console.print(f"  [dim italic {GRAY}]{escape(frame)}[/dim italic {GRAY}]")


def print_user_line(text: str) -> None:
    console.print(f"[bold {WHITE}]>[/bold {WHITE}] {escape(text)}")


def print_poll(question: str, options: list[tuple[str, str]]) -> str:
    """Structured poll UI (legacy signature kept for any callers)."""
    console.print(f"\n[bold {ORANGE}]?[/bold {ORANGE}] {escape(question)}")
    for idx, (opt_text, hint) in enumerate(options, 1):
        hint_part = f"  [dim]– {escape(hint)}[/dim]" if hint else ""
        console.print(f"  [{WHITE}]{idx}.[/{WHITE}] {escape(opt_text)}{hint_part}")
    console.print()
    while True:
        try:
            raw = input("  → ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1][0]
            console.print(f"  [dim]Введи число 1–{len(options)}[/dim]")
        except (EOFError, KeyboardInterrupt):
            return options[-1][0]
