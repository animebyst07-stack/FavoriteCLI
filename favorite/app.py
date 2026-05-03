"""
FavoriteCLI — main application entry point (DI container + run loop).
"""
import os
import sys
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
from .commands.memory_cmd import MemoryCommand
from .commands.tasks_cmd import TasksCommand
from .commands.usage_cmd import UsageCommand
from .commands.base import CommandContext
from .agent.system_prompt import build_system_prompt

console = Console()


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
    reg.register(MemoryCommand())
    reg.register(TasksCommand())
    reg.register(UsageCommand())
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


def _load_system_prompt(ctx: CommandContext) -> str:
    try:
        return build_system_prompt(ctx.config, ctx.workdir)
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
    from .memory.hot_reload import start_watcher
    from .memory.favorite_md import _DEFAULT as FAV_MD_PATH

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

    def on_fav_md_change():
        console.print("\n● [dim]Favorite.md обновлён[/dim]")

    watcher = start_watcher(str(FAV_MD_PATH), on_fav_md_change)

    session = build_session()
    _show_home(workdir)

    try:
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
                    system_prompt = _load_system_prompt(ctx)
                    messages = _build_messages(raw, history[:-1], system_prompt)
                    _handle_chat(raw, messages, ctx, mgr, session_id, cfg)
    finally:
        watcher.stop()
        watcher.join()

    clear_screen()
    console.print("\n[dim]До встречи.[/dim]\n")


def _handle_chat(
    text: str,
    messages: list[dict],
    ctx,
    mgr,
    session_id: str,
    cfg,
) -> None:
    from .agent.llm import call_llm, stream_llm
    from .ui.spinner import Spinner
    import requests as _req

    or_key = cfg.default_openrouter_key()

    if or_key:
        # --- Streaming path (OpenRouter) ---
        console.print()
        console.print("  [bold #ff8c00]●[/bold #ff8c00] Favorite: ", end="")
        full = ""
        try:
            for chunk in stream_llm(messages, cfg):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                full += chunk
        except KeyboardInterrupt:
            console.print("\n[dim](прервано)[/dim]")
            if full:
                _agent_loop(full, messages, ctx, mgr, session_id, cfg, skip_first_print=True)
            return
        except _req.exceptions.ConnectionError:
            console.print(f"\n[bold red]Не удалось подключиться к OpenRouter.[/bold red]")
            return
        except Exception as e:
            console.print(f"\n[red]Ошибка API: {e}[/red]")
            return
        
        # After stream, re-render and show stats
        if full.strip():
            from rich.markdown import Markdown
            from .agent.response_processor import strip_thinking_blocks
            from .agent.tags import strip_tags
            
            clean = strip_tags(strip_thinking_blocks(full))
            if clean.strip():
                # Move to new line and clear the "Favorite:" prefix line 
                # actually it's easier to just print a separator and then markdown
                console.print("\n")
                print_separator()
                console.print(Markdown(clean))
                
            # Update stats
            tokens = len(full) // 4
            mgr.update_stats(session_id, tokens)
            console.print(f"\n[dim]est. tokens: {tokens}[/dim]")
        else:
            console.print("\n")

        _agent_loop(full, messages, ctx, mgr, session_id, cfg, skip_first_print=True)
        return

    # --- Blocking path (FavoriteAPI via spinner) ---
    spinner = Spinner()
    spinner.start()
    try:
        response = call_llm(messages, cfg)
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
                    response = call_llm(messages, cfg)
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
    if response:
        tokens = len(response) // 4
        mgr.update_stats(session_id, tokens)
        console.print(f"[dim]est. tokens: {tokens}[/dim]")
    _agent_loop(response, messages, ctx, mgr, session_id, cfg)


def _agent_loop(
    first_response: str,
    messages: list[dict],
    ctx,
    mgr,
    session_id: str,
    cfg,
    skip_first_print: bool = False,
) -> None:
    from .agent.tags import extract_tags, strip_tags
    from .agent.executor import execute_tags_with_output
    from .agent.llm import call_llm
    from .ui.spinner import Spinner

    all_responses: list[str] = []
    response = first_response
    step = 0

    while True:
        tags = extract_tags(response)
        clean = strip_tags(response) if tags else response

        # Print only if not already streamed to screen
        if clean.strip() and not (step == 0 and skip_first_print):
            print_agent_message(clean)

        all_responses.append(response)
        step += 1

        if not tags:
            break

        tool_output = execute_tags_with_output(tags, ctx, cfg)

        # Continue loop if: has actionable tags AND produced output
        # CONTINUE tag always produces output (at least "[continue]")
        has_actions = any(
            t.name.upper() in ("SHELL_RAW", "SKILL", "CONTINUE", "POLL")
            for t in tags
        )
        if not has_actions or not tool_output:
            break

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": f"[tool output]\n{tool_output}"})

        spinner = Spinner()
        spinner.start()
        try:
            response = call_llm(messages, cfg)
            spinner.stop()
            if response:
                tokens = len(response) // 4
                mgr.update_stats(session_id, tokens)
                console.print(f"[dim]est. tokens: {tokens}[/dim]")
        except KeyboardInterrupt:
            spinner.stop()
            console.print("\n[dim](прервано пользователем)[/dim]")
            break
        except Exception as e:
            spinner.stop()
            console.print(f"[red]Ошибка API (шаг агента): {e}[/red]")
            break

    final = "\n".join(all_responses)
    from .agent.response_processor import strip_thinking_blocks
    final = strip_thinking_blocks(final)
    mgr.append_history(session_id, {"type": "agent", "content": final})
