"""
FavoriteCLI — main application entry point (DI container + run loop).
"""
import os
from pathlib import Path

from rich.console import Console

from .platform import detect_platform
from .config.loader import get_config, reload_config
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

_MAX_AGENT_STEPS = 8


def _get_model_name(cfg) -> str:
    or_key = cfg.default_openrouter_key()
    name = (or_key or {}).get("model", None)
    if not name:
        fav = cfg.default_favorite_key()
        name = ("FavoriteAPI/" + (fav.get("model") or "gemini")) if fav else "нет ключей"
    return name


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


def _show_home(workdir: str) -> None:
    cfg = reload_config()
    model_name = _get_model_name(cfg)
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


def _load_system_prompt(workdir: str) -> str:
    try:
        from .memory.favorite_md import FavoriteMd
        return FavoriteMd().read() or ""
    except Exception:
        return ""


def _build_messages(text: str, history: list[dict], system_prompt: str) -> list[dict]:
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for entry in history[-20:]:
        role = entry.get("type", "")
        content = entry.get("content", "")
        if role == "user":
            messages.append({"role": "user", "content": content})
        elif role in ("agent", "assistant"):
            messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": text})
    return messages


def run() -> None:
    platform = detect_platform()
    workdir = _pick_workdir()
    mgr = SessionManager()
    session_id = mgr.create_session(workdir=workdir)
    registry = _build_registry()
    ctx = CommandContext(
        workdir=workdir,
        session_id=session_id,
        platform=platform,
        config=get_config(),
    )
    session = build_session()
    _show_home(workdir)

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
                _show_home(workdir)
            else:
                console.print(f"[dim]Команда не найдена: {raw}[/dim]")
        else:
            cfg = reload_config()
            if not cfg.has_any_provider():
                console.print(
                    "[yellow]Нет API-ключа.[/yellow] "
                    "Добавь через [bold #ff8c00]/OpenRouter API[/bold #ff8c00]"
                )
            else:
                history = mgr.load_history(session_id)
                system_prompt = _load_system_prompt(workdir)
                messages = _build_messages(raw, history[:-1], system_prompt)
                _handle_chat(raw, messages, ctx, mgr, session_id, cfg)

    clear_screen()
    console.print("\n[dim]До встречи.[/dim]\n")


def _handle_chat(text: str, messages: list[dict], ctx, mgr, session_id: str, cfg) -> None:
    from .ui.spinner import Spinner
    import requests as _req

    spinner = Spinner()
    spinner.start()
    try:
        response = _call_llm(messages, cfg)
    except _req.exceptions.ConnectionError:
        spinner.stop()
        current_url = cfg.favorite_api_base_url
        if cfg.has_tg_bridge():
            console.print("[dim]Ищу URL через Telegram-мост...[/dim]")
            from .bridge.tg_url import fetch_url, invalidate
            invalidate()
            fresh_url = fetch_url(cfg.tg_bridge_token, cfg.tg_bridge_chat_id)
            if fresh_url and fresh_url != current_url:
                cfg.set_favorite_api_base_url(fresh_url)
                console.print(f"[dim]Новый URL: {fresh_url} — повторяю...[/dim]")
                spin2 = Spinner()
                spin2.start()
                try:
                    response = _call_llm(messages, cfg)
                    spin2.stop()
                    _agent_loop(response, messages, ctx, mgr, session_id, cfg)
                    return
                except Exception:
                    spin2.stop()
        console.print(
            f"[bold red]Не удалось подключиться к FavoriteAPI.[/bold red] "
            f"[dim]Текущий адрес: [/dim][#ff8c00]{current_url}[/#ff8c00]"
        )
        console.print("[dim]Введи новый URL (или Enter чтобы пропустить):[/dim]")
        try:
            new_url = input("  URL: ").strip()
            if new_url:
                if not new_url.startswith("http"):
                    new_url = "http://" + new_url
                cfg.set_favorite_api_base_url(new_url)
                console.print(f"[green]Сохранено:[/green] {new_url}. Повтори сообщение.")
        except (EOFError, KeyboardInterrupt):
            pass
        return
    except Exception as e:
        spinner.stop()
        console.print(f"[red]Ошибка API: {e}[/red]")
        return

    spinner.stop()
    _agent_loop(response, messages, ctx, mgr, session_id, cfg)


def _agent_loop(
    first_response: str,
    messages: list[dict],
    ctx,
    mgr,
    session_id: str,
    cfg,
) -> None:
    from .agent.tags import extract_tags, strip_tags
    from .agent.executor import execute_tags_with_output
    from .ui.spinner import Spinner

    all_responses: list[str] = []
    response = first_response

    for _step in range(_MAX_AGENT_STEPS):
        tags = extract_tags(response)
        clean = strip_tags(response) if tags else response

        if clean.strip():
            print_agent_message(clean)

        all_responses.append(response)

        if not tags:
            break

        tool_output = execute_tags_with_output(tags, ctx, cfg)

        has_actions = any(t.name.upper() in ("SHELL_RAW", "SKILL") for t in tags)
        if not has_actions or not tool_output:
            break

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": f"[tool output]\n{tool_output}"})

        spinner = Spinner()
        spinner.start()
        try:
            response = _call_llm(messages, cfg)
            spinner.stop()
        except Exception as e:
            spinner.stop()
            console.print(f"[red]Ошибка API (шаг агента): {e}[/red]")
            break

    final = "\n".join(all_responses)
    mgr.append_history(session_id, {"type": "agent", "content": final})


def _call_llm(messages: list[dict], cfg) -> str:
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
            "messages": messages,
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
        body = {"messages": messages}
        if fav.get("model"):
            body["model"] = fav["model"]
        r = req.post(
            f"{cfg.favorite_api_base_url}/api/v1/chat",
            headers=headers, json=body, timeout=90,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    raise RuntimeError("Нет доступного провайдера.")
