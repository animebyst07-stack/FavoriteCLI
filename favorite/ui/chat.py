from rich.console import Console
from rich.text import Text
from rich.markup import escape
from .theme import ORANGE, WHITE, GRAY, DIM

console = Console()


def print_user_line(text: str) -> None:
    console.print(f"[bold {WHITE}]\u276f[/bold {WHITE}] {escape(text)}")


def print_agent_message(text: str, agent_name: str = "") -> None:
    prefix = f"[bold {ORANGE}]\u25cf[/bold {ORANGE}]"
    if agent_name:
        prefix += f" [dim]{agent_name}[/dim]"
    console.print(f"{prefix} {escape(text)}")


def print_step_block(text: str) -> None:
    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        leader = "\u23ce " if i == 0 else "  "
        console.print(f"  [dim]{leader}{escape(line)}[/dim]")


def print_thinking(frame: str) -> None:
    console.print(f"  [dim italic]{frame}[/dim italic]")


def print_poll(question: str, options: list[tuple[str, str]]) -> str:
    console.print(f"\n[bold {ORANGE}]\u276f[/bold {ORANGE}] {escape(question)}")
    for idx, (opt_text, hint) in enumerate(options, 1):
        hint_part = f"  [dim]– {escape(hint)}[/dim]" if hint else ""
        console.print(f"  [{WHITE}]{idx}.[/{WHITE}] {escape(opt_text)}{hint_part}")
    console.print()
    while True:
        try:
            raw = input("  Выбери номер: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1][0]
            console.print(f"  [dim]Введи число от 1 до {len(options)}[/dim]")
        except (EOFError, KeyboardInterrupt):
            return options[-1][0]


def print_separator() -> None:
    console.print("\u2500" * 56, style=f"dim {GRAY}")


def print_status(text: str) -> None:
    console.print(f"[dim]{escape(text)}[/dim]", end="\r")
