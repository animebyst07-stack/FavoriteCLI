"""
favorite/commands/build_cmd.py
/build mode — reads plan.txt from current session, runs full agentic loop.
All tags allowed: SHELL_RAW, SHELL_BG, GIT_PUSH, WRITE_FAV, WRITE_CTX, SKILL, CONTINUE, POLL.
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator

console = Console()

_BUILD_SYSTEM = """\
You are Favorite in /build mode — full execution access.
You have a plan. Execute it step by step using available tags.

All tags available:
  ≪STEP≫thinking≪/STEP≫
  ≪SHELL_RAW≫command≪/SHELL_RAW≫    — sync shell, output returned to you
  ≪SHELL_BG≫command≪/SHELL_BG≫      — background process
  ≪SLEEP:s=N≫≪/SLEEP≫
  ≪SKILL:name=websearch≫query≪/SKILL≫
  ≪SKILL:name=fetch≫url≪/SKILL≫
  ≪SKILL:name=fs:op=read:path=f≫≪/SKILL≫
  ≪SKILL:name=fs:op=write:path=f≫content≪/SKILL≫
  ≪WRITE_FAV≫new Favorite.md≪/WRITE_FAV≫
  ≪WRITE_CTX≫compressed notes≪/WRITE_CTX≫
  ≪GIT_PUSH:msg="..."≫≪/GIT_PUSH≫
  ≪CONTINUE≫hint≪/CONTINUE≫         — split response, continue next turn
  ≪POLL≫question≪/POLL≫             — ask user a question

Rules:
- Follow the plan. Verify each step with shell before marking done.
- Use ≪STEP≫ to think before acting.
- Respond in Russian.
- Ctrl+C stops execution at any time.

PLAN:
{plan}
"""


class BuildCommand(ICommand):
    name = "/build"
    description = "Режим исполнения: читает plan.txt и выполняет задачи"
    priority = 10

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config

        if not cfg.has_any_provider():
            console.print(
                "[yellow]Нет API-ключа.[/yellow] "
                "Настрой через [bold #ff8c00]/OpenRouter API[/bold #ff8c00]"
            )
            return

        plan_path = Path(ctx.workdir) / "sessions" / ctx.session_id / "plan.txt"
        plan_text = ""

        if plan_path.exists():
            plan_text = plan_path.read_text(encoding="utf-8").strip()
            console.print(Panel(
                Markdown(plan_text),
                title="[bold #ff8c00]plan.txt[/bold #ff8c00]",
                border_style="#ff8c00",
            ))
            try:
                confirm = input("  Запустить выполнение? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return
            if confirm not in ("y", "д", "да", "yes"):
                console.print("[dim]Отменено.[/dim]")
                return
        else:
            console.print(
                "[dim]plan.txt не найден для этой сессии. "
                "Создай план через [bold #ff8c00]/plan[/bold #ff8c00] "
                "или опиши задачу прямо здесь:[/dim]"
            )
            try:
                plan_text = input("  Задача: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not plan_text:
                return

        system = _BUILD_SYSTEM.format(plan=plan_text)
        initial_user = args.strip() if args else "Начинай выполнение плана."

        messages: list[dict] = [
            {"role": "system", "content": system},
            {"role": "user", "content": initial_user},
        ]

        _run_build_loop(messages, ctx, cfg)


def _run_build_loop(messages: list[dict], ctx: CommandContext, cfg) -> None:
    """Full agentic loop for /build mode. All tags allowed."""
    from ..agent.tags import extract_tags, strip_tags
    from ..agent.executor import execute_tags_with_output
    from ..agent.llm import call_llm
    from ..ui.spinner import Spinner

    while True:
        spinner = Spinner()
        spinner.start()
        try:
            response = call_llm(messages, cfg)
            spinner.stop()
        except KeyboardInterrupt:
            spinner.stop()
            console.print("\n[dim](прервано Ctrl+C)[/dim]")
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
            # No tags — ask if user wants to continue or add instruction
            try:
                user_reply = input("  Продолжить / уточнить (Enter — выход): ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not user_reply:
                console.print("[dim]/build завершён.[/dim]")
                return
            messages.append({"role": "user", "content": user_reply})
            continue

        tool_output = execute_tags_with_output(tags, ctx, cfg)

        has_actions = any(
            t.name.upper() in ("SHELL_RAW", "SKILL", "CONTINUE", "POLL")
            for t in tags
        )
        if not has_actions or not tool_output:
            # Agent finished — ask if user wants to add anything
            try:
                user_reply = input("  Продолжить / уточнить (Enter — выход): ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if not user_reply:
                console.print("[dim]/build завершён.[/dim]")
                return
            messages.append({"role": "user", "content": user_reply})
            continue

        messages.append({"role": "user", "content": f"[tool output]\n{tool_output}"})
