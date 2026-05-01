import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from .theme import ORANGE, WHITE, GRAY, LOGO_ART

console = Console()


def clear_screen() -> None:
    os.system("clear")


def render_welcome(model_name: str, workdir: str) -> None:
    # Укорачиваем путь если не влезает
    max_path = 44
    display_path = workdir if len(workdir) <= max_path else "…" + workdir[-(max_path - 1):]

    content = Text(justify="center")
    content.append("\nWelcome back!\n", style=f"bold {WHITE}")
    content.append("\n")
    content.append(LOGO_ART, style=f"bold {ORANGE}")
    content.append("\n\n")
    content.append(model_name, style=f"bold {ORANGE}")
    content.append("\n")
    content.append(display_path, style=GRAY)
    content.append("\n")

    panel = Panel(
        content,
        title="[bold #ff8c00]Favorite Code[/bold #ff8c00]",
        border_style=f"bold {ORANGE}",
        padding=(0, 2),
        width=54,
    )
    console.print(Align.center(panel))
    console.print()


def render_separator() -> None:
    console.print("\u2500" * 50, style=GRAY)


def print_agent_dot(text: str) -> None:
    console.print(f"[bold {ORANGE}]\u25cf[/bold {ORANGE}] {text}")


def print_step(text: str) -> None:
    for line in text.strip().splitlines():
        console.print(f"  [dim]\u23ce  {line}[/dim]")


def print_error(text: str) -> None:
    console.print(f"[bold red]ERROR:[/bold red] {text}")


def print_info(text: str) -> None:
    console.print(text)
