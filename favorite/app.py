"""
FavoriteCLI — main application entry point (DI container + run loop).
"""
import os
from pathlib import Path

from rich.console import Console

from .platform import detect_platform
from .config.loader import get_config
from .ui.welcome import render_welcome, clear_screen
from .ui.chat import print_agent_message, print_separator
from .ui.prompt import build_session, get_prompt_tokens
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
                    p = input("  Путь: ").strip()
                except (EOFError, KeyboardInterrupt):
                    return os.getcwd()
                if Path(p).is_dir():
                    return str(Path(p).resolve())
                console.print(f"  [red]Не найдено: {p}[/red]")


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


def _show_home(model_name: str, workdir: str, cfg) -> None:
    """Очищает экран и рисует главный экран."""
    clear_screen()
    render_welcome(model_name=model_name, workdir=workdir)
    if not cfg.has_any_provider():
        console.print(
            "  [dim]Ключи не настроены. Добавь через [/dim]"
            "[bold #ff8c00]/OpenRouter API[/bold #ff8c00]"
            "[dim] или [/dim]"
            "[bold #ff8c00]/Favorite API[/bold #ff8c00]\n"
        )
    console.print("[dim]Введи сообщение или / для команд. Ctrl+C — выход.[/dim]\n")


def run() -> None:
    platform = detect_platform()
    cfg = get_config()

    workdir = _pick_workdir()

    mgr = SessionManager()
    session_id = mgr.create_session(workdir=workdir)

    default_key = cfg.default_openrouter_key()
    model_name = (default_key or {}).get("model", None)
    if not model_name:
        fav = cfg.default_favorite_key()
        model_name = ("FavoriteAPI/" + (fav.get("model") or "default")) if fav else "нет ключей"

    registry = _build_registry()
    ctx = CommandContext(
        workdir=workdir,
        session_id=session_id,
        platform=platform,
        config=cfg,
    )

    session = build_session()

    _show_home(model_name, workdir, cfg)

    while True:
        try:
            raw = session.prompt(get_prompt_tokens, style=STYLE)
        except KeyboardInterrupt:
            console.print("\n[dim]Ctrl+C — нажми ещё раз для выхода.[/dim]")
            try:
                session.prompt([("class:prompt-arrow", "\u276f ")], style=STYLE)
            except (KeyboardInterrupt, EOFError):
                break
            continue
        except EOFError:
            break

        raw = raw.strip()
        if not raw:
            continue

        from .ui.chat import print_user_line
        print_user_line(raw)
        mgr.append_history(session_id, {"type": "user", "content": raw})

        if raw.startswith("/"):
            matched_cmd = None
            matched_args = ""
            for c in registry.all_sorted():
                if raw.lower().startswith(c.name.lower()):
                    matched_cmd = c
                    matched_args = raw[len(c.name):].strip()
                    break
            if matched_cmd:
                try:
                    clear_screen()
                    matched_cmd.execute(matched_args, ctx)
                except Exception as e:
                    console.print(f"[red]Ошибка команды: {e}[/red]")
                # Возвращаемся на главный экран после команды
                _show_home(model_name, workdir, cfg)
            else:
                console.print(f"[dim]Команда не найдена: {raw}[/dim]")
        else:
            if not cfg.has_any_provider():
                console.print(
                    "[yellow]Нет API-ключа.[/yellow] "
                    "Добавь через [bold #ff8c00]/OpenRouter API[/bold #ff8c00]"
                )
            else:
                _handle_chat(raw, ctx, mgr, session_id, cfg)

    clear_screen()
    console.print("\n[dim]До встречи.[/dim]\n")


def _handle_chat(text, ctx, mgr, session_id, cfg) -> None:
    from .ui.spinner import Spinner
    import requests as _req
    spinner = Spinner()
    spinner.start()
    try:
        response = _call_llm(text, cfg)
    except _req.exceptions.ConnectionError:
        spinner.stop()
        console.print(
            "[bold red]FavoriteAPI сервер не запущен.[/bold red] "
            "[dim]Запусти в другом терминале:[/dim] "
            "[bold #ff8c00]python api.py[/bold #ff8c00]"
        )
        return
    except Exception as e:
        spinner.stop()
        console.print(f"[red]Ошибка API: {e}[/red]")
        return
    spinner.stop()
    print_agent_message(response)
    mgr.append_history(session_id, {"type": "agent", "content": response})


def _call_llm(text: str, cfg) -> str:
    import requests as req

    or_key = cfg.default_openrouter_key()
    if or_key:
        headers = {
            "Authorization": f"Bearer {or_key['key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
            "X-Title": "FavoriteCLI",
        }
        body = {
            "model": or_key.get("model", "qwen/qwen3-coder:free"),
            "messages": [{"role": "user", "content": text}],
        }
        r = req.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=body, timeout=60,
        )
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return data["choices"][0]["message"]["content"]

    fav = cfg.default_favorite_key()
    if fav:
        headers = {
            "Authorization": f"Bearer {fav['key']}",
            "Content-Type": "application/json",
        }
        body = {"messages": [{"role": "user", "content": text}]}
        if fav.get("model"):
            body["model"] = fav["model"]
        r = req.post(
            f"{cfg.favorite_api_base_url}/api/v1/chat",
            headers=headers, json=body, timeout=90,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    raise RuntimeError("Нет доступного провайдера.")
