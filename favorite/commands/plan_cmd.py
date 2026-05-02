"""
favorite/commands/plan_cmd.py
/plan mode — read-only planning dialog with POLL → WRITE_PLAN.
Forbidden tags: SHELL_RAW, SHELL_BG, GIT_PUSH, WRITE_FAV, WRITE_CTX.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator

console = Console()

_PLAN_SYSTEM = """\
You are Favorite in /plan mode.
Your job: understand the task, ask clarifying questions, then write a finalized plan.

Allowed tags only:
  ≪STEP≫thinking≪/STEP≫             — reasoning shown to user
  ≪POLL≫question\\n– opt1\\n– opt2≪/POLL≫ — ask user a structured question (answer returned to you)
  ≪CONTINUE≫hint≪/CONTINUE≫         — split your response, continue in next turn
  ≪WRITE_PLAN≫plan text≪/WRITE_PLAN≫ — save final plan (ends /plan session)

Forbidden: SHELL_RAW, SHELL_BG, GIT_PUSH, WRITE_FAV, WRITE_CTX.
Do NOT execute anything. Research-only questions via POLL.

Process:
1. Understand task from user message
2. Ask 2–4 clarifying questions via POLL
3. After answers — produce structured plan and emit ≪WRITE_PLAN≫
4. Plan format: numbered steps, each with goal + acceptance criteria

Respond in Russian.
"""


class PlanCommand(ICommand):
    name = "/plan"
    description = "Режим планирования: диалог → вопросы → plan.txt"
    priority = 9

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config

        console.print(Panel(
            "[bold #ff8c00]/plan[/bold #ff8c00] — режим планирования\n"
            "[dim]Опиши задачу. Агент задаст вопросы и зафиксирует план в plan.txt.\n"
            "Ctrl+C или пустой Enter — выход.[/dim]",
            border_style="#ff8c00",
        ))

        if not cfg.has_any_provider():
            console.print(
                "[yellow]Нет API-ключа.[/yellow] "
                "Настрой через [bold #ff8c00]/OpenRouter API[/bold #ff8c00]"
            )
            return

        # Get initial task from args or prompt user
        if args:
            task = args.strip()
        else:
            try:
                task = input("  Задача: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
        if not task:
            return

        messages: list[dict] = [
            {"role": "system", "content": _PLAN_SYSTEM},
            {"role": "user", "content": task},
        ]

        _run_plan_loop(messages, ctx, cfg)


def _run_plan_loop(messages: list[dict], ctx: CommandContext, cfg) -> None:
    """Inner loop for /plan mode. Runs until WRITE_PLAN or user exits."""
    from ..agent.tags import extract_tags, strip_tags
    from ..agent.executor import _handle_poll, _handle_write_plan, _handle_continue
    from ..agent.llm import call_llm
    from ..ui.spinner import Spinner

    plan_done = False

    while not plan_done:
        spinner = Spinner()
        spinner.start()
        try:
            response = call_llm(messages, cfg)
            spinner.stop()
        except KeyboardInterrupt:
            spinner.stop()
            console.print("\n[dim](прервано)[/dim]")
            return
        except Exception as e:
            spinner.stop()
            console.print(f"[red]Ошибка API: {e}[/red]")
            return

        tags = extract_tags(response)
        clean = strip_tags(response) if tags else response

        if clean.strip():
            print_agent_message(clean)

        messages.append({"role": "assistant", "content": response})

        if not tags:
            # No tags — ask user if they want to add something
            try:
                user_reply = input("  Ты: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not user_reply:
                return
            messages.append({"role": "user", "content": user_reply})
            continue

        # Process only allowed plan-mode tags; collect feedback
        tool_outputs: list[str] = []
        for tag in tags:
            name = tag.name.upper()
            if name == "POLL":
                out = _handle_poll(tag)
                if out:
                    tool_outputs.append(out)
            elif name == "WRITE_PLAN":
                out = _handle_write_plan(tag, ctx)
                if out:
                    tool_outputs.append(out)
                plan_done = True
            elif name == "CONTINUE":
                out = _handle_continue(tag)
                if out:
                    tool_outputs.append(out)
            elif name == "STEP":
                # already rendered via strip_tags / print_agent_message
                pass
            else:
                console.print(
                    f"  [dim][/plan] тег ≪{tag.name}≫ запрещён в режиме планирования[/dim]"
                )

        if plan_done:
            console.print(
                "\n[bold #ff8c00]✓[/bold #ff8c00] [dim]план зафиксирован. "
                "Для исполнения — [bold #ff8c00]/build[/bold #ff8c00][/dim]\n"
            )
            return

        if tool_outputs:
            messages.append({
                "role": "user",
                "content": "\n".join(tool_outputs),
            })
        else:
            # Agent used no actionable tags — ask user for input
            try:
                user_reply = input("  Ты: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not user_reply:
                return
            messages.append({"role": "user", "content": user_reply})
