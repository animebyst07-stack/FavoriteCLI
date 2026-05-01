"""
FavoriteCLI — main application entry point (DI container + run loop).
"""
import os
import sys
from pathlib import Path

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console

from .platform import detect_platform
from .config.loader import get_config
from .ui.welcome import render_welcome, render_separator
from .ui.chat import (
    print_user_line, print_agent_message, print_separator,
    print_step_block, print_status
)
from .ui.prompt import build_session, BOTTOM_TOOLBAR, get_prompt_tokens
from .ui.theme import STYLE
from .sessions.manager import SessionManager
from .commands.registry import CommandRegistry
from .commands.favorite_api import FavoriteApiCommand
from .commands.openrouter_api import OpenRouterApiCommand
from .commands.models import ModelsCommand
from .commands.sessions_cmd import NewSessionCommand, SessionCommand
from .commands.skills_cmd import SkillsCommand
from .commands.plan_cmd import PlanCommand
from .commands.build_cmd import BuildCommand
from .commands.agents_cmd import AgentsCommand
from .commands.base import CommandContext

console = Console()


def _pick_workdir() -> str:
    console.print(
        "\n[bold #ff8c00]Выбери рабочую директорию:[/bold #ff8c00]\n"
        "  [1] Текущая директория\n"
        "  [2] Указать путь\n"
    )
    while True:
        try:
            choice = input("  Выбери [1/2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return os.getcwd()
        if choice == "1":
            return os.getcwd()
        if choice == "2":
            while True:
                try:
                    p = input("  Путь к директории: ").strip()
                except (EOFError, KeyboardInterrupt):
                    return os.getcwd()
                if Path(p).is_dir():
                    return str(Path(p).resolve())
                console.print(f"  [red]Директория не найдена: {p}[/red]")


def _build_registry() -> CommandRegistry:
    reg = CommandRegistry()
    reg.register(FavoriteApiCommand())
    reg.register(OpenRouterApiCommand())
    reg.register(ModelsCommand())
    reg.register(NewSessionCommand())
    reg.register(SessionCommand())
    reg.register(SkillsCommand())
    reg.register(PlanCommand())
    reg.register(BuildCommand())
    reg.register(AgentsCommand())
    return reg


def run() -> None:
    platform = detect_platform()
    cfg = get_config()
    workdir = _pick_workdir()

    mgr = SessionManager()
    session_id = mgr.create_session(workdir=workdir)

    default_key = cfg.default_openrouter_key()
    model_name = (default_key or {}).get("model", "qwen/qwen3-coder:free")

    render_welcome(model_name=model_name, workdir=workdir)

    registry = _build_registry()
    ctx = CommandContext(
        workdir=workdir,
        session_id=session_id,
        platform=platform,
        config=cfg,
    )

    session = build_session()

    console.print(
        "\n[dim]Введи сообщение или / для команд. Ctrl+C для выхода.[/dim]\n"
    )

    while True:
        try:
            raw = session.prompt(
                get_prompt_tokens,
                style=STYLE,
                bottom_toolbar=BOTTOM_TOOLBAR,
            )
        except KeyboardInterrupt:
            console.print("\n[dim]Прерывание. Ctrl+C ещё раз для выхода.[/dim]")
            try:
                session.prompt(
                    [("class:prompt-arrow", "\u276f ")],
                    style=STYLE,
                )
            except (KeyboardInterrupt, EOFError):
                break
            continue
        except EOFError:
            break

        raw = raw.strip()
        if not raw:
            continue

        print_user_line(raw)
        mgr.append_history(session_id, {"type": "user", "content": raw})

        if raw.startswith("/"):
            cmd_name = raw
            cmd_args = ""
            for c in registry.all_sorted():
                if raw.lower().startswith(c.name.lower()):
                    cmd_name = c.name
                    cmd_args = raw[len(c.name):].strip()
                    break
            cmd = registry.get(cmd_name)
            if cmd:
                try:
                    cmd.execute(cmd_args, ctx)
                except Exception as e:
                    console.print(f"[red]Ошибка команды: {e}[/red]")
            else:
                console.print(f"[dim]Команда не найдена: {raw}[/dim]")
        else:
            _handle_chat(raw, ctx, mgr, session_id, model_name, cfg)

    console.print("\n[dim]До встречи. Сессия сохранена.[/dim]")


def _handle_chat(
    text: str, ctx: CommandContext, mgr: SessionManager,
    session_id: str, model_name: str, cfg
) -> None:
    from .ui.spinner import Spinner
    spinner = Spinner()
    spinner.start()
    try:
        response = _call_llm(text, model_name, cfg)
    except Exception as e:
        spinner.stop()
        console.print(f"[red]Ошибка API: {e}[/red]")
        return
    spinner.stop()
    print_agent_message(response)
    mgr.append_history(session_id, {"type": "agent", "content": response})


def _call_llm(text: str, model: str, cfg) -> str:
    import requests as req
    key_data = cfg.default_openrouter_key()
    if not key_data:
        return "Нет API-ключа. Добавь ключ через /OpenRouter API."
    headers = {
        "Authorization": f"Bearer {key_data['key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
        "X-Title": "FavoriteCLI",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }
    r = req.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=60,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", str(data["error"])))
    return data["choices"][0]["message"]["content"]
