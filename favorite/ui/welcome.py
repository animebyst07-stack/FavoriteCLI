from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from .theme import ORANGE, WHITE, GRAY, LOGO_ART

console = Console()


def render_welcome(model_name: str, workdir: str) -> None:
    logo = Text(LOGO_ART, style=f"bold {ORANGE}")

    content = Text()
    content.append("\n")
    content.append("        Welcome back!\n", style=f"bold {WHITE}")
    content.append("\n")
    content.append(LOGO_ART + "\n", style=f"bold {ORANGE}")
    content.append("\n")
    content.append(f"   {model_name}\n", style=f"{ORANGE}")
    content.append("    API Usage Billing\n", style=f"{GRAY}")
    content.append(f" {workdir}\n", style=f"{GRAY}")
    content.append("\n")

    panel = Panel(
        content,
        title="[bold #ff8c00]Favorite Code[/bold #ff8c00]",
        border_style=f"bold {ORANGE}",
        expand=False,
        width=58,
    )
    console.print(Align.center(panel))


def render_separator() -> None:
    console.print("\u2500" * 56, style=f"{GRAY}")


def print_agent_dot(text: str) -> None:
    console.print(f"[bold {ORANGE}]\u25cf[/bold {ORANGE}] {text}")


def print_step(text: str) -> None:
    for line in text.strip().splitlines():
        console.print(f"  [dim]\u23ce  {line}[/dim]")


def print_error(text: str) -> None:
    console.print(f"[bold red]ERROR:[/bold red] {text}")


def print_info(text: str) -> None:
    console.print(f"[dim]{text}[/dim]")
